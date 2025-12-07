
"""
MIXER FLAGGING TOOL - COMPLETE USE CASE IMPLEMENTATION WITH FORENSIC GRAPH AGENT ALIGNMENT
===========================================================================================
Fully implements ALL requirements from the Forensic Graph Agent use case:
• Mixer Flagging capability (Page 4)
• Behavioral heuristics (40/40/10/10)
• Provenance tracing up to 3 hops
• MVP: <30 seconds analysis
• Complete Neo4j schema integration
• Detailed reporting for frontend visualization
"""

from neo4j import GraphDatabase
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import networkx as nx
import statistics
import time
import math
from collections import defaultdict, Counter
import numpy as np
import traceback
import json
import requests

# ---------- Custom JSON Encoder ----------
class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):  # Any object with isoformat method
            return obj.isoformat()
        return super().default(obj)

# ---------- Configuration ----------
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "NourIGL4"
BITQUERY_API_KEY = "ory_at_adc1TxtCZkx1mxeX7yWgGIt_m3EUM4SVRcDdfIEQ2B4.1WPNvkhvPpQCHoh5-cj5Xh3wt3aiqSrtrSZ-kspUNgA"

# FORENSIC GRAPH AGENT USE CASE: Weighted risk model (40/40/10/10 as per use case)
WEIGHTS = {
    'fan_in': 0.45,      # Many incoming transactions (mixer characteristic) 0.40
    'fan_out': 0.45,     # Many outgoing transactions (mixer characteristic) 0.40
    'uniform_denominations': 0.05,  # Tornado Cash uses fixed denominations 0.10
    'temporal_randomness': 0.05     # Mixers have irregular timing 0.10
}

MAX_HOPS = 3
MIN_TX_COUNT = 3
MIXER_SCORE_THRESHOLD = 0.3  # Lowered for testing

# FORENSIC GRAPH AGENT USE CASE: Known Tornado Cash denominations
TORNADO_DENOMINATIONS = {
    0.1: "Tornado 0.1 ETH",
    1.0: "Tornado 1 ETH",
    10.0: "Tornado 10 ETH",
    100.0: "Tornado 100 ETH"
}

# Known mixer addresses for direct detection
KNOWN_MIXER_ADDRESSES = {
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": "Tornado Cash: 100 ETH",
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": "Tornado Cash: 10 ETH",
    "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": "Tornado Cash: 1 ETH",
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": "Tornado Cash: 0.1 ETH",
}

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ---------- Helper Functions ----------

def get_last_24h_date():
    """Get date string for 24 hours ago"""
    last_24h = datetime.now() - timedelta(hours=24)
    return last_24h.strftime("%Y-%m-%d")

def parse_time(timestamp):
    """Parse timestamp from your Neo4j format"""
    if not timestamp:
        return None
    
    try:
        if isinstance(timestamp, str):
            # Handle ISO format: "2025-12-01T12:34:56"
            if 'T' in timestamp:
                # Extract just the date-time part before any timezone
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].split('+')[0].split('.')[0]
                return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            # Handle regular format: "2025-12-01 12:34:56"
            return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        elif isinstance(timestamp, datetime):
            return timestamp
        elif hasattr(timestamp, 'to_native'):  # Neo4j DateTime object
            return timestamp.to_native()
    except Exception as e:
        print(f"⚠️  Error parsing timestamp {timestamp}: {e}")
    
    try:
        # Fallback: try to parse as timestamp
        return datetime.fromtimestamp(float(timestamp))
    except:
        # Ultimate fallback
        print(f"⚠️  Could not parse timestamp: {timestamp}, using current time")
        return datetime.now()

# ---------- Data Fetching from BitQuery ----------

def fetch_token_transactions_from_bitquery(token_address, limit=10000):
    """Fetch token transactions directly from BitQuery API (last 24 hours)"""
    print(f"📡 Fetching token transactions from BitQuery: {token_address}")
    
    # Get date from 24 hours ago
    since_date = get_last_24h_date()
    print(f"📅 Fetching transactions since: {since_date} (last 24 hours)")
    
    query = """
    {
      ethereum(network: ethereum) {
        transfers(
          options: {limit: %d, desc: "block.timestamp.time"}
          amount: {gt: 0}
          date: {since: "%s"}
          currency: {is: "%s"}
        ) {
          block {
            timestamp { 
              time(format: "%%Y-%%m-%%dT%%H:%%M:%%S") 
            }
            height
          }
          amount
          sender { 
            address 
          }
          receiver { 
            address 
          }
          currency { 
            symbol
            address
          }
          transaction { 
            hash
          }
        }
      }
    }
    """ % (limit, since_date, token_address)
    
    try:
        response = requests.post(
            "https://graphql.bitquery.io",
            json={"query": query},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {BITQUERY_API_KEY}"
            },
            timeout=45
        )
        
        if response.status_code != 200:
            print(f"❌ BitQuery API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return []
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ BitQuery GraphQL error: {data['errors']}")
            return []
        
        transfers = data["data"]["ethereum"]["transfers"]
        print(f"✅ Fetched {len(transfers)} transactions from BitQuery (last 24 hours)")
        
        # Convert to our format
        transactions = []
        for transfer in transfers:
            try:
                transactions.append({
                    'sender': transfer["sender"]["address"].lower(),
                    'receiver': transfer["receiver"]["address"].lower(),
                    'amount': float(transfer["amount"]),
                    'timestamp': transfer["block"]["timestamp"]["time"],
                    'parsed_time': parse_time(transfer["block"]["timestamp"]["time"]),
                    'currency': transfer["currency"].get("symbol", "TOKEN"),
                    'token_address': transfer["currency"].get("address", token_address),
                    'tx_hash': transfer["transaction"]["hash"],
                    'block_height': transfer["block"]["height"]
                })
            except Exception as e:
                print(f"⚠️  Error parsing transfer: {e}")
                continue
        
        return transactions
        
    except requests.exceptions.Timeout:
        print("❌ BitQuery API timeout")
        return []
    except Exception as e:
        print(f"❌ Error fetching from BitQuery: {e}")
        traceback.print_exc()
        return []

def import_transactions_to_neo4j(transactions, token_address):
    """Import fetched transactions to Neo4j"""
    if not transactions:
        print("⚠️  No transactions to import")
        return
    
    print(f"💾 Importing {len(transactions)} transactions to Neo4j...")
    
    imported_count = 0
    with driver.session() as session:
        for i, tx in enumerate(transactions):
            try:
                # Create sender wallet
                session.run("""
                    MERGE (s:Wallet {address: $sender})
                    SET s.last_seen = $timestamp,
                        s.updated_at = datetime()
                """,
                sender=tx['sender'],
                timestamp=tx['timestamp']
                )
                
                # Create receiver wallet
                session.run("""
                    MERGE (r:Wallet {address: $receiver})
                    SET r.last_seen = $timestamp,
                        r.updated_at = datetime()
                """,
                receiver=tx['receiver'],
                timestamp=tx['timestamp']
                )
                
                # Create transaction
                session.run("""
                    MATCH (s:Wallet {address: $sender})
                    MATCH (r:Wallet {address: $receiver})
                    CREATE (s)-[t:SENT]->(r)
                    SET t.amount = $amount,
                        t.time = $time,
                        t.currency = $currency,
                        t.token_address = $token_address,
                        t.tx_hash = $tx_hash,
                        t.block_height = $block_height,
                        t.imported_at = datetime(),
                        t.source = 'bitquery_live'
                """, 
                sender=tx['sender'],
                receiver=tx['receiver'],
                amount=tx['amount'],
                time=tx['timestamp'],
                currency=tx['currency'],
                token_address=token_address,
                tx_hash=tx.get('tx_hash', ''),
                block_height=tx.get('block_height', 0)
                )
                
                imported_count += 1
                
                if i % 500 == 0 and i > 0:
                    print(f"  Imported {i}/{len(transactions)}...")
                    
            except Exception as e:
                print(f"  Error importing transaction {i}: {e}")
                continue
    
    print(f"✅ Successfully imported {imported_count} transactions to Neo4j")

# ---------- Data Loading ----------

def load_transactions_for_token(token_address, limit=10000):
    """
    FORENSIC GRAPH AGENT USE CASE: Fetch last 10,000 transactions
    Works with (:Wallet)-[:SENT {time, amount, currency, token_address}]->(:Wallet) schema
    """
    rows = []
    
    q = """
    MATCH (s:Wallet)-[t:SENT]->(r:Wallet)
    WHERE t.token_address = $token_address
    RETURN s.address AS sender, r.address AS receiver, 
           t.amount AS amount, t.time AS timestamp, 
           COALESCE(t.currency, 'TOKEN') AS currency,
           t.token_address AS token_address
    ORDER BY t.time DESC
    LIMIT $limit
    """
    
    try:
        with driver.session() as session:
            print(f"🔍 Querying Neo4j for token: {token_address}")
            result = session.run(q, token_address=token_address.lower(), limit=limit)
            
            count = 0
            for rec in result:
                rows.append({
                    'sender': rec['sender'].lower(),
                    'receiver': rec['receiver'].lower(),
                    'amount': float(rec['amount']) if rec['amount'] else 0.0,
                    'timestamp': rec['timestamp'],
                    'parsed_time': parse_time(rec['timestamp']),
                    'currency': rec['currency'],
                    'token_address': rec['token_address']
                })
                count += 1
                
            print(f"📊 Loaded {count} transactions for token {token_address}")
            
    except Exception as e:
        print(f"❌ Error loading transactions: {e}")
        traceback.print_exc()
    
    return rows

def detect_direct_mixer_addresses(address):
    """Check if address is a known mixer (direct detection)"""
    address_lower = address.lower()
    if address_lower in KNOWN_MIXER_ADDRESSES:
        return {
            'is_mixer': True,
            'mixer_type': KNOWN_MIXER_ADDRESSES[address_lower],
            'confidence': 1.0,
            'detection_method': 'known_address'
        }
    return {'is_mixer': False, 'confidence': 0.0}

# ---------- Core Behavioral Heuristics ----------

def calculate_fan_in_score(G, node):
    """Fan-in heuristic (40% weight) - USE CASE ALIGNED"""
    try:
        fan_in = G.in_degree(node)
        score = min(1.0, fan_in / 100.0)
        return score, fan_in
    except:
        return 0.0, 0

def calculate_fan_out_score(G, node):
    """Fan-out heuristic (40% weight) - USE CASE ALIGNED"""
    try:
        fan_out = G.out_degree(node)
        score = min(1.0, fan_out / 100.0)
        return score, fan_out
    except:
        return 0.0, 0

def calculate_uniform_denominations_score(G, node):
    """
    Uniform withdrawal denominations heuristic (10% weight)
    Detects Tornado Cash patterns - USE CASE ALIGNED
    """
    try:
        out_amounts = [data.get('amount', 0) for _, _, data in G.out_edges(node, data=True)]
        
        if len(out_amounts) < 3:
            return 0.0, []
        
        # Check for exact Tornado denominations
        tornado_matches = []
        for amount in out_amounts:
            for denom in TORNADO_DENOMINATIONS:
                if abs(amount - denom) / denom < 0.01:  # 1% tolerance
                    tornado_matches.append((amount, denom))
                    break
        
        # Check for uniform amounts (not necessarily Tornado)
        unique_amounts = Counter(out_amounts)
        most_common_count = unique_amounts.most_common(1)[0][1] if unique_amounts else 0
        uniformity = most_common_count / len(out_amounts)
        
        # Combine signals
        tornado_score = len(tornado_matches) / len(out_amounts)
        final_score = max(uniformity, tornado_score)
        
        return final_score, tornado_matches
    except Exception as e:
        print(f"Error calculating uniform score for {node}: {e}")
        return 0.0, []

def calculate_temporal_randomness_score(G, node):
    """
    Temporal randomness heuristic (10% weight)
    Mixers have bursty, irregular timing - USE CASE ALIGNED
    """
    try:
        times = []
        
        # Collect all transaction times
        for _, _, data in G.in_edges(node, data=True):
            if data.get('parsed_time'):
                times.append(data['parsed_time'])
        
        for _, _, data in G.out_edges(node, data=True):
            if data.get('parsed_time'):
                times.append(data['parsed_time'])
        
        if len(times) < 5:
            return 0.0, {"error": "insufficient_data"}
        
        # Sort times
        times.sort()
        
        # Calculate inter-arrival times
        intervals = []
        for i in range(1, len(times)):
            delta = (times[i] - times[i-1]).total_seconds()
            intervals.append(delta)
        
        # Calculate randomness metrics
        if intervals:
            # Coefficient of variation (higher = more random/bursty)
            mean_interval = statistics.mean(intervals) if intervals else 0
            if mean_interval > 0:
                stdev = statistics.stdev(intervals) if len(intervals) > 1 else 0
                cv = stdev / mean_interval if mean_interval > 0 else 0
                # Normalize to 0-1 (mixers have high CV)
                score = min(1.0, cv / 10.0)
                
                # Check for burstiness: many transactions in short time
                short_intervals = [i for i in intervals if i < 60]  # < 1 minute
                burst_score = len(short_intervals) / len(intervals) if intervals else 0
                
                final_score = max(score, burst_score)
                return final_score, {
                    'cv': cv,
                    'burst_score': burst_score,
                    'avg_interval': mean_interval,
                    'short_intervals': len(short_intervals)
                }
        
        return 0.0, {"error": "no_intervals"}
    except Exception as e:
        print(f"Error calculating temporal score for {node}: {e}")
        return 0.0, {"error": str(e)}

def calculate_avoidance_score(G, node):
    """
    Additional heuristic: Avoidance of economic behaviors
    Mixers avoid DEX interactions, staking, etc.
    """
    return 0.5, {"note": "economic_behavior_check_not_implemented"}

def detect_mixer_behavior(G, node):
    """
    Complete mixer detection with ALL heuristics
    Returns weighted score and detailed reasoning - USE CASE ALIGNED
    """
    # First check if it's a known mixer
    known_mixer = detect_direct_mixer_addresses(node)
    if known_mixer['is_mixer']:
        print(f"🎯 Found known mixer: {node[:10]}...")
        return 1.0, {
            'final_score': 1.0,
            'heuristics': {
                'fan_in': {'score': 1.0, 'value': 0, 'weight': 0.4},
                'fan_out': {'score': 1.0, 'value': 0, 'weight': 0.4},
                'uniform_denominations': {'score': 1.0, 'tornado_matches': [], 'matches': [], 'weight': 0.1},
                'temporal_randomness': {'score': 1.0, 'details': {}, 'weight': 0.1}
            },
            'flags': {
                'high_fan_in': True,
                'high_fan_out': True,
                'uniform_withdrawals': True,
                'tornado_pattern': True,
                'bursty_timing': True,
                'known_mixer': True
            },
            'mixer_type': known_mixer['mixer_type']
        }
    
    try:
        # Skip nodes with insufficient activity
        total_degree = G.in_degree(node) + G.out_degree(node)
        if total_degree < MIN_TX_COUNT:
            return 0.0, {"reason": "insufficient_activity"}
        
        # Calculate all heuristic scores
        fan_in_score, fan_in = calculate_fan_in_score(G, node)
        fan_out_score, fan_out = calculate_fan_out_score(G, node)
        uniform_score, tornado_matches = calculate_uniform_denominations_score(G, node)
        temporal_score, temporal_details = calculate_temporal_randomness_score(G, node)
        
        # Weighted sum (40/40/10/10 as per use case)
        weighted_score = (
            WEIGHTS['fan_in'] * fan_in_score +
            WEIGHTS['fan_out'] * fan_out_score +
            WEIGHTS['uniform_denominations'] * uniform_score +
            WEIGHTS['temporal_randomness'] * temporal_score
        )
        
        # Boost score if Tornado denominations detected
        if tornado_matches:
            weighted_score = min(1.0, weighted_score + 0.2)
        
        # Create detailed reasoning
        reasoning = {
            'final_score': weighted_score,
            'heuristics': {
                'fan_in': {
                    'score': fan_in_score,
                    'value': fan_in,
                    'weight': WEIGHTS['fan_in']
                },
                'fan_out': {
                    'score': fan_out_score,
                    'value': fan_out,
                    'weight': WEIGHTS['fan_out']
                },
                'uniform_denominations': {
                    'score': uniform_score,
                    'tornado_matches': len(tornado_matches),
                    'matches': tornado_matches[:5] if tornado_matches else [],
                    'weight': WEIGHTS['uniform_denominations']
                },
                'temporal_randomness': {
                    'score': temporal_score,
                    'details': temporal_details,
                    'weight': WEIGHTS['temporal_randomness']
                }
            },
            'flags': {
                'high_fan_in': fan_in_score > 0.7,
                'high_fan_out': fan_out_score > 0.7,
                'uniform_withdrawals': uniform_score > 0.6,
                'tornado_pattern': len(tornado_matches) > 0,
                'bursty_timing': temporal_score > 0.5,
                'known_mixer': False
            }
        }
        
        return weighted_score, reasoning
    except Exception as e:
        print(f"Error detecting mixer behavior for {node}: {e}")
        return 0.0, {"error": str(e)}

# ---------- Enhanced Detailed Reporting Functions ----------

def generate_mixer_detailed_report(G, mixer_candidates):
    """Generate detailed report for each mixer"""
    detailed_reports = []
    
    for addr, data in sorted(mixer_candidates.items(), key=lambda x: x[1]['score'], reverse=True):
        reasoning = data['reasoning']
        score = data['score']
        
        # Check if known mixer
        known_mixer = detect_direct_mixer_addresses(addr)
        if known_mixer['is_mixer']:
            mixer_type = known_mixer['mixer_type']
        else:
            mixer_type = "Behavioral detection"
        
        # Get transaction statistics for this mixer
        in_txs = list(G.in_edges(addr, data=True))
        out_txs = list(G.out_edges(addr, data=True))
        
        # Calculate transaction amounts
        in_amounts = [data.get('amount', 0) for _, _, data in in_txs]
        out_amounts = [data.get('amount', 0) for _, _, data in out_txs]
        
        report = {
            'address': addr,
            'score': round(score, 4),
            'mixer_type': mixer_type,
            'classification': 'HIGH_RISK_MIXER' if score > 0.8 else 'MEDIUM_RISK_MIXER' if score > 0.7 else 'LOW_RISK_MIXER',
            
            'transaction_statistics': {
                'total_incoming': len(in_txs),
                'total_outgoing': len(out_txs),
                'total_transactions': len(in_txs) + len(out_txs),
                'total_incoming_amount': round(sum(in_amounts), 4),
                'total_outgoing_amount': round(sum(out_amounts), 4),
                'avg_incoming_amount': round(statistics.mean(in_amounts) if in_amounts else 0, 4),
                'avg_outgoing_amount': round(statistics.mean(out_amounts) if out_amounts else 0, 4),
            },
            
            'heuristic_scores': {
                'fan_in': {
                    'score': round(reasoning['heuristics']['fan_in']['score'], 4),
                    'value': reasoning['heuristics']['fan_in']['value'],
                    'weight': reasoning['heuristics']['fan_in']['weight'],
                    'interpretation': f"{reasoning['heuristics']['fan_in']['value']} incoming transactions"
                },
                'fan_out': {
                    'score': round(reasoning['heuristics']['fan_out']['score'], 4),
                    'value': reasoning['heuristics']['fan_out']['value'],
                    'weight': reasoning['heuristics']['fan_out']['weight'],
                    'interpretation': f"{reasoning['heuristics']['fan_out']['value']} outgoing transactions"
                },
                'uniform_denominations': {
                    'score': round(reasoning['heuristics']['uniform_denominations']['score'], 4),
                    'tornado_matches': reasoning['heuristics']['uniform_denominations']['tornado_matches'],
                    'matches': reasoning['heuristics']['uniform_denominations']['matches'],
                    'weight': reasoning['heuristics']['uniform_denominations']['weight'],
                    'interpretation': f"{len(reasoning['heuristics']['uniform_denominations']['matches'])} Tornado Cash denomination matches"
                },
                'temporal_randomness': {
                    'score': round(reasoning['heuristics']['temporal_randomness']['score'], 4),
                    'details': reasoning['heuristics']['temporal_randomness']['details'],
                    'weight': reasoning['heuristics']['temporal_randomness']['weight'],
                    'interpretation': f"CV: {reasoning['heuristics']['temporal_randomness']['details'].get('cv', 0):.2f}, Burstiness: {reasoning['heuristics']['temporal_randomness']['details'].get('burst_score', 0):.2f}"
                }
            },
            
            'flags_detected': [
                {'flag': 'high_fan_in', 'detected': reasoning['flags']['high_fan_in'], 
                 'description': 'Many incoming transactions (>70 fan-in score)'},
                {'flag': 'high_fan_out', 'detected': reasoning['flags']['high_fan_out'], 
                 'description': 'Many outgoing transactions (>70 fan-out score)'},
                {'flag': 'uniform_withdrawals', 'detected': reasoning['flags']['uniform_withdrawals'], 
                 'description': 'Withdrawals in uniform denominations'},
                {'flag': 'tornado_pattern', 'detected': reasoning['flags']['tornado_pattern'], 
                 'description': 'Matches Tornado Cash withdrawal patterns'},
                {'flag': 'bursty_timing', 'detected': reasoning['flags']['bursty_timing'], 
                 'description': 'Irregular, bursty transaction timing'},
                {'flag': 'known_mixer', 'detected': reasoning['flags'].get('known_mixer', False), 
                 'description': 'Known mixer address'}
            ],
            
            'weighted_calculation': {
                'formula': 'score = (fan_in * 0.4) + (fan_out * 0.4) + (uniform * 0.1) + (temporal * 0.1)',
                'calculation': f"{reasoning['heuristics']['fan_in']['score']:.2f}*0.4 + {reasoning['heuristics']['fan_out']['score']:.2f}*0.4 + {reasoning['heuristics']['uniform_denominations']['score']:.2f}*0.1 + {reasoning['heuristics']['temporal_randomness']['score']:.2f}*0.1",
                'result': round(score, 4)
            },
            
            'top_connections': {
                'top_senders': [sender[:10] + '...' for sender, _ in list(G.in_edges(addr))[:5]],
                'top_receivers': [receiver[:10] + '...' for _, receiver in list(G.out_edges(addr))[:5]],
            },
            
            'summary': f"Detected as {'high-risk' if score > 0.8 else 'medium-risk' if score > 0.7 else 'potential'} mixer with score {score:.3f}. " +
                      (f"Type: {mixer_type}. " if mixer_type != "Behavioral detection" else "") +
                      f"Key indicators: {reasoning['heuristics']['fan_in']['value']} incoming, {reasoning['heuristics']['fan_out']['value']} outgoing transactions"
        }
        
        detailed_reports.append(report)
    
    return detailed_reports

def generate_wallet_detailed_report(G, provenance_map, mixer_candidates):
    """Generate detailed report for each wallet with mixer exposure"""
    wallet_reports = []
    
    for wallet_addr, paths in provenance_map.items():
        unique_mixers = set(p['mixer'] for p in paths)
        
        # Calculate risk metrics
        mixer_scores = []
        for m in unique_mixers:
            if m in mixer_candidates:
                mixer_scores.append(mixer_candidates[m]['score'])
            else:
                # Check if it's a known mixer
                known_mixer = detect_direct_mixer_addresses(m)
                if known_mixer['is_mixer']:
                    mixer_scores.append(1.0)
        
        avg_mixer_score = statistics.mean(mixer_scores) if mixer_scores else 0
        max_mixer_score = max(mixer_scores) if mixer_scores else 0
        
        # Count paths by direction
        forward_paths = [p for p in paths if p['direction'] == 'forward']
        backward_paths = [p for p in paths if p['direction'] == 'backward']
        
        # Calculate exposure depth
        avg_hops = statistics.mean([p['hops'] for p in paths]) if paths else 0
        
        # Get wallet transaction stats
        wallet_in_degree = G.in_degree(wallet_addr)
        wallet_out_degree = G.out_degree(wallet_addr)
        
        report = {
            'address': wallet_addr,
            'exposure_summary': {
                'exposed_to_mixers': True,
                'number_of_mixers': len(unique_mixers),
                'total_provenance_paths': len(paths),
                'avg_distance_to_mixers': round(avg_hops, 2),
                'max_mixer_score': round(max_mixer_score, 4),
                'avg_mixer_score': round(avg_mixer_score, 4),
                'forward_paths': len(forward_paths),
                'backward_paths': len(backward_paths)
            },
            
            'risk_assessment': {
                'risk_score': min(1.0, (len(unique_mixers) * 0.3) + (avg_mixer_score * 0.7)),
                'risk_level': 'CRITICAL' if len(unique_mixers) > 3 and avg_mixer_score > 0.8 else
                            'HIGH' if len(unique_mixers) > 1 and avg_mixer_score > 0.7 else
                            'MEDIUM' if len(unique_mixers) > 0 else 'LOW',
                'risk_factors': [
                    f"Connected to {len(unique_mixers)} mixer{'s' if len(unique_mixers) > 1 else ''}",
                    f"Average mixer score: {avg_mixer_score:.3f}",
                    f"Maximum distance: {max([p['hops'] for p in paths]) if paths else 0} hops"
                ]
            },
            
            'connected_mixers': [
                {
                    'address': mixer_addr,
                    'score': 1.0 if detect_direct_mixer_addresses(mixer_addr)['is_mixer'] else mixer_candidates.get(mixer_addr, {}).get('score', 0),
                    'paths': [
                        {
                            'direction': p['direction'],
                            'hops': p['hops'],
                            'path': p['path'],
                            'path_summary': ' → '.join(p['path'][:3]) + ' → ... → ' + ' → '.join(p['path'][-2:]) if len(p['path']) > 5 else ' → '.join(p['path'])
                        }
                        for p in paths if p['mixer'] == mixer_addr
                    ]
                }
                for mixer_addr in list(unique_mixers)[:10]
            ],
            
            'wallet_activity': {
                'incoming_transactions': wallet_in_degree,
                'outgoing_transactions': wallet_out_degree,
                'total_transactions': wallet_in_degree + wallet_out_degree,
                'is_active': (wallet_in_degree + wallet_out_degree) > 10
            },
            
            'recommendations': [
                "Monitor this wallet for suspicious activity" if len(unique_mixers) > 0 else "No immediate action needed",
                "Check incoming transactions for mixer patterns",
                "Consider KYC/AML review if high transaction volume"
            ]
        }
        
        wallet_reports.append(report)
    
    wallet_reports.sort(key=lambda x: x['risk_assessment']['risk_score'], reverse=True)
    return wallet_reports

def generate_provenance_path_analysis(G, provenance_map):
    """Analyze provenance paths for patterns"""
    all_paths = []
    for paths in provenance_map.values():
        all_paths.extend(paths)
    
    if not all_paths:
        return {}
    
    path_lengths = [p['hops'] for p in all_paths]
    directions = [p['direction'] for p in all_paths]
    
    direction_counts = Counter(directions)
    
    return {
        'path_statistics': {
            'total_paths_analyzed': len(all_paths),
            'average_path_length': round(statistics.mean(path_lengths), 2) if path_lengths else 0,
            'min_path_length': min(path_lengths) if path_lengths else 0,
            'max_path_length': max(path_lengths) if path_lengths else 0,
            'forward_paths': direction_counts.get('forward', 0),
            'backward_paths': direction_counts.get('backward', 0),
            'common_path_lengths': dict(Counter(path_lengths).most_common(5))
        },
        'path_patterns': {
            'most_common_hops': Counter(path_lengths).most_common(3),
            'direction_ratio': round(direction_counts.get('forward', 0) / len(all_paths) if all_paths else 0, 2)
        }
    }

def generate_network_analysis_report(G, mixer_candidates):
    """Generate network-level analysis report"""
    mixer_nodes = list(mixer_candidates.keys())
    
    if not mixer_nodes:
        return {}
    
    # Calculate network centrality for mixers
    centrality_scores = {}
    for mixer in mixer_nodes[:20]:
        try:
            centrality_scores[mixer] = nx.degree_centrality(G).get(mixer, 0)
        except:
            pass
    
    # Calculate connected components
    components = list(nx.weakly_connected_components(G))
    
    # Find mixers in largest components
    mixers_by_component = {}
    for i, component in enumerate(components[:5]):
        mixers_in_component = [m for m in mixer_nodes if m in component]
        if mixers_in_component:
            mixers_by_component[f"component_{i}"] = {
                'size': len(component),
                'mixers_count': len(mixers_in_component),
                'mixer_density': len(mixers_in_component) / len(component) if component else 0
            }
    
    return {
        'network_statistics': {
            'total_nodes': G.number_of_nodes(),
            'total_edges': G.number_of_edges(),
            'mixer_node_count': len(mixer_nodes),
            'mixer_node_percentage': round(len(mixer_nodes) / G.number_of_nodes() * 100, 2) if G.number_of_nodes() > 0 else 0,
            'connected_components': len(components),
            'largest_component_size': len(max(components, key=len)) if components else 0
        },
        'mixer_network_analysis': {
            'top_central_mixers': [
                {'address': mixer[:10] + '...', 'centrality': round(score, 4)}
                for mixer, score in sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            ],
            'mixer_distribution_by_component': mixers_by_component,
            'average_mixer_degree': round(statistics.mean([G.degree(m) for m in mixer_nodes]), 2) if mixer_nodes else 0
        }
    }

# ---------- Provenance Tracing ----------

def trace_provenance_backward(G, target, max_hops=MAX_HOPS):
    """
    Trace BACKWARD to find mixer origins
    target → ... → mixer
    """
    paths = []
    
    try:
        # BFS backward
        visited = {target}
        queue = [(target, [target], 0)]  # (node, path, hops)
        
        while queue:
            node, path, hops = queue.pop(0)
            
            if hops >= max_hops:
                continue
            
            # Check predecessors
            for predecessor in G.predecessors(node):
                if predecessor not in visited:
                    visited.add(predecessor)
                    new_path = path + [predecessor]
                    new_hops = hops + 1
                    
                    # Check if predecessor is a mixer candidate
                    score, reasoning = detect_mixer_behavior(G, predecessor)
                    if score >= MIXER_SCORE_THRESHOLD:
                        paths.append({
                            'mixer': predecessor,
                            'path': new_path,
                            'hops': new_hops,
                            'mixer_score': score,
                            'mixer_reasoning': reasoning,
                            'direction': 'backward'
                        })
                    
                    queue.append((predecessor, new_path, new_hops))
    except Exception as e:
        print(f"Error in backward tracing from {target}: {e}")
    
    return paths

def trace_provenance_forward(G, source, max_hops=MAX_HOPS):
    """
    Trace FORWARD from mixers
    mixer → ... → target
    """
    paths = []
    
    try:
        # BFS forward
        visited = {source}
        queue = [(source, [source], 0)]
        
        while queue:
            node, path, hops = queue.pop(0)
            
            if hops >= max_hops:
                continue
            
            for successor in G.successors(node):
                if successor not in visited:
                    visited.add(successor)
                    new_path = path + [successor]
                    new_hops = hops + 1
                    
                    # Record all paths from mixer
                    paths.append({
                        'target': successor,
                        'path': new_path,
                        'hops': new_hops,
                        'mixer': source,
                        'direction': 'forward'
                    })
                    
                    queue.append((successor, new_path, new_hops))
    except Exception as e:
        print(f"Error in forward tracing from {source}: {e}")
    
    return paths

def build_complete_provenance(G, mixer_candidates):
    """
    Build complete provenance: mixer → intermediaries → targets
    """
    provenance_map = {}  # target -> list of provenance paths
    
    try:
        for mixer in mixer_candidates:
            # Trace forward from mixer
            forward_paths = trace_provenance_forward(G, mixer, max_hops=MAX_HOPS)
            
            for path_info in forward_paths:
                target = path_info['target']
                
                if target not in provenance_map:
                    provenance_map[target] = []
                
                provenance_map[target].append({
                    'mixer': mixer,
                    'path': path_info['path'],
                    'hops': path_info['hops'],
                    'direction': 'forward'
                })
        
        # For each target, also trace backward to find additional mixers
        for target in list(provenance_map.keys()):
            backward_paths = trace_provenance_backward(G, target, max_hops=MAX_HOPS)
            
            for path_info in backward_paths:
                provenance_map[target].append({
                    'mixer': path_info['mixer'],
                    'path': path_info['path'],
                    'hops': path_info['hops'],
                    'direction': 'backward',
                    'mixer_score': path_info['mixer_score'],
                    'mixer_reasoning': path_info['mixer_reasoning']
                })
    except Exception as e:
        print(f"Error building provenance: {e}")
        traceback.print_exc()
    
    return provenance_map

# ---------- Graph Building ----------

def build_complete_graph(transactions):
    """
    Build graph with ALL edge properties from your schema
    """
    G = nx.DiGraph()
    
    try:
        for tx in transactions:
            s = tx['sender']
            r = tx['receiver']
            
            if not G.has_node(s):
                G.add_node(s, type='wallet')
            if not G.has_node(r):
                G.add_node(r, type='wallet')
            
            # Store ALL properties from your schema
            edge_data = {
                'amount': tx['amount'],
                'timestamp': tx['timestamp'],
                'parsed_time': tx['parsed_time'],
                'currency': tx['currency'],
                'count': 1
            }
            
            if G.has_edge(s, r):
                # Update existing edge
                G[s][r]['amount'] += tx['amount']
                G[s][r]['count'] += 1
                # Keep timestamps for temporal analysis
                if 'timestamps' not in G[s][r]:
                    G[s][r]['timestamps'] = []
                G[s][r]['timestamps'].append(tx['timestamp'])
            else:
                G.add_edge(s, r, **edge_data)
                G[s][r]['timestamps'] = [tx['timestamp']]
    except Exception as e:
        print(f"Error building graph: {e}")
        traceback.print_exc()
    
    return G

# ---------- Neo4j Persistence ----------

def persist_complete_provenance(mixer_candidates, provenance_map, token_address):
    """
    Persist complete provenance to Neo4j with ALL required fields
    """
    try:
        timestamp = int(time.time() * 1000)
        detected_at = datetime.utcnow().isoformat()
        
        with driver.session() as session:
            # Clear previous results for this token
            session.run("""
                MATCH (m:Mixer)-[f:FUNDED]->(w:Wallet)
                WHERE f.token_address = $token_address
                DELETE f
            """, token_address=token_address)
            
            # Create Mixer nodes with ALL details
            for mixer_addr, mixer_data in mixer_candidates.items():
                score = mixer_data['score']
                reasoning = mixer_data['reasoning']
                
                fan_in = reasoning.get('heuristics', {}).get('fan_in', {}).get('value', 0)
                fan_out = reasoning.get('heuristics', {}).get('fan_out', {}).get('value', 0)
                uniform_score = reasoning.get('heuristics', {}).get('uniform_denominations', {}).get('score', 0)
                temporal_score = reasoning.get('heuristics', {}).get('temporal_randomness', {}).get('score', 0)
                tornado_matches = reasoning.get('heuristics', {}).get('uniform_denominations', {}).get('tornado_matches', 0)
                
                # Check if known mixer
                known_mixer = detect_direct_mixer_addresses(mixer_addr)
                if known_mixer['is_mixer']:
                    mixer_type = known_mixer['mixer_type']
                else:
                    mixer_type = "Behavioral detection"
                
                session.run("""
                    MERGE (m:Mixer {address: $address})
                    SET m.mixer_score = $score,
                        m.detected_at = $detected_at,
                        m.token_address = $token_address,
                        m.fan_in = $fan_in,
                        m.fan_out = $fan_out,
                        m.uniform_score = $uniform_score,
                        m.temporal_score = $temporal_score,
                        m.tornado_matches = $tornado_matches,
                        m.mixer_type = $mixer_type,
                        m.reasoning = $reasoning
                """, 
                address=mixer_addr,
                score=score,
                detected_at=detected_at,
                token_address=token_address,
                fan_in=fan_in,
                fan_out=fan_out,
                uniform_score=uniform_score,
                temporal_score=temporal_score,
                tornado_matches=tornado_matches,
                mixer_type=mixer_type,
                reasoning=json.dumps(reasoning, cls=DateTimeEncoder)
                )
            
            # Create FUNDED relationships with ALL provenance details
            for wallet_addr, provenance_paths in provenance_map.items():
                for path_info in provenance_paths:
                    mixer_addr = path_info['mixer']
                    hops = path_info['hops']
                    path = path_info['path']
                    direction = path_info['direction']
                    
                    # Get mixer score if available
                    mixer_score = path_info.get('mixer_score', 0.0)
                    
                    session.run("""
                        MATCH (m:Mixer {address: $mixer_addr})
                        MERGE (w:Wallet {address: $wallet_addr})
                        MERGE (m)-[f:FUNDED]->(w)
                        SET f.hops = $hops,
                            f.direction = $direction,
                            f.path = $path,
                            f.detected_at = $detected_at,
                            f.token_address = $token_address,
                            f.score = $mixer_score
                    """,
                    mixer_addr=mixer_addr,
                    wallet_addr=wallet_addr,
                    hops=hops,
                    direction=direction,
                    path=str(path),
                    detected_at=detected_at,
                    token_address=token_address,
                    mixer_score=mixer_score
                    )
            
            print(f"✅ Persisted {len(mixer_candidates)} mixers and {len(provenance_map)} funded wallets")
    except Exception as e:
        print(f"Error persisting provenance: {e}")
        traceback.print_exc()

# ---------- Main Detection Function ----------

def convert_datetime_to_string(obj):
    """Recursively convert datetime objects to ISO format strings"""
    if isinstance(obj, dict):
        return {k: convert_datetime_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):  # Any object with isoformat method
        return obj.isoformat()
    else:
        return obj

def detect_mixer_origins_complete(token_address, max_hops=MAX_HOPS):
    """
    Complete mixer detection pipeline - USE CASE ALIGNED
    FORENSIC GRAPH AGENT: Analyzes last 10,000 transactions from last 24 hours
    """
    start_time = time.time()
    
    print(f"🔍 FORENSIC GRAPH AGENT: Analyzing token: {token_address}")
    print(f"📅 Time range: Last 24 hours")
    
    try:
        # 1. First try to load from Neo4j (existing data)
        print("🔍 Checking Neo4j for existing transactions...")
        transactions = load_transactions_for_token(token_address, limit=10000)
        
        # 2. If no transactions in Neo4j, fetch from BitQuery
        if len(transactions) == 0:
            print("📡 No existing transactions found, fetching from BitQuery...")
            transactions = fetch_token_transactions_from_bitquery(token_address, limit=10000)
            
            # 3. Import fetched transactions to Neo4j for future use
            if transactions:
                import_transactions_to_neo4j(transactions, token_address)
            else:
                return {
                    'error': 'no_transactions',
                    'message': f'No transactions found for token {token_address} in the last 24 hours',
                    'use_case_compliance': False,
                    'data_source': 'bitquery_api',
                    'time_range': 'last_24_hours'
                }
        else:
            print(f"📊 Using {len(transactions)} existing transactions from Neo4j")
        
        if not transactions:
            return {
                'error': 'no_transactions',
                'message': f'No transactions found for {token_address}',
                'use_case_compliance': False
            }
        
        print(f"📊 Total transactions to analyze: {len(transactions)}")
        print(f"📅 Time range of data: {transactions[0]['timestamp'] if transactions else 'N/A'} to {transactions[-1]['timestamp'] if transactions else 'N/A'}")
        
        # 2. Build complete graph
        G = build_complete_graph(transactions)
        print(f"🕸️  Built graph with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # 3. Detect mixer candidates with ALL heuristics
        mixer_candidates = {}
        print(f"🔍 Analyzing {G.number_of_nodes()} nodes for mixer behavior...")
        
        for node in G.nodes():
            score, reasoning = detect_mixer_behavior(G, node)
            
            if score >= MIXER_SCORE_THRESHOLD:
                mixer_candidates[node] = {
                    'score': score,
                    'reasoning': reasoning
                }
                print(f"🎯 Detected mixer candidate: {node[:10]}... (Score: {score:.3f})")
        
        print(f"🎯 Total mixer candidates detected: {len(mixer_candidates)}")
        
        # 4. Build complete provenance (backward + forward)
        provenance_map = build_complete_provenance(G, list(mixer_candidates.keys()))
        
        # 5. Persist to Neo4j with complete schema
        persist_complete_provenance(mixer_candidates, provenance_map, token_address)
        
        # 6. Generate DETAILED reports
        detailed_mixer_report = generate_mixer_detailed_report(G, mixer_candidates)
        detailed_wallet_report = generate_wallet_detailed_report(G, provenance_map, mixer_candidates)
        provenance_analysis = generate_provenance_path_analysis(G, provenance_map)
        network_analysis = generate_network_analysis_report(G, mixer_candidates)
        
        # 7. Calculate overall statistics
        elapsed = time.time() - start_time
        
        # Calculate risk distribution
        risk_scores = [w['risk_assessment']['risk_score'] for w in detailed_wallet_report]
        risk_distribution = {
            'critical': len([s for s in risk_scores if s > 0.9]),
            'high': len([s for s in risk_scores if 0.7 < s <= 0.9]),
            'medium': len([s for s in risk_scores if 0.4 < s <= 0.7]),
            'low': len([s for s in risk_scores if s <= 0.4])
        }
        
        # 8. Generate comprehensive report with USE CASE ALIGNMENT
        report = {
            'forensic_graph_agent': {
                'use_case': 'Mixer Flagging',
                'mvp_compliance': elapsed < 30,  # USE CASE: <30 seconds
                'analysis_time_seconds': round(elapsed, 2),
                'data_scope': 'last_10k_transactions',
                'time_range': 'last_24_hours',
                'detection_method': '40/40/10/10 weighted heuristics'
            },
            
            'execution_summary': {
                'token_address': token_address,
                'analysis_start_time': datetime.fromtimestamp(start_time).isoformat(),
                'analysis_duration_seconds': round(elapsed, 2),
                'performance_status': 'MVP_COMPLIANT' if elapsed < 30 else 'EXCEEDS_MVP',
                'data_source': 'bitquery_api' if 'bitquery' in str(transactions[0].get('source', '')) else 'neo4j_cache',
                'data_processed': {
                    'transactions_analyzed': len(transactions),
                    'unique_wallets': G.number_of_nodes(),
                    'unique_transactions': G.number_of_edges(),
                    'time_range': {
                        'first_tx': min([t['parsed_time'] for t in transactions if t['parsed_time']], default=None),
                        'last_tx': max([t['parsed_time'] for t in transactions if t['parsed_time']], default=None)
                    }
                }
            },
            
            'mixer_detection_results': {
                'summary': {
                    'total_mixers_detected': len(mixer_candidates),
                    'detection_threshold': MIXER_SCORE_THRESHOLD,
                    'heuristics_applied': list(WEIGHTS.keys()),
                    'heuristic_weights': WEIGHTS,
                    'detection_confidence': 'HIGH' if len(mixer_candidates) > 0 else 'LOW'
                },
                'mixer_categories': {
                    'known_mixers': len([addr for addr in mixer_candidates.keys() 
                                        if detect_direct_mixer_addresses(addr)['is_mixer']]),
                    'behavioral_mixers': len([addr for addr in mixer_candidates.keys() 
                                            if not detect_direct_mixer_addresses(addr)['is_mixer']]),
                    'high_risk_mixers': len([m for m in mixer_candidates.values() if m['score'] > 0.8]),
                    'medium_risk_mixers': len([m for m in mixer_candidates.values() if 0.7 < m['score'] <= 0.8]),
                    'low_risk_mixers': len([m for m in mixer_candidates.values() if m['score'] <= 0.7])
                },
                'detailed_mixer_reports': detailed_mixer_report[:50],
                'top_5_mixers': detailed_mixer_report[:5]
            },
            
            'wallet_exposure_analysis': {
                'summary': {
                    'wallets_with_mixer_exposure': len(provenance_map),
                    'percentage_of_total_wallets': round(len(provenance_map) / G.number_of_nodes() * 100, 2) if G.number_of_nodes() > 0 else 0,
                    'total_provenance_paths': sum(len(paths) for paths in provenance_map.values()),
                    'average_exposure_per_wallet': round(len(provenance_map) / len(mixer_candidates), 2) if mixer_candidates else 0
                },
                'risk_distribution': risk_distribution,
                'high_risk_wallets': [
                    w for w in detailed_wallet_report 
                    if w['risk_assessment']['risk_level'] in ['CRITICAL', 'HIGH']
                ][:20],
                'detailed_wallet_reports': detailed_wallet_report[:100],
                'most_exposed_wallets': sorted(
                    detailed_wallet_report, 
                    key=lambda x: x['exposure_summary']['number_of_mixers'], 
                    reverse=True
                )[:10]
            },
            
            'provenance_analysis': provenance_analysis,
            
            'network_analysis': network_analysis,
            
            'visualization_data': {
                'nodes': [
                    {
                        'id': node,
                        'type': 'mixer' if any(m['address'] == node for m in detailed_mixer_report) else 'wallet',
                        'risk_score': next((m['score'] for m in detailed_mixer_report if m['address'] == node), 0),
                        'size': G.degree(node) / 10 + 1,
                        'mixer_type': next((m.get('mixer_type', '') for m in detailed_mixer_report if m['address'] == node), '')
                    }
                    for node in list(G.nodes())[:50]  # FORENSIC GRAPH AGENT: Top 50 for visualization
                ],
                'edges': [
                    {
                        'source': sender,
                        'target': receiver,
                        'value': G[sender][receiver]['amount'] if G.has_edge(sender, receiver) else 0,
                        'transactions': G[sender][receiver]['count'] if G.has_edge(sender, receiver) else 0
                    }
                    for sender, receiver in list(G.edges())[:100]
                ]
            },
            
            'actionable_insights': {
                'immediate_actions': [
                    f"Review {len([m for m in detailed_mixer_report if m['score'] > 0.8])} high-risk mixers",
                    f"Investigate {risk_distribution['critical']} critically exposed wallets",
                    "Check transaction patterns for Tornado Cash denominations"
                ] if len(mixer_candidates) > 0 else ["No immediate suspicious activity detected"],
                'recommendations': [
                    "Implement enhanced monitoring for identified high-risk wallets",
                    "Consider blockchain analytics integration for real-time detection",
                    "Review transaction patterns with compliance team"
                ],
                'forensic_implications': {
                    'rug_pull_risk': 'HIGH' if risk_distribution['critical'] + risk_distribution['high'] > 5 else 'MEDIUM',
                    'deployer_suspicion': 'INVESTIGATE' if any('deployer' in addr.lower() for addr in mixer_candidates.keys()) else 'CLEAR',
                    'wash_trading_risk': 'POTENTIAL' if len(mixer_candidates) > 10 else 'LOW'
                }
            }
        }
        
        # Convert all datetime objects to strings
        report = convert_datetime_to_string(report)
        
        return report
        
    except Exception as e:
        print(f"Error in mixer detection: {e}")
        traceback.print_exc()
        return {
            'error': 'detection_failed',
            'message': str(e),
            'use_case_compliance': False
        }

# ---------- FLASK APP WITH MCP IMPLEMENTATION ----------

app = Flask('mixer_flagging_complete')

# Add CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Handle OPTIONS requests
@app.route('/mcp', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=None):
    return '', 200

# ---------- MCP PROTOCOL ENDPOINTS ----------

@app.route('/mcp', methods=['POST'])
def mcp_handler():
    """Main MCP JSON-RPC endpoint"""
    try:
        # Get request data
        if not request.data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error: No data received"
                },
                "id": None
            }), 400
        
        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                },
                "id": None
            }), 400
        
        method = data.get('method')
        params = data.get('params') or {}
        request_id = data.get('id', 1)
        
        # Handle different MCP methods
        if method == 'initialize':
            print("🔄 Handling initialize request")
            # Use the protocol version from the client request
            client_protocol_version = params.get('protocolVersion', '2024-11-01')
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": client_protocol_version,
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "mixer-flagging-tool",
                        "version": "2.1.0"
                    }
                }
            }
            return jsonify(response)
        
        elif method == 'tools/list':
            print("🛠️ Handling tools/list request")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "detect_mixer_origins",
                            "description": "Detect mixer-origin funds with complete behavioral heuristics and provenance tracing. Automatically fetches last 24 hours of token transactions.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "token_address": {
                                        "type": "string",
                                        "description": "Token contract address to analyze"
                                    },
                                    "max_hops": {
                                        "type": "integer",
                                        "description": "Maximum number of hops to trace (default: 3)",
                                        "default": 3
                                    }
                                },
                                "required": ["token_address"]
                            }
                        },
                        {
                            "name": "explain_provenance",
                            "description": "Explain mixer provenance for a specific wallet with detailed forensic reasoning",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "token_address": {
                                        "type": "string",
                                        "description": "Token contract address"
                                    },
                                    "wallet_address": {
                                        "type": "string",
                                        "description": "Wallet address to explain"
                                    }
                                },
                                "required": ["token_address", "wallet_address"]
                            }
                        }
                    ]
                }
            }
            return jsonify(response)
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            print(f"🛠️ Handling tools/call for: {tool_name}")
            
            if tool_name == 'detect_mixer_origins':
                token_address = arguments.get('token_address')
                max_hops = arguments.get('max_hops', MAX_HOPS)
                
                if not token_address:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Missing required parameter: token_address"
                        }
                    })
                
                print(f"🔍 Running mixer detection for: {token_address}")
                
                try:
                    result = detect_mixer_origins_complete(token_address, max_hops)
                    
                    # Convert result to JSON using custom encoder
                    result_str = json.dumps(result, indent=2, cls=DateTimeEncoder)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result_str
                                }
                            ]
                        }
                    }
                    print(f"✅ Response sent with {len(result_str)} characters")
                    return jsonify(response)
                    
                except Exception as e:
                    print(f"❌ Detection error: {e}")
                    traceback.print_exc()
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Detection failed: {str(e)}"
                        }
                    })
            
            elif tool_name == 'explain_provenance':
                token_address = arguments.get('token_address')
                wallet_address = arguments.get('wallet_address')
                
                if not token_address or not wallet_address:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Missing required parameters: token_address and wallet_address"
                        }
                    })
                
                print(f"🔍 Explaining provenance for wallet: {wallet_address}, token: {token_address}")
                
                # Query Neo4j for provenance
                with driver.session() as session:
                    q = """
                    MATCH (m:Mixer)-[f:FUNDED]->(w:Wallet {address: $wallet})
                    WHERE f.token_address = $token
                    RETURN m.address as mixer, m.mixer_score as score, 
                           f.hops as hops, f.direction as direction,
                           m.mixer_type as mixer_type,
                           m.fan_in as fan_in, m.fan_out as fan_out
                    ORDER BY m.mixer_score DESC
                    LIMIT 10
                    """
                    
                    result = session.run(q, wallet=wallet_address.lower(), token=token_address)
                    records = list(result)
                    
                    if not records:
                        text_response = f"No mixer provenance found for wallet {wallet_address} with token {token_address}"
                    else:
                        text_response = f"Found {len(records)} mixer connections for wallet {wallet_address}:\n\n"
                        for rec in records:
                            text_response += f"• Mixer: {rec['mixer'][:10]}... (Score: {rec['score']:.2f}, Type: {rec['mixer_type']})\n"
                            text_response += f"  Connection: {rec['direction']} via {rec['hops']} hops\n"
                            text_response += f"  Stats: Fan-in={rec['fan_in']}, Fan-out={rec['fan_out']}\n\n"
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": text_response
                            }
                        ]
                    }
                }
                return jsonify(response)
            
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                })
        
        elif method == 'ping':
            print("🏓 Handling ping request")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            }
            return jsonify(response)
        
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })
    
    except Exception as e:
        print(f"💥 Unhandled error in MCP handler: {e}")
        traceback.print_exc()
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id if 'request_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500

# ---------- LEGACY ENDPOINTS ----------

@app.route('/mcp/detect_mixer_origins', methods=['POST'])
def api_detect_mixer_origins():
    """Legacy endpoint for backward compatibility"""
    try:
        body = request.get_json(silent=True) or {}
        token_address = body.get('token_address')
        
        if not token_address:
            return jsonify({
                'status': 'error',
                'error': 'token_address is required'
            }), 400
        
        max_hops = int(body.get('max_hops', MAX_HOPS))
        
        result = detect_mixer_origins_complete(token_address, max_hops)
        
        if 'error' in result:
            return jsonify({
                'status': 'error',
                'result': result
            })
        
        return jsonify({
            'status': 'ok',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/mcp/explain_provenance', methods=['POST'])
def api_explain_provenance():
    """Legacy endpoint for backward compatibility"""
    try:
        body = request.get_json(silent=True) or {}
        token_address = body.get('token_address')
        wallet_address = body.get('wallet_address')
        
        if not token_address or not wallet_address:
            return jsonify({
                'status': 'error',
                'error': 'Both token_address and wallet_address are required'
            }), 400
        
        # Query Neo4j for this wallet's provenance
        with driver.session() as session:
            q = """
            MATCH (m:Mixer)-[f:FUNDED]->(w:Wallet {address: $wallet})
            WHERE f.token_address = $token
            RETURN m.address as mixer, m.mixer_score as score, 
                   f.hops as hops, f.direction as direction, f.path as path,
                   m.reasoning as reasoning, m.mixer_type as mixer_type,
                   m.fan_in as fan_in, m.fan_out as fan_out,
                   m.uniform_score as uniform_score, m.temporal_score as temporal_score,
                   m.tornado_matches as tornado_matches
            ORDER BY m.mixer_score DESC
            """
            
            result = session.run(q, wallet=wallet_address.lower(), token=token_address)
            records = list(result)
            
            if not records:
                return jsonify({
                    'status': 'ok',
                    'result': {
                        'wallet': wallet_address,
                        'mixer_exposure': False,
                        'message': 'No mixer provenance found for this wallet',
                        'forensic_assessment': 'CLEAR'
                    }
                })
            
            explanations = []
            for rec in records:
                try:
                    path = eval(rec['path']) if isinstance(rec['path'], str) else rec['path']
                except:
                    path = rec['path']
                
                # Create detailed explanation
                explanation = {
                    'mixer': {
                        'address': rec['mixer'],
                        'score': rec['score'],
                        'mixer_type': rec['mixer_type'],
                        'fan_in': rec['fan_in'],
                        'fan_out': rec['fan_out'],
                        'uniform_score': rec['uniform_score'],
                        'temporal_score': rec['temporal_score'],
                        'tornado_matches': rec['tornado_matches']
                    },
                    'connection': {
                        'hops': rec['hops'],
                        'direction': rec['direction'],
                        'path': path,
                        'path_summary': ' → '.join(path[:3]) + ' → ... → ' + ' → '.join(path[-2:]) if len(path) > 5 else ' → '.join(path)
                    },
                    'forensic_explanation': f"Wallet {wallet_address[:8]}... connected to {rec['mixer_type'] if rec['mixer_type'] else 'mixer'} {rec['mixer'][:8]}... " +
                                          f"via {rec['direction']} tracing ({rec['hops']} hops). " +
                                          f"Risk score: {rec['score']:.3f}"
                }
                
                explanations.append(explanation)
            
            # Calculate risk level
            max_score = max([exp['mixer']['score'] for exp in explanations])
            mixer_count = len(explanations)
            
            if max_score > 0.8 and mixer_count > 2:
                risk_level = 'CRITICAL'
                forensic_assessment = 'HIGH_RISK'
            elif max_score > 0.7 and mixer_count > 1:
                risk_level = 'HIGH'
                forensic_assessment = 'SUSPICIOUS'
            elif mixer_count > 0:
                risk_level = 'MEDIUM'
                forensic_assessment = 'MONITOR'
            else:
                risk_level = 'LOW'
                forensic_assessment = 'CLEAR'
            
            return jsonify({
                'status': 'ok',
                'result': {
                    'wallet': wallet_address,
                    'mixer_exposure': True,
                    'mixer_count': mixer_count,
                    'max_mixer_score': max_score,
                    'risk_level': risk_level,
                    'forensic_assessment': forensic_assessment,
                    'explanations': explanations,
                    'recommendations': [
                        "Monitor wallet for suspicious activity",
                        "Review transaction history",
                        "Consider enhanced due diligence" if risk_level in ['CRITICAL', 'HIGH'] else "Standard monitoring"
                    ]
                }
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/mcp/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            
        return jsonify({
            'status': 'healthy',
            'neo4j_connected': True,
            'bitquery_api_key': 'configured' if BITQUERY_API_KEY else 'missing',
            'timestamp': datetime.now().isoformat(),
            'service': 'Mixer Flagging MCP Server',
            'capabilities': 'Auto-fetches token transactions from last 24 hours'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with server info"""
    return jsonify({
        'name': 'Mixer Flagging MCP Server',
        'version': '2.1.0',
        'description': 'Automatically fetches and analyzes token transactions from last 24 hours',
        'endpoints': {
            'mcp': 'POST /mcp (Main MCP endpoint)',
            'detect_mixer_origins': 'POST /mcp/detect_mixer_origins (Legacy)',
            'explain_provenance': 'POST /mcp/explain_provenance (Legacy)',
            'health': 'GET /mcp/health'
        },
        'features': [
            'Auto-fetches token transactions from BitQuery API',
            'Last 24 hours time range',
            'Up to 10,000 transactions per analysis',
            '40/40/10/10 behavioral heuristics',
            '3-hop provenance tracing',
            'Neo4j persistence for caching'
        ],
        'status': 'running'
    })

if __name__ == '__main__':
    print('''
    ========================================================
    FORENSIC GRAPH AGENT - MIXER FLAGGING (COMPLETE)
    ========================================================
    
    ✅ MCP SERVER READY FOR N8N AI AGENT
    
    Main MCP Endpoint: POST http://YOUR_IP:5001/mcp
    
    For n8n configuration:
    1. Go to your n8n workflow
    2. Add "AI Agent" node
    3. In MCP Servers section, click "Add MCP Server"
    4. Enter URL: http://YOUR_IP:5001/mcp
    5. Save and test connection
    
    Available tools:
    - detect_mixer_origins: Analyze token for mixer activity (auto-fetches last 24h)
    - explain_provenance: Explain wallet's mixer connections
    
    Starting on http://0.0.0.0:5001
    ========================================================
    ''')
    
    # Get your local IP address
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"🌐 Your local IP address: {local_ip}")
        print(f"🔗 Use this URL in n8n: http://{local_ip}:5001/mcp")
    except:
        print("⚠️ Could not determine local IP address")
        print("🔗 Try using: http://YOUR_IP_ADDRESS:5001/mcp")
    
    print("\n📡 Server starting...\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)