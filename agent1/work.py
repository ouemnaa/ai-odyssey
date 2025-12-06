import requests
import networkx as nx
import community as community_louvain
from datetime import datetime, timedelta
from collections import defaultdict
import json
import sys
import time
import csv

class ForensicGraphAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.G = nx.DiGraph()
        self.internal_G = nx.DiGraph()
        self.combined_G = nx.DiGraph()
        self.token_holders = {}
        self.transactions_cache = []
        
    def fetch_real_transactions(self, days_back=7, limit=5000, currency="ETH", token_contract_address=None):
        """Récupère les transactions réelles depuis BitQuery"""
        start_time = time.time()
        
        if token_contract_address:
            print(f"\n📡 Récupération des transactions de token ({token_contract_address[:20]}..., {days_back} jours)...")
        else:
            print(f"\n📡 Récupération des transactions réelles ({currency}, {days_back} jours)...")
        
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        # Construire la requête selon si c'est un token spécifique ou une devise native
        if token_contract_address:
            # Requête pour un token ERC-20 spécifique
            query = """
            {
              ethereum(network: ethereum) {
                transfers(
                  options: {limit: %s, desc: "block.timestamp.time"}
                  date: {since: "%s"}
                  currency: {is: "%s"}
                ) {
                  block {
                    timestamp { 
                      time(format: "%%Y-%%m-%%d %%H:%%M:%%S")
                    }
                    height
                  }
                  amount
                  sender { 
                    address
                    annotation
                  }
                  receiver { 
                    address
                    annotation
                  }
                  transaction {
                    hash
                  }
                  currency {
                    symbol
                    address
                  }
                }
              }
            }
            """ % (limit, since_date, token_contract_address)
        else:
            # Requête pour une devise native (ETH)
            query = """
            {
              ethereum(network: ethereum) {
                transfers(
                  options: {limit: %s, desc: "block.timestamp.time"}
                  date: {since: "%s"}
                  currency: {is: "%s"}
                ) {
                  block {
                    timestamp { 
                      time(format: "%%Y-%%m-%%d %%H:%%M:%%S")
                    }
                    height
                  }
                  amount
                  sender { 
                    address
                    annotation
                  }
                  receiver { 
                    address
                    annotation
                  }
                  transaction {
                    hash
                  }
                  currency {
                    symbol
                    address
                  }
                }
              }
            }
            """ % (limit, since_date, currency)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                "https://graphql.bitquery.io",
                json={"query": query},
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print(f"⚠️  Erreur BitQuery: {data['errors'][0]['message'][:100]}...")
                    return []
                
                transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
                
                if transfers:
                    elapsed_time = time.time() - start_time
                    
                    if token_contract_address:
                        print(f"✅ {len(transfers)} transactions de token récupérées")
                        currency_symbol = transfers[0]['currency']['symbol'] if transfers and 'currency' in transfers[0] else "TOKEN"
                    else:
                        print(f"✅ {len(transfers)} transactions réelles récupérées ({currency})")
                        currency_symbol = currency
                    
                    print(f"   ⏱️  Temps de fetch: {elapsed_time:.2f}s")
                    
                    # Afficher un échantillon
                    if transfers:
                        print(f"   • Exemple: {transfers[0]['sender']['address'][:12]}... → {transfers[0]['receiver']['address'][:12]}... ({float(transfers[0]['amount']):.4f} {currency_symbol})")
                    
                    # Statistiques
                    total_amount = sum(float(tx['amount']) for tx in transfers)
                    avg_amount = total_amount / len(transfers) if transfers else 0
                    print(f"   • Montant total: {total_amount:.4f} {currency_symbol}")
                    print(f"   • Montant moyen: {avg_amount:.4f} {currency_symbol}")
                    
                    return transfers
                else:
                    elapsed_time = time.time() - start_time
                    print(f"⚠️  Aucune transaction trouvée (temps: {elapsed_time:.2f}s)")
                    return []
            else:
                elapsed_time = time.time() - start_time
                print(f"⚠️  Erreur HTTP {response.status_code} (temps: {elapsed_time:.2f}s)")
                return []
                
        except requests.exceptions.Timeout:
            elapsed_time = time.time() - start_time
            print(f"⏰ Timeout: La requête a pris trop de temps ({elapsed_time:.2f}s)")
            return []
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"⚠️  Exception: {str(e)[:100]}... (temps: {elapsed_time:.2f}s)")
            return []
    
    def fetch_real_internal_transactions(self, limit=5000, token_contract_address=None):
        """Récupère les transactions internes réelles"""
        start_time = time.time()
        
        if token_contract_address:
            print(f"\n🔍 Récupération des transactions internes pour le token {token_contract_address[:20]}...")
        else:
            print("\n🔍 Récupération des transactions internes réelles...")
        
        # Construire la requête selon si un token est spécifié
        if token_contract_address:
            query = """
            {
              ethereum(network: ethereum) {
                smartContractCalls(
                  options: {limit: %s, desc: "block.timestamp.time"}
                  date: {since: "2024-12-01"}
                  smartContractAddress: {is: "%s"}
                ) {
                  block {
                    timestamp { time(format: "%%Y-%%m-%%d %%H:%%M:%%S") }
                  }
                  sender { address }
                  receiver { address }
                  value
                  smartContractMethod { name }
                  smartContract { address }
                }
              }
            }
            """ % (limit, token_contract_address)
        else:
            # Essayer de récupérer les transactions internes pour les adresses trouvées
            if not self.transactions_cache:
                print("⚠️  Aucune transaction disponible pour rechercher des internals")
                return []
            
            # Extraire les adresses uniques
            all_addresses = set()
            for tx in self.transactions_cache:
                all_addresses.add(tx['sender']['address'])
                all_addresses.add(tx['receiver']['address'])
            
            # Prendre les 10 premières adresses pour la requête
            sample_addresses = list(all_addresses)[:10]
            
            query = """
            {
              ethereum(network: ethereum) {
                smartContractCalls(
                  options: {limit: %s, desc: "block.timestamp.time"}
                  date: {since: "2025-01-01"}
                  smartContractAddress: {in: %s}
                ) {
                  block {
                    timestamp { time(format: "%%Y-%%m-%%d %%H:%%M:%%S") }
                  }
                  sender { address }
                  receiver { address }
                  value
                  smartContractMethod { name }
                  smartContract { address }
                }
              }
            }
            """ % (limit, json.dumps(sample_addresses))
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                "https://graphql.bitquery.io",
                json={"query": query},
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    # Si erreur, essayer une requête plus simple
                    print(f"⚠️  Erreur pour internals: {data['errors'][0]['message'][:100]}...")
                    return self.fetch_generic_internal_transactions(limit, token_contract_address)
                
                calls = data.get("data", {}).get("ethereum", {}).get("smartContractCalls", [])
                
                if calls:
                    elapsed_time = time.time() - start_time
                    print(f"✅ {len(calls)} transactions internes réelles récupérées")
                    print(f"   ⏱️  Temps de fetch: {elapsed_time:.2f}s")
                    
                    # Convertir au même format
                    internal_txs = []
                    for call in calls:
                        internal_txs.append({
                            'sender': {'address': call['sender']['address']},
                            'receiver': {'address': call['receiver']['address']},
                            'value': call.get('value', '0'),
                            'smartContract': {'address': call.get('smartContract', {}).get('address')},
                            'smartContractMethod': {'name': call.get('smartContractMethod', {}).get('name', 'unknown')}
                        })
                    
                    return internal_txs
                else:
                    print("⚠️  Aucune transaction interne trouvée")
                    return []
            else:
                print(f"⚠️  Erreur HTTP {response.status_code} pour internals")
                return []
                
        except Exception as e:
            print(f"⚠️  Exception pour internals: {str(e)[:100]}...")
            return []
    
    def fetch_generic_internal_transactions(self, limit=500, token_contract_address=None):
        """Récupère des transactions internes génériques"""
        print("   Tentative avec requête générique...")
        
        if token_contract_address:
            # Requête spécifique au token
            query = """
            {
              ethereum(network: ethereum) {
                smartContractCalls(
                  options: {limit: %s, desc: "block.timestamp.time"}
                  date: {since: "2024-12-01"}
                  smartContractAddress: {is: "%s"}
                  external: false
                ) {
                  block {
                    timestamp { time(format: "%%Y-%%m-%%d %%H:%%M:%%S") }
                  }
                  sender { address }
                  receiver { address }
                  value
                  smartContractMethod { name }
                  smartContract { address }
                }
              }
            }
            """ % (limit, token_contract_address)
        else:
            # Requête générique
            query = """
            {
              ethereum(network: ethereum) {
                smartContractCalls(
                  options: {limit: %s, desc: "block.timestamp.time"}
                  date: {since: "2025-01-01"}
                  external: false
                ) {
                  block {
                    timestamp { time(format: "%%Y-%%m-%%d %%H:%%M:%%S") }
                  }
                  sender { address }
                  receiver { address }
                  value
                  smartContractMethod { name }
                  smartContract { address }
                }
              }
            }
            """ % limit
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                "https://graphql.bitquery.io",
                json={"query": query},
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                calls = data.get("data", {}).get("ethereum", {}).get("smartContractCalls", [])
                
                if calls:
                    print(f"   ✅ {len(calls)} transactions internes génériques récupérées")
                    
                    internal_txs = []
                    for call in calls:
                        internal_txs.append({
                            'sender': {'address': call['sender']['address']},
                            'receiver': {'address': call['receiver']['address']},
                            'value': call.get('value', '0'),
                            'smartContract': {'address': call.get('smartContract', {}).get('address')},
                            'smartContractMethod': {'name': call.get('smartContractMethod', {}).get('name', 'unknown')}
                        })
                    
                    return internal_txs
                else:
                    return []
            else:
                return []
                
        except:
            return []
    
    def fetch_real_token_holders(self, token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7", limit=50):
        """Récupère les vrais holders de tokens"""
        start_time = time.time()
        print(f"\n🏦 Récupération des holders réels pour {token_address[:20]}...")
        
        query = """
        {
          ethereum(network: ethereum) {
            transfers(
              currency: {is: "%s"}
              options: {desc: "amount", limit: %s}
              date: {since: "2024-12-01"}
            ) {
              receiver {
                address
              }
              amount
            }
          }
        }
        """ % (token_address, limit)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                "https://graphql.bitquery.io",
                json={"query": query},
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print(f"⚠️  Erreur pour holders: {data['errors'][0]['message'][:100]}...")
                    return {}
                
                transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
                
                if transfers:
                    holders = {}
                    for transfer in transfers:
                        receiver = transfer.get('receiver', {}).get('address')
                        amount = float(transfer.get('amount', 0))
                        
                        if receiver and amount > 0:
                            holders[receiver] = holders.get(receiver, 0) + amount
                    
                    if holders:
                        elapsed_time = time.time() - start_time
                        print(f"✅ {len(holders)} holders réels récupérés")
                        print(f"   ⏱️  Temps de fetch: {elapsed_time:.2f}s")
                        
                        # Afficher le top 3
                        top_3 = sorted(holders.items(), key=lambda x: x[1], reverse=True)[:3]
                        print(f"   • Top 3: {', '.join([f'{addr[:10]}... ({bal:,.0f})' for addr, bal in top_3])}")
                        
                        return holders
                    else:
                        print("⚠️  Aucun holder trouvé")
                        return {}
                else:
                    print("⚠️  Aucun transfert trouvé pour ce token")
                    return {}
            else:
                print(f"⚠️  Erreur HTTP {response.status_code} pour holders")
                return {}
                
        except Exception as e:
            print(f"⚠️  Exception pour holders: {str(e)[:100]}...")
            return {}
    
    def build_graph_from_real_data(self, transactions, internal_transactions=None):
        """Construit le graphe avec les données réelles"""
        print("\n🏗️ Construction du graphe avec données réelles...")
        
        # Traiter les transactions normales
        normal_edges = set()
        for tx in transactions:
            sender = tx.get('sender', {}).get('address')
            receiver = tx.get('receiver', {}).get('address')
            amount = float(tx.get('amount', 0))
            
            if not sender or not receiver:
                continue
            
            # Ajouter les annotations si disponibles
            sender_annotation = tx.get('sender', {}).get('annotation', '')
            receiver_annotation = tx.get('receiver', {}).get('annotation', '')
            
            # Ajouter les nœuds avec propriétés
            self.G.add_node(sender, 
                           type='wallet',
                           annotation=sender_annotation,
                           initial_amount=amount if sender not in self.G.nodes() else self.G.nodes[sender].get('initial_amount', 0))
            
            self.G.add_node(receiver, 
                           type='wallet',
                           annotation=receiver_annotation,
                           initial_amount=amount if receiver not in self.G.nodes() else self.G.nodes[receiver].get('initial_amount', 0))
            
            edge_key = (sender, receiver)
            if edge_key in normal_edges:
                # Mettre à jour l'arête existante
                if self.G.has_edge(sender, receiver):
                    self.G[sender][receiver]['weight'] += 1
                    self.G[sender][receiver]['total_amount'] += amount
                    self.G[sender][receiver]['tx_count'] += 1
            else:
                # Créer nouvelle arête
                self.G.add_edge(sender, receiver, 
                               weight=1,
                               total_amount=amount,
                               tx_count=1,
                               avg_amount=amount,
                               currency=tx.get('currency', {}).get('symbol', 'ETH'),
                               tx_hash=tx.get('transaction', {}).get('hash', ''))
                normal_edges.add(edge_key)
        
        print(f"   • Transactions normales: {len(normal_edges)} arêtes uniques")
        
        # Traiter les transactions internes si disponibles
        if internal_transactions:
            internal_edges = set()
            for tx in internal_transactions:
                sender = tx.get('sender', {}).get('address')
                receiver = tx.get('receiver', {}).get('address')
                value = float(tx.get('value', 0))
                
                if not sender or not receiver or value <= 0:
                    continue
                
                # Identifier les contrats
                is_contract = tx.get('smartContract') is not None
                sender_type = 'contract' if is_contract else 'wallet'
                
                self.internal_G.add_node(sender, type=sender_type)
                self.internal_G.add_node(receiver, type='wallet')
                
                edge_key = (sender, receiver)
                if edge_key in internal_edges:
                    if self.internal_G.has_edge(sender, receiver):
                        self.internal_G[sender][receiver]['weight'] += 1
                        self.internal_G[sender][receiver]['total_amount'] += value
                        self.internal_G[sender][receiver]['tx_count'] += 1
                else:
                    self.internal_G.add_edge(sender, receiver,
                                           weight=1,
                                           total_amount=value,
                                           tx_count=1,
                                           method=tx.get('smartContractMethod', {}).get('name', 'unknown'),
                                           contract_address=tx.get('smartContract', {}).get('address', ''))
                    internal_edges.add(edge_key)
            
            print(f"   • Transactions internes: {len(internal_edges)} arêtes uniques")
        
        # Combiner les graphes
        self.combined_G = nx.compose(self.G, self.internal_G)
        
        # Mettre à jour les compteurs pour les arêtes qui existent dans les deux
        for u, v in self.combined_G.edges():
            weight = 0
            total_amount = 0
            tx_count = 0
            
            if self.G.has_edge(u, v):
                weight += self.G[u][v].get('weight', 0)
                total_amount += self.G[u][v].get('total_amount', 0)
                tx_count += self.G[u][v].get('tx_count', 0)
            
            if self.internal_G.has_edge(u, v):
                weight += self.internal_G[u][v].get('weight', 0)
                total_amount += self.internal_G[u][v].get('total_amount', 0)
                tx_count += self.internal_G[u][v].get('tx_count', 0)
            
            self.combined_G[u][v]['combined_weight'] = weight
            self.combined_G[u][v]['combined_total'] = total_amount
            self.combined_G[u][v]['combined_count'] = tx_count
        
        print(f"\n📊 STATISTIQUES DU GRAPHE RÉEL:")
        print(f"   • Nœuds uniques: {self.combined_G.number_of_nodes()}")
        print(f"   • Arêtes uniques: {self.combined_G.number_of_edges()}")
        print(f"   • Contrats identifiés: {sum(1 for _, d in self.combined_G.nodes(data=True) if d.get('type') == 'contract')}")
        
        # Calculer quelques métriques
        if self.combined_G.number_of_nodes() > 0:
            degrees = [deg for _, deg in self.combined_G.degree()]
            avg_degree = sum(degrees) / len(degrees)
            max_degree = max(degrees) if degrees else 0
            
            print(f"   • Degré moyen: {avg_degree:.2f}")
            print(f"   • Degré max: {max_degree}")
            
            # Identifier les hubs
            hubs = [(node, deg) for node, deg in self.combined_G.degree() if deg >= 5]
            if hubs:
                print(f"   • Hubs (≥5 connexions): {len(hubs)}")
        
        return self.combined_G
    
    # ==================== MÉTHODES DE DÉTECTION AVANCÉES ====================
    
    def detect_funding_patterns(self):
        """Détecte les patterns de financement suspects"""
        print("\n💰 Détection des patterns de financement suspects...")
        
        funding_patterns = []
        
        # 1. Détection de financement en étoile (star funding)
        for node in self.combined_G.nodes():
            out_degree = self.combined_G.out_degree(node)
            
            if out_degree >= 3:  # Au moins 3 sorties
                receivers = list(self.combined_G.successors(node))
                
                # Analyser les montants
                amounts = []
                total_sent = 0
                for receiver in receivers:
                    if self.combined_G.has_edge(node, receiver):
                        amount = self.combined_G[node][receiver].get('total_amount', 0)
                        amounts.append(amount)
                        total_sent += amount
                
                if amounts:
                    avg_amount = total_sent / len(amounts)
                    std_amount = (sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)) ** 0.5
                    
                    # Coefficient de variation (faible = montants similaires)
                    cv = std_amount / avg_amount if avg_amount > 0 else 1
                    
                    # Pattern suspect: beaucoup de sorties avec montants similaires
                    if cv < 0.3 and out_degree >= 3:
                        funding_patterns.append({
                            'type': 'star_funding',
                            'source': node,
                            'receivers': receivers,
                            'count': out_degree,
                            'total_sent': total_sent,
                            'avg_amount': avg_amount,
                            'cv': cv,
                            'is_uniform': cv < 0.2
                        })
        
        # 2. Détection de financement en cascade
        cascade_patterns = self._detect_cascade_funding()
        funding_patterns.extend(cascade_patterns)
        
        print(f"✅ {len(funding_patterns)} patterns de financement détectés")
        return funding_patterns
    
    def _detect_cascade_funding(self):
        """Détecte les financements en cascade (A→B→C→D)"""
        cascade_patterns = []
        
        # Chercher des chemins de longueur 2-4
        for source in self.combined_G.nodes():
            for target in self.combined_G.nodes():
                if source != target:
                    # Chercher tous les chemins simples entre source et target
                    try:
                        paths = list(nx.all_simple_paths(self.combined_G, source, target, cutoff=4))
                        
                        for path in paths:
                            if 3 <= len(path) <= 5:  # Chemins de 3 à 5 nœuds
                                # Vérifier que chaque étape a un montant significatif
                                amounts = []
                                for i in range(len(path)-1):
                                    if self.combined_G.has_edge(path[i], path[i+1]):
                                        amounts.append(self.combined_G[path[i]][path[i+1]].get('total_amount', 0))
                                
                                if len(amounts) == len(path)-1 and all(a > 0 for a in amounts):
                                    cascade_patterns.append({
                                        'type': 'cascade_funding',
                                        'path': path,
                                        'length': len(path),
                                        'total_amount': sum(amounts),
                                        'avg_per_step': sum(amounts) / len(amounts)
                                    })
                    except:
                        continue
        
        return cascade_patterns
    
    def detect_wash_trading_patterns(self):
        """Détecte les patterns de wash trading"""
        print("\n🔄 Détection des patterns de wash trading...")
        
        wash_patterns = []
        
        # 1. Cycles courts (3-5 nœuds)
        try:
            cycles = list(nx.simple_cycles(self.combined_G))
            
            for cycle in cycles:
                if 3 <= len(cycle) <= 5:
                    # Calculer les volumes
                    volumes = []
                    for i in range(len(cycle)):
                        sender = cycle[i]
                        receiver = cycle[(i + 1) % len(cycle)]
                        
                        if self.combined_G.has_edge(sender, receiver):
                            volumes.append(self.combined_G[sender][receiver].get('total_amount', 0))
                    
                    if len(volumes) == len(cycle):
                        total_volume = sum(volumes)
                        
                        wash_patterns.append({
                            'type': 'circular_trading',
                            'cycle': cycle,
                            'length': len(cycle),
                            'total_volume': total_volume,
                            'avg_volume': total_volume / len(volumes)
                        })
        except Exception as e:
            print(f"   ⚠️  Erreur détection cycles: {e}")
        
        # 2. Paires de trading réciproques
        reciprocal_pairs = []
        for u, v in self.combined_G.edges():
            if self.combined_G.has_edge(v, u):
                vol_u_to_v = self.combined_G[u][v].get('total_amount', 0)
                vol_v_to_u = self.combined_G[v][u].get('total_amount', 0)
                
                if vol_u_to_v > 0 and vol_v_to_u > 0:
                    ratio = min(vol_u_to_v, vol_v_to_u) / max(vol_u_to_v, vol_v_to_u)
                    
                    if ratio > 0.8:  # Volumes similaires
                        reciprocal_pairs.append({
                            'pair': [u, v],
                            'volume_AB': vol_u_to_v,
                            'volume_BA': vol_v_to_u,
                            'similarity_ratio': ratio
                        })
        
        if reciprocal_pairs:
            wash_patterns.extend([{
                'type': 'reciprocal_trading',
                **pair
            } for pair in reciprocal_pairs])
        
        print(f"✅ {len(wash_patterns)} patterns de wash trading détectés")
        return wash_patterns
    
    
    
    def detect_mixer_patterns(self):
        """Détecte les patterns de mixers (tumblers)"""
        print("\n🌀 Détection des patterns de mixers...")
        
        mixer_patterns = []
        
        # Chercher les nœuds avec beaucoup de connexions entrantes et sortantes
        for node in self.combined_G.nodes():
            in_degree = self.combined_G.in_degree(node)
            out_degree = self.combined_G.out_degree(node)
            
            # Pattern de mixer: beaucoup d'entrées et sorties, montants similaires
            if in_degree >= 3 and out_degree >= 3:
                # Analyser les montants entrants
                in_amounts = []
                total_in = 0
                for pred in self.combined_G.predecessors(node):
                    if self.combined_G.has_edge(pred, node):
                        amount = self.combined_G[pred][node].get('total_amount', 0)
                        in_amounts.append(amount)
                        total_in += amount
                
                # Analyser les montants sortants
                out_amounts = []
                total_out = 0
                for succ in self.combined_G.successors(node):
                    if self.combined_G.has_edge(node, succ):
                        amount = self.combined_G[node][succ].get('total_amount', 0)
                        out_amounts.append(amount)
                        total_out += amount
                
                if in_amounts and out_amounts:
                    avg_in = total_in / len(in_amounts)
                    avg_out = total_out / len(out_amounts)
                    
                    # Écart entre entrées et sorties (mixer conserve souvent des frais)
                    volume_ratio = total_out / total_in if total_in > 0 else 0
                    
                    if 0.9 <= volume_ratio <= 1.1:  # Peu de perte
                        mixer_patterns.append({
                            'type': 'mixer_suspected',
                            'node': node,
                            'in_degree': in_degree,
                            'out_degree': out_degree,
                            'total_in': total_in,
                            'total_out': total_out,
                            'volume_ratio': volume_ratio,
                            'avg_in': avg_in,
                            'avg_out': avg_out
                        })
        
        print(f"✅ {len(mixer_patterns)} patterns de mixers détectés")
        return mixer_patterns
    
    def detect_ponzi_patterns(self):
        """Détecte les patterns de schémas Ponzi"""
        print("\n📊 Détection des patterns de schémas Ponzi...")
        
        ponzi_patterns = []
        
        # Chercher les structures pyramidales
        for node in self.combined_G.nodes():
            # Ratio entrées/sorties
            total_in = sum(self.combined_G[pred][node].get('total_amount', 0) 
                          for pred in self.combined_G.predecessors(node) 
                          if self.combined_G.has_edge(pred, node))
            
            total_out = sum(self.combined_G[node][succ].get('total_amount', 0) 
                           for succ in self.combined_G.successors(node) 
                           if self.combined_G.has_edge(node, succ))
            
            if total_in > 0 and total_out > 0:
                # Dans un Ponzi, les sorties sont souvent > entrées (redistribution)
                redistribution_ratio = total_out / total_in
                
                # Beaucoup de petits entrants, quelques gros sortants
                in_count = self.combined_G.in_degree(node)
                out_count = self.combined_G.out_degree(node)
                
                if redistribution_ratio > 1.5 and in_count > out_count * 2:
                    ponzi_patterns.append({
                        'type': 'ponzi_suspected',
                        'node': node,
                        'total_in': total_in,
                        'total_out': total_out,
                        'redistribution_ratio': redistribution_ratio,
                        'in_count': in_count,
                        'out_count': out_count
                    })
        
        print(f"✅ {len(ponzi_patterns)} patterns Ponzi détectés")
        return ponzi_patterns
    
    # ==================== MÉTHODES EXISTANTES AMÉLIORÉES ====================
    
    def detect_all_clusters_real(self):
        """Détecte tous les types de clusters avec données réelles"""
        print("\n🎯 DÉTECTION DE CLUSTERS SUR DONNÉES RÉELLES")
        print("=" * 50)
        
        all_clusters = []
        
        # Détections de base
        print("\n1. Clusters de source commune...")
        source_clusters = self.detect_common_source_clusters_real()
        all_clusters.extend(source_clusters)
        
        print("\n2. Clusters fortement connectés...")
        connected_clusters = self.detect_highly_connected_clusters_real()
        all_clusters.extend(connected_clusters)
        
        print("\n3. Clusters par montant...")
        amount_clusters = self.detect_amount_based_clusters_real()
        all_clusters.extend(amount_clusters)
        
        # Détections avancées
        # print("\n4. Patterns de financement suspects...")
        # funding_patterns = self.detect_funding_patterns()
        # all_clusters.extend(funding_patterns)
        
        print("\n5. Patterns de wash trading...")
        wash_patterns = self.detect_wash_trading_patterns()
        all_clusters.extend(wash_patterns)
        
        # print("\n6. Patterns de mixers...")
        # mixer_patterns = self.detect_mixer_patterns()
        # all_clusters.extend(mixer_patterns)
        
        # print("\n7. Patterns Ponzi...")
        # ponzi_patterns = self.detect_ponzi_patterns()
        # all_clusters.extend(ponzi_patterns)
        
        print("\n8. Clusters avec whales...")
        whale_clusters = self.detect_clusters_with_whales()
        all_clusters.extend(whale_clusters)
        
        print(f"\n✅ Total: {len(all_clusters)} clusters et patterns détectés")
        
        return all_clusters
    
    def detect_common_source_clusters_real(self):
        """Version améliorée pour données réelles"""
        wallet_sources = defaultdict(set)
        wallet_amounts = defaultdict(float)
        
        for sender, receiver, data in self.combined_G.edges(data=True):
            amount = data.get('total_amount', data.get('combined_total', 0))
            wallet_sources[receiver].add(sender)
            wallet_amounts[receiver] += amount
        
        source_to_wallets = defaultdict(list)
        for wallet, sources in wallet_sources.items():
            if sources:
                source_key = frozenset(sources)
                source_to_wallets[source_key].append({
                    'address': wallet,
                    'amount_received': wallet_amounts[wallet]
                })
        
        clusters = []
        for sources, wallets in source_to_wallets.items():
            if len(wallets) >= 3:
                total_received = sum(w['amount_received'] for w in wallets)
                
                clusters.append({
                    'type': 'common_source',
                    'funding_sources': list(sources),
                    'wallets': [w['address'] for w in wallets],
                    'wallet_details': wallets,
                    'size': len(wallets),
                    'source_count': len(sources),
                    'total_received': total_received,
                    'avg_received': total_received / len(wallets)
                })
        
        return clusters
    
    def detect_highly_connected_clusters_real(self, min_size=3):
        """Détection de communautés sur données réelles"""
        if self.combined_G.number_of_nodes() < min_size:
            return []
        
        try:
            if nx.is_directed(self.combined_G):
                G_undirected = self.combined_G.to_undirected()
            else:
                G_undirected = self.combined_G.copy()
            
            partition = community_louvain.best_partition(G_undirected)
            
            communities = defaultdict(list)
            for node, comm_id in partition.items():
                communities[comm_id].append(node)
            
            clusters = []
            for comm_id, nodes in communities.items():
                if len(nodes) >= min_size:
                    subgraph = G_undirected.subgraph(nodes)
                    
                    density = nx.density(subgraph)
                    degrees = [deg for _, deg in subgraph.degree()]
                    avg_degree = sum(degrees) / len(degrees) if degrees else 0
                    
                    # Calculer le volume interne
                    internal_volume = 0
                    for u, v, data in subgraph.edges(data=True):
                        internal_volume += data.get('total_amount', data.get('combined_total', 0))
                    
                    clusters.append({
                        'type': 'highly_connected',
                        'community_id': comm_id,
                        'wallets': nodes,
                        'size': len(nodes),
                        'density': density,
                        'avg_degree': avg_degree,
                        'internal_edges': subgraph.number_of_edges(),
                        'internal_volume': internal_volume
                    })
            
            return clusters
            
        except Exception as e:
            print(f"   ⚠️  Erreur Louvain: {e}")
            return []
    
    def detect_amount_based_clusters_real(self, amount_tolerance=0.2):
        """Clusters par montant sur données réelles"""
        edge_amounts = []
        
        for _, _, data in self.combined_G.edges(data=True):
            amount = data.get('total_amount', data.get('combined_total', 0))
            if amount > 0:
                edge_amounts.append(amount)
        
        if len(edge_amounts) < 3:
            return []
        
        # Regrouper par plages de montants
        amount_groups = defaultdict(list)
        
        for sender, receiver, data in self.combined_G.edges(data=True):
            amount = data.get('total_amount', data.get('combined_total', 0))
            if amount > 0:
                # Arrondir à l'ordre de magnitude
                if amount >= 1000:
                    key = round(amount, -3)  # Arrondir au millier
                elif amount >= 100:
                    key = round(amount, -2)  # Arrondir à la centaine
                elif amount >= 10:
                    key = round(amount, -1)  # Arrondir à la dizaine
                else:
                    key = round(amount, 1)   # Arrondir au dixième
                
                amount_groups[key].append({
                    'from': sender,
                    'to': receiver,
                    'amount': amount
                })
        
        clusters = []
        for amount_key, edges in amount_groups.items():
            if len(edges) >= 3:
                all_wallets = set()
                total_amount = 0
                
                for edge in edges:
                    all_wallets.add(edge['from'])
                    all_wallets.add(edge['to'])
                    total_amount += edge['amount']
                
                clusters.append({
                    'type': 'amount_based',
                    'amount_range': amount_key,
                    'wallets': list(all_wallets),
                    'size': len(all_wallets),
                    'transaction_count': len(edges),
                    'total_amount': total_amount,
                    'avg_amount': total_amount / len(edges)
                })
        
        return clusters
    
    def detect_clusters_with_whales(self):
        """Détecte les clusters contenant des whales"""
        if not self.token_holders:
            return []
        
        # Trier les holders
        sorted_holders = sorted(self.token_holders.items(), key=lambda x: x[1], reverse=True)
        top_n = min(20, len(sorted_holders))
        top_holders = {addr: balance for addr, balance in sorted_holders[:top_n]}
        
        # Détecter les clusters de base
        base_clusters = []
        base_clusters.extend(self.detect_common_source_clusters_real())
        base_clusters.extend(self.detect_highly_connected_clusters_real())
        base_clusters.extend(self.detect_amount_based_clusters_real())
        
        whale_clusters = []
        for cluster in base_clusters:
            wallets = cluster.get('wallets', [])
            
            # Vérifier la présence de whales
            whale_in_cluster = [addr for addr in wallets if addr in top_holders]
            
            if whale_in_cluster:
                # Calculer la richesse totale
                cluster_wealth = sum(self.token_holders.get(addr, 0) for addr in wallets if addr in self.token_holders)
                
                whale_clusters.append({
                    **cluster,
                    'whale_count': len(whale_in_cluster),
                    'whale_addresses': whale_in_cluster,
                    'cluster_wealth': cluster_wealth,
                    'type': cluster.get('type', 'unknown') + '_with_whales'
                })
        
        return whale_clusters
    
    def calculate_advanced_risk_metrics(self, clusters):
        """Calcule des métriques de risque avancées"""
        print("\n📊 Calcul des métriques de risque avancées...")
        
        for cluster in clusters:
            cluster_type = cluster.get('type', '')
            
            # Score basé sur le type
            type_weights = {
                'circular_trading': 0.95,
                'ponzi_suspected': 0.90,
                'mixer_suspected': 0.85,
                'star_funding': 0.80,
                'common_source_with_whales': 0.75,
                'common_source': 0.65,
                'highly_connected_with_whales': 0.70,
                'highly_connected': 0.60,
                'amount_based_with_whales': 0.55,
                'amount_based': 0.45,
                'cascade_funding': 0.50,
                'reciprocal_trading': 0.75
            }
            
            base_score = type_weights.get(cluster_type, 0.3)
            
            # Score basé sur la taille
            size = cluster.get('size', 0)
            size_score = min(size / 10, 1.0)
            
            # Score basé sur le volume
            volume = cluster.get('total_amount', 
                               cluster.get('total_volume', 
                                         cluster.get('total_received', 
                                                   cluster.get('total_in', 0))))
            if volume > 0:
                volume_score = min(volume / 1000, 1.0)  # Normaliser sur 1000 ETH
            else:
                volume_score = 0
            
            # Score basé sur les whales
            whale_score = cluster.get('whale_count', 0) / 5 if 'whale_count' in cluster else 0
            whale_score = min(whale_score, 1.0)
            
            # Score basé sur l'uniformité (pour les patterns de financement)
            uniformity_score = 0
            if 'cv' in cluster and cluster['cv'] < 0.3:
                uniformity_score = 0.8
            if 'is_uniform' in cluster and cluster['is_uniform']:
                uniformity_score = 0.9
            if 'similarity_ratio' in cluster and cluster['similarity_ratio'] > 0.8:
                uniformity_score = 0.7
            
            # Calcul du score composite
            risk_score = (
                base_score * 0.35 +
                size_score * 0.20 +
                volume_score * 0.20 +
                whale_score * 0.15 +
                uniformity_score * 0.10
            )
            
            # Ajustements
            if cluster_type in ['circular_trading', 'ponzi_suspected', 'mixer_suspected']:
                risk_score *= 1.1
            
            # Limiter à 1.0
            risk_score = min(risk_score, 1.0)
            
            # Déterminer le niveau de risque
            if risk_score >= 0.75:
                risk_level = 'CRITICAL'
            elif risk_score >= 0.60:
                risk_level = 'HIGH'
            elif risk_score >= 0.40:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            cluster['risk_score'] = round(risk_score, 3)
            cluster['risk_level'] = risk_level
        
        return clusters
    
    def generate_real_data_report(self, clusters):
        """Génère un rapport pour les données réelles"""
        print("\n" + "=" * 70)
        print("📋 RAPPORT FORENSIC - DONNÉES RÉELLES")
        print("=" * 70)
        
        if not clusters:
            print("\n❌ Aucun cluster ou pattern suspect détecté")
            return
        
        total = len(clusters)
        
        # Compter par type
        from collections import Counter
        type_counter = Counter([c.get('type', 'unknown') for c in clusters])
        
        print(f"\n📈 RÉSUMÉ GÉNÉRAL:")
        print(f"   • Total détections: {total}")
        print(f"   • Types uniques: {len(type_counter)}")
        
        # Risques par niveau
        risk_levels = defaultdict(int)
        for c in clusters:
            risk_levels[c.get('risk_level', 'UNKNOWN')] += 1
        
        print(f"\n⚠️  NIVEAUX DE RISQUE:")
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
            count = risk_levels.get(level, 0)
            if count > 0:
                percentage = (count / total) * 100
                print(f"   • {level:9s}: {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n🔍 DISTRIBUTION PAR TYPE:")
        for type_name, count in type_counter.most_common():
            print(f"   • {type_name:25s}: {count:3d}")
        
        # Top 10 des détections les plus critiques
        critical_clusters = [c for c in clusters if c.get('risk_level') in ['CRITICAL', 'HIGH']]
        
        if critical_clusters:
            print(f"\n🚨 TOP 10 DÉTECTIONS CRITIQUES:")
            top_clusters = sorted(critical_clusters, key=lambda x: x.get('risk_score', 0), reverse=True)[:10]
            
            for i, cluster in enumerate(top_clusters, 1):
                print(f"\n   {i}. {cluster.get('type', 'N/A')}")
                print(f"      Score: {cluster.get('risk_score', 0):.3f} | Niveau: {cluster.get('risk_level', 'N/A')}")
                
                # Informations spécifiques
                if 'size' in cluster:
                    print(f"      Taille: {cluster['size']} wallets")
                
                if 'source' in cluster:
                    print(f"      Source: {cluster['source'][:20]}...")
                
                if 'total_amount' in cluster:
                    print(f"      Volume: {cluster['total_amount']:.2f} ETH")
                
                if 'whale_count' in cluster and cluster['whale_count'] > 0:
                    print(f"      🐋 Whales: {cluster['whale_count']}")
                
                # Afficher quelques adresses
                wallets = cluster.get('wallets', [])
                if not wallets and 'receivers' in cluster:
                    wallets = cluster['receivers']
                
                if wallets and len(wallets) > 0:
                    sample = wallets[:2]
                    print(f"      Exemples: {', '.join([w[:12] + '...' for w in sample])}")
                    if len(wallets) > 2:
                        print(f"      (+ {len(wallets) - 2} autres)")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if any(c.get('type') == 'mixer_suspected' for c in clusters):
            print("   • ⚠️  Mixers détectés: Surveiller les transactions de blanchiment")
        
        if any(c.get('type') == 'ponzi_suspected' for c in clusters):
            print("   • ⚠️  Patterns Ponzi: Investigation approfondie requise")
        
        if any(c.get('type') == 'circular_trading' for c in clusters):
            print("   • ⚠️  Wash trading: Possible manipulation de marché")
        
        if any('whale' in c.get('type', '') for c in clusters):
            print("   • 🐋 Whales impliqués: Surveiller l'impact sur le marché")
        
        print(f"\n{'='*70}")
        print("✅ Analyse forensic complète")
        print(f"{'='*70}")
    
    def export_results(self, clusters, filename_prefix="forensic_real"):
        """Exporte les résultats des données réelles"""
        if not clusters:
            print("⚠️  Aucun résultat à exporter")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(clusters, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 Données exportées: {json_filename}")
        except Exception as e:
            print(f"⚠️  Erreur export JSON: {e}")
        
        # Export CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'type', 'risk_level', 'risk_score', 'size',
                    'whale_count', 'total_amount', 'description'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for cluster in clusters:
                    row = {
                        'type': cluster.get('type', ''),
                        'risk_level': cluster.get('risk_level', ''),
                        'risk_score': cluster.get('risk_score', 0),
                        'size': cluster.get('size', 0),
                        'whale_count': cluster.get('whale_count', 0),
                        'total_amount': cluster.get('total_amount', 
                                                  cluster.get('total_volume', 
                                                            cluster.get('total_received', 0))),
                        'description': self._get_cluster_description(cluster)
                    }
                    writer.writerow(row)
            
            print(f"📊 Résumé exporté: {csv_filename}")
            
        except Exception as e:
            print(f"⚠️  Erreur export CSV: {e}")
    
    def _get_cluster_description(self, cluster):
        """Génère une description pour l'export"""
        desc_parts = []
        
        if 'size' in cluster:
            desc_parts.append(f"{cluster['size']} wallets")
        
        if 'source' in cluster:
            desc_parts.append(f"source: {cluster['source'][:10]}...")
        
        if 'total_amount' in cluster:
            desc_parts.append(f"{cluster['total_amount']:.2f} ETH")
        
        if 'whale_count' in cluster and cluster['whale_count'] > 0:
            desc_parts.append(f"{cluster['whale_count']} whales")
        
        return " | ".join(desc_parts)


def main_real_data(token_contract_address=None):
    """Fonction principale pour l'analyse avec données réelles"""
    BITQUERY_API_KEY = ""
    
    print("\n" + "=" * 70)
    if token_contract_address:
        print(f"🔍 FORENSIC GRAPH AGENT - TOKEN ANALYSIS: {token_contract_address[:30]}...")
    else:
        print("🔍 FORENSIC GRAPH AGENT - DONNÉES RÉELLES")
    print("=" * 70)
    
    # 1. Initialiser l'agent
    agent = ForensicGraphAgent(BITQUERY_API_KEY)
    
    # 2. Récupérer les transactions réelles
    print("\n📥 TÉLÉCHARGEMENT DES DONNÉES RÉELLES...")
    
    if token_contract_address:
        # Analyse d'un token spécifique
        all_transactions = agent.fetch_real_transactions(
            days_back=1, 
            limit=5000, 
            token_contract_address=token_contract_address
        )
        
        if all_transactions:
            agent.transactions_cache = all_transactions
            
            # Récupérer les transactions internes pour ce token
            internal_txs = agent.fetch_real_internal_transactions(
                limit=500, 
                token_contract_address=token_contract_address
            )
            
            # Récupérer les holders de ce token
            token_holders = agent.fetch_real_token_holders(
                token_address=token_contract_address, 
                limit=50
            )
            agent.token_holders = token_holders
        else:
            print("❌ Aucune donnée trouvée pour ce token")
            return []
    else:
        # Analyse générique (ETH et tokens principaux)
        currencies = ["ETH", "USDT", "USDC", "DAI"]
        all_transactions = []
        
        for currency in currencies[:2]:  # Essayer les 2 premières
            transactions = agent.fetch_real_transactions(days_back=1, limit=5000, currency=currency)
            if transactions:
                all_transactions.extend(transactions)
                print(f"   ✅ Ajouté {len(transactions)} transactions {currency}")
                break  # S'arrêter après la première devise avec des données
        
        if not all_transactions:
            print("❌ Aucune donnée réelle récupérée")
            return []
        
        agent.transactions_cache = all_transactions
        
        # Récupérer les transactions internes
        internal_txs = agent.fetch_real_internal_transactions(limit=500)
        
        # Récupérer les token holders pour USDT par défaut
        token_holders = agent.fetch_real_token_holders(limit=50)
        agent.token_holders = token_holders
    
    if not all_transactions:
        return []
    
    # 5. Construire le graphe
    agent.build_graph_from_real_data(all_transactions, internal_txs)
    
    # 6. Détection complète
    print("\n" + "=" * 70)
    print("🔎 ANALYSE FORENSIC COMPLÈTE")
    print("=" * 70)
    
    all_clusters = agent.detect_all_clusters_real()
    
    # 7. Calcul des métriques
    if all_clusters:
        all_clusters = agent.calculate_advanced_risk_metrics(all_clusters)
        
        # 8. Générer le rapport
        agent.generate_real_data_report(all_clusters)
        
        # 9. Exporter les résultats
        if token_contract_address:
            filename_prefix = f"forensic_token_{token_contract_address[:10]}"
        else:
            filename_prefix = "forensic_real"
            
        agent.export_results(all_clusters, filename_prefix)
        
        return all_clusters
    else:
        print("\n⚠️  Aucune détection sur les données réelles")
        return []


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Forensic Graph Agent - Analyse de données blockchain')
    parser.add_argument('--token', type=str, help='Adresse du token contract à analyser')
    parser.add_argument('--days', type=int, default=1, help='Nombre de jours en arrière (défaut: 7)')
    parser.add_argument('--limit', type=int, default=5000, help='Limite de transactions (défaut: 5000)')
    
    # args = parser.parse_args()
    
    print("\n🔧 FORENSIC GRAPH AGENT v3.0 - REAL DATA MODE")
    print("   Analyse forensic avec données blockchain réelles")
    print("   " + "-" * 60)
    
    # Vérifier les dépendances
    try:
        import networkx as nx
        import community
        import requests
        print("✅ Dépendances satisfaites")
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("   Installation: pip install networkx python-louvain requests")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    
    # Exécuter l'analyse
    start_time = time.time()
    token = "0x6982508145454ce325ddbe47a25d4ec3d2311933"
    
    try:
        if token:
            print(f"\n🎯 Analyse du token: {token}")
            results = main_real_data(token_contract_address=token)
        else:
            print("\n🎯 Analyse générique (ETH)")
            results = main_real_data()
            
        elapsed_time = time.time() - start_time
        
        print(f"\n⏱️  Temps d'exécution: {elapsed_time:.2f} secondes")
        
        if results:
            print(f"📊 {len(results)} détections analysées avec succès")
            
            # Statistiques finales
            critical_count = sum(1 for r in results if r.get('risk_level') in ['CRITICAL', 'HIGH'])
            if critical_count > 0:
                print(f"🚨 {critical_count} détections à haut risque nécessitent investigation")
                
        else:
            print("📊 Aucune détection significative")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Analyse interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎯 Analyse terminée")
    print("=" * 70)