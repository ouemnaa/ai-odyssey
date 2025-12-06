# # # import requests
# # # from neo_import import insert_transfers

# # # BITQUERY_API_KEY = "ory_at_IgOGfUWwtV3dqHQz4dW_bs5eWxgX7tnV0FdEo_GAYJI.vhiOQPEaYquvNRbmJAT3-DUId3dzWxiIT-1lFS2LNr4"

# # # query = """
# # # {
# # #   ethereum(network: ethereum) {
# # #     transfers(
# # #       options: {limit: 5000, desc: "block.timestamp.time"}
# # #       amount: {gt: 0}
# # #       date: {since: "2025-12-01"}
# # #       currency: {is: "ETH"}
# # #     ) {
# # #       block {
# # #         timestamp { time(format: "%Y-%m-%d %H:%M:%S") }
# # #       }
# # #       amount
# # #       sender { address }
# # #       receiver { address }
# # #       currency { symbol }
# # #     }
# # #   }
# # # }
# # # """





# # # r = requests.post(
# # #     "https://graphql.bitquery.io",
# # #     json={"query": query},
# # #     headers={
# # #         "Content-Type": "application/json",
# # #         "Authorization": f"Bearer {BITQUERY_API_KEY}"
# # #     }
# # # )

# # # print("Status:", r.status_code)


# # # data = r.json()
# # # if "errors" in data:
# # #     print(data["errors"])
# # #     exit()

# # # transfers = data["data"]["ethereum"]["transfers"]
# # # insert_transfers(transfers)
# # # print("Imported", len(transfers), "transactions into Neo4j 🚀")

# # # import_enhanced.py
# # from neo4j import GraphDatabase
# # import requests
# # import json

# # NEO4J_URI = "neo4j://127.0.0.1:7687"
# # NEO4J_USER = "neo4j"
# # NEO4J_PASSWORD = "NourIGL4"
# # BITQUERY_API_KEY = "ory_at_IgOGfUWwtV3dqHQz4dW_bs5eWxgX7tnV0FdEo_GAYJI.vhiOQPEaYquvNRbmJAT3-DUId3dzWxiIT-1lFS2LNr4"

# # driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# # def import_ethereum_data():
# #     """Import Ethereum data with ALL required fields"""
    
# #     # Clear existing data (optional)
# #     with driver.session() as session:
# #         session.run("MATCH (n) DETACH DELETE n")
# #         print("Cleared existing database")
    
# #     # BitQuery query for ETH transfers
# #     query = """
# #     {
# #       ethereum(network: ethereum) {
# #         transfers(
# #           options: {limit: 10000, desc: "block.timestamp.time"}
# #           amount: {gt: 0}
# #           date: {since: "2025-12-04"}
# #           currency: {is: "ETH"}
# #         ) {
# #           block {
# #             timestamp { time(format: "%Y-%m-%dT%H:%M:%S") }
# #             height
# #           }
# #           amount
# #           sender { address }
# #           receiver { address }
# #           currency { symbol }
# #           transaction { hash }
# #         }
# #       }
# #     }
# #     """
    
# #     # Fetch from BitQuery
# #     response = requests.post(
# #         "https://graphql.bitquery.io",
# #         json={"query": query},
# #         headers={
# #             "Content-Type": "application/json",
# #             "Authorization": f"Bearer {BITQUERY_API_KEY}"
# #         }
# #     )
    
# #     if response.status_code != 200:
# #         print(f"API Error: {response.status_code}")
# #         return
    
# #     data = response.json()
    
# #     if "errors" in data:
# #         print(f"GraphQL Errors: {data['errors']}")
# #         return
    
# #     transfers = data["data"]["ethereum"]["transfers"]
# #     print(f"Fetched {len(transfers)} transfers from BitQuery")
    
# #     # Import to Neo4j
# #     with driver.session() as session:
# #         for i, transfer in enumerate(transfers):
# #             if i % 500 == 0:
# #                 print(f"Imported {i}/{len(transfers)}...")
            
# #             session.run("""
# #                 MERGE (s:Wallet {address: $sender})
# #                 MERGE (r:Wallet {address: $receiver})
# #                 CREATE (s)-[t:SENT]->(r)
# #                 SET t.amount = $amount,
# #                     t.time = $time,
# #                     t.currency = $currency,
# #                     t.block_height = $block_height,
# #                     t.tx_hash = $tx_hash
# #             """, 
# #             sender=transfer["sender"]["address"].lower(),
# #             receiver=transfer["receiver"]["address"].lower(),
# #             amount=float(transfer["amount"]),
# #             time=transfer["block"]["timestamp"]["time"],
# #             currency=transfer["currency"]["symbol"],
# #             block_height=transfer["block"]["height"],
# #             tx_hash=transfer["transaction"]["hash"]
# #             )
    
# #     print(f"✅ Successfully imported {len(transfers)} transfers to Neo4j")

# # if __name__ == "__main__":
# #     import_ethereum_data()

# # check_smart_contract_schema.py
# # import_enhanced_with_mixer.py
# from neo4j import GraphDatabase
# import requests
# import json

# NEO4J_URI = "neo4j://127.0.0.1:7687"
# NEO4J_USER = "neo4j"
# NEO4J_PASSWORD = "NourIGL4"
# BITQUERY_API_KEY = "ory_at_IgOGfUWwtV3dqHQz4dW_bs5eWxgX7tnV0FdEo_GAYJI.vhiOQPEaYquvNRbmJAT3-DUId3dzWxiIT-1lFS2LNr4"

# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# def detect_mixer_annotation(annotation):
#     """Check if an annotation contains mixer/scam related keywords"""
#     if not annotation:
#         return False
    
#     annotation_lower = annotation.lower()
#     mixer_keywords = ["tornado", "mixer", "scam", "fraud", "hack", "phishing", "malicious"]
    
#     return any(keyword in annotation_lower for keyword in mixer_keywords)

# def get_address_annotations(transfers):
#     """Extract unique addresses with their annotations from transfers"""
#     address_data = {}
    
#     for transfer in transfers:
#         sender_addr = transfer["sender"]["address"].lower()
#         receiver_addr = transfer["receiver"]["address"].lower()
        
#         # Get sender annotation if available
#         if "annotation" in transfer["sender"]:
#             address_data[sender_addr] = transfer["sender"]["annotation"]
        
#         # Get receiver annotation if available
#         if "annotation" in transfer["receiver"]:
#             address_data[receiver_addr] = transfer["receiver"]["annotation"]
    
#     return address_data

# def import_ethereum_data_with_mixer():
#     """Import Ethereum data with mixer detection"""
    
#     # Clear existing data (optional)
#     with driver.session() as session:
#         session.run("MATCH (n) DETACH DELETE n")
#         print("Cleared existing database")
    
#     # BitQuery query for ETH transfers WITH annotations
#     query = """
#     {
#       ethereum(network: ethereum) {
#         transfers(
#           options: {limit: 10000, desc: "block.timestamp.time"}
#           amount: {gt: 0}
#           date: {since: "2025-12-04"}
#           currency: {is: "ETH"}
#         ) {
#           block {
#             timestamp { time(format: "%Y-%m-%dT%H:%M:%S") }
#             height
#           }
#           amount
#           sender { 
#             address 
#             annotation
#           }
#           receiver { 
#             address 
#             annotation
#           }
#           currency { symbol }
#           transaction { hash }
#         }
#       }
#     }
#     """
    
#     # Fetch from BitQuery
#     response = requests.post(
#         "https://graphql.bitquery.io",
#         json={"query": query},
#         headers={
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {BITQUERY_API_KEY}"
#         }
#     )
    
#     if response.status_code != 200:
#         print(f"API Error: {response.status_code}")
#         return
    
#     data = response.json()
    
#     if "errors" in data:
#         print(f"GraphQL Errors: {data['errors']}")
#         return
    
#     transfers = data["data"]["ethereum"]["transfers"]
#     print(f"Fetched {len(transfers)} transfers from BitQuery")
    
#     # Extract address annotations
#     address_annotations = get_address_annotations(transfers)
    
#     # First pass: Create all wallet nodes with mixer flag
#     with driver.session() as session:
#         # Create wallets with mixer property
#         for address, annotation in address_annotations.items():
#             is_mixer = detect_mixer_annotation(annotation)
            
#             session.run("""
#                 MERGE (w:Wallet {address: $address})
#                 SET w.is_mixer = $is_mixer,
#                     w.annotation = $annotation
#             """,
#             address=address,
#             is_mixer=is_mixer,
#             annotation=annotation
#             )
    
#     # Second pass: Create transfers
#     with driver.session() as session:
#         for i, transfer in enumerate(transfers):
#             if i % 500 == 0:
#                 print(f"Imported {i}/{len(transfers)} transfers...")
            
#             session.run("""
#                 MERGE (s:Wallet {address: $sender})
#                 MERGE (r:Wallet {address: $receiver})
#                 CREATE (s)-[t:SENT]->(r)
#                 SET t.amount = $amount,
#                     t.time = $time,
#                     t.currency = $currency,
#                     t.block_height = $block_height,
#                     t.tx_hash = $tx_hash
#             """, 
#             sender=transfer["sender"]["address"].lower(),
#             receiver=transfer["receiver"]["address"].lower(),
#             amount=float(transfer["amount"]),
#             time=transfer["block"]["timestamp"]["time"],
#             currency=transfer["currency"]["symbol"],
#             block_height=transfer["block"]["height"],
#             tx_hash=transfer["transaction"]["hash"]
#             )
    
#     # Query to see mixer addresses
#     with driver.session() as session:
#         result = session.run("""
#             MATCH (w:Wallet)
#             WHERE w.is_mixer = true
#             RETURN w.address, w.annotation
#             LIMIT 20
#         """)
        
#         print("\n📊 Detected Mixer Addresses:")
#         for record in result:
#             print(f"  - {record['w.address']}: {record['w.annotation']}")
    
#     print(f"\n✅ Successfully imported {len(transfers)} transfers to Neo4j with mixer detection")

# if __name__ == "__main__":
#  !   import_ethereum_data_with_mixer()

# COMPLETE_token_data_importer.py
# from neo4j import GraphDatabase
# import requests
# import json
# import time
# from datetime import datetime

# NEO4J_URI = "neo4j://127.0.0.1:7687"
# NEO4J_USER = "neo4j"
# NEO4J_PASSWORD = "NourIGL4"
# BITQUERY_API_KEY = "ory_at_IgOGfUWwtV3dqHQz4dW_bs5eWxgX7tnV0FdEo_GAYJI.vhiOQPEaYquvNRbmJAT3-DUId3dzWxiIT-1lFS2LNr4"

# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# def detect_mixer_annotation(annotation):
#     """Check if an annotation contains mixer/scam related keywords"""
#     if not annotation:
#         return False
    
#     annotation_lower = annotation.lower()
#     mixer_keywords = ["tornado", "mixer", "scam", "fraud", "hack", "phishing", "malicious"]
    
#     return any(keyword in annotation_lower for keyword in mixer_keywords)

# def import_token_transactions(token_address, token_symbol="MEME", limit=10000):
#     """Import token transactions for a specific token address with ALL fields"""
    
#     print(f"🔍 Importing transactions for token: {token_address}")
    
#     # BitQuery query for TOKEN transfers (ERC20) with ALL fields including annotations
#     query = """
#     {
#       ethereum(network: ethereum) {
#         transfers(
#           options: {limit: %d, desc: "block.timestamp.time"}
#           amount: {gt: 0}
#           date: {since: "2025-12-06"}
#           currency: {is: "%s"}
#         ) {
#           block {
#             timestamp { 
#               time(format: "%%Y-%%m-%%dT%%H:%%M:%%S") 
#               iso8601
#             }
#             height
#           }
#           amount
#           sender { 
#             address 
#             annotation
#             smartContract {
#               contractType
#               currency {
#                 symbol
#               }
#             }
#           }
#           receiver { 
#             address 
#             annotation
#             smartContract {
#               contractType
#               currency {
#                 symbol
#               }
#             }
#           }
#           currency { 
#             symbol
#             address
#             tokenType
#           }
#           transaction { 
#             hash
#             gasValue
#             gas
#           }
#           external
#         }
#       }
#     }
#     """ % (limit, token_address)
    
#     # Fetch from BitQuery
#     response = requests.post(
#         "https://graphql.bitquery.io",
#         json={"query": query},
#         headers={
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {BITQUERY_API_KEY}"
#         }
#     )
    
#     if response.status_code != 200:
#         print(f"API Error: {response.status_code}")
#         return 0
    
#     data = response.json()
    
#     if "errors" in data:
#         print(f"GraphQL Errors: {data['errors']}")
#         return 0
    
#     transfers = data["data"]["ethereum"]["transfers"]
#     print(f"📊 Fetched {len(transfers)} token transfers")
    
#     if len(transfers) == 0:
#         print(f"❌ No transactions found for token {token_address}")
#         return 0
    
#     # Import to Neo4j with ALL fields
#     imported_count = 0
#     with driver.session() as session:
#         for i, transfer in enumerate(transfers):
#             try:
#                 # Extract sender info
#                 sender_addr = transfer["sender"]["address"].lower()
#                 sender_annotation = transfer["sender"].get("annotation")
#                 sender_is_contract = bool(transfer["sender"].get("smartContract"))
#                 sender_contract_type = transfer["sender"].get("smartContract", {}).get("contractType") if sender_is_contract else None
                
#                 # Extract receiver info
#                 receiver_addr = transfer["receiver"]["address"].lower()
#                 receiver_annotation = transfer["receiver"].get("annotation")
#                 receiver_is_contract = bool(transfer["receiver"].get("smartContract"))
#                 receiver_contract_type = transfer["receiver"].get("smartContract", {}).get("contractType") if receiver_is_contract else None
                
#                 # Check if addresses are mixers based on annotation
#                 sender_is_mixer = detect_mixer_annotation(sender_annotation)
#                 receiver_is_mixer = detect_mixer_annotation(receiver_annotation)
                
#                 # Extract transaction details
#                 amount = float(transfer["amount"])
#                 timestamp = transfer["block"]["timestamp"]["time"]
#                 timestamp_iso = transfer["block"]["timestamp"].get("iso8601", timestamp)
#                 block_height = transfer["block"]["height"]
#                 tx_hash = transfer["transaction"]["hash"]
#                 gas_value = transfer["transaction"].get("gasValue", 0)
#                 gas_used = transfer["transaction"].get("gas", 0)
                
#                 # Extract currency details
#                 currency_symbol = transfer["currency"].get("symbol", token_symbol)
#                 currency_address = transfer["currency"].get("address", token_address)
#                 token_type = transfer["currency"].get("tokenType", "ERC20")
#                 is_external = transfer.get("external", False)
                
#                 # Create or update sender wallet with ALL properties
#                 session.run("""
#                     MERGE (s:Wallet {address: $address})
#                     SET s.annotation = $annotation,
#                         s.is_contract = $is_contract,
#                         s.contract_type = $contract_type,
#                         s.is_mixer = $is_mixer,
#                         s.last_seen = $timestamp,
#                         s.updated_at = datetime()
#                 """,
#                 address=sender_addr,
#                 annotation=sender_annotation,
#                 is_contract=sender_is_contract,
#                 contract_type=sender_contract_type,
#                 is_mixer=sender_is_mixer,
#                 timestamp=timestamp
#                 )
                
#                 # Create or update receiver wallet with ALL properties
#                 session.run("""
#                     MERGE (r:Wallet {address: $address})
#                     SET r.annotation = $annotation,
#                         r.is_contract = $is_contract,
#                         r.contract_type = $contract_type,
#                         r.is_mixer = $is_mixer,
#                         r.last_seen = $timestamp,
#                         r.updated_at = datetime()
#                 """,
#                 address=receiver_addr,
#                 annotation=receiver_annotation,
#                 is_contract=receiver_is_contract,
#                 contract_type=receiver_contract_type,
#                 is_mixer=receiver_is_mixer,
#                 timestamp=timestamp
#                 )
                
#                 # Create transaction with ALL properties
#                 session.run("""
#                     MATCH (s:Wallet {address: $sender})
#                     MATCH (r:Wallet {address: $receiver})
#                     CREATE (s)-[t:SENT]->(r)
#                     SET t.amount = $amount,
#                         t.time = $time,
#                         t.timestamp_iso = $timestamp_iso,
#                         t.currency = $currency,
#                         t.token_address = $token_address,
#                         t.token_type = $token_type,
#                         t.block_height = $block_height,
#                         t.tx_hash = $tx_hash,
#                         t.gas_value = $gas_value,
#                         t.gas_used = $gas_used,
#                         t.external = $external,
#                         t.imported_at = datetime()
#                 """, 
#                 sender=sender_addr,
#                 receiver=receiver_addr,
#                 amount=amount,
#                 time=timestamp,
#                 timestamp_iso=timestamp_iso,
#                 currency=currency_symbol,
#                 token_address=currency_address,
#                 token_type=token_type,
#                 block_height=block_height,
#                 tx_hash=tx_hash,
#                 gas_value=gas_value,
#                 gas_used=gas_used,
#                 external=is_external
#                 )
                
#                 imported_count += 1
                
#                 if i % 100 == 0:
#                     print(f"  Imported {i}/{len(transfers)}...")
                    
#             except Exception as e:
#                 print(f"Error importing transfer {i}: {e}")
#                 print(f"Transfer data: {json.dumps(transfer, indent=2)[:500]}...")
#                 continue
    
#     print(f"✅ Successfully imported {imported_count} token transactions")
#     return imported_count

# def import_multiple_tokens():
#     """Import transactions for multiple tokens with complete data"""
    
#     # Clear existing data first (optional - comment out if you want to keep existing data)
#     with driver.session() as session:
#         session.run("MATCH (n) DETACH DELETE n")
#         print("🧹 Cleared existing database")
    
#     # Test with a working token first (UNI has lots of transactions)
#     test_tokens = [
        
        
#         {
#             "address": "0xb131f4A55907B10d1F0A50d8ab8FA09EC342cd74",  # Your example token
#             "symbol": "MEME",
#             "name": "Unknown Meme Coin"
#         }
#     ]
    
#     total_imported = 0
#     for token in test_tokens:
#         print(f"\n{'='*60}")
#         print(f"📦 Importing: {token['name']} ({token['symbol']})")
#         print(f"📍 Address: {token['address']}")
#         print(f"{'='*60}")
        
#         count = import_token_transactions(
#             token_address=token['address'],
#             token_symbol=token['symbol'],
#             limit=5000  # Import last 5,000 transactions per token
#         )
#         total_imported += count
        
#         # Small delay between API calls
#         time.sleep(1)
    
#     print(f"\n{'='*60}")
#     print(f"🎉 TOTAL IMPORTED: {total_imported} transactions across {len(test_tokens)} tokens")
#     print(f"{'='*60}")
    
#     # Create indexes for faster queries
#     with driver.session() as session:
#         # Indexes for transactions
#         session.run("CREATE INDEX token_address_idx IF NOT EXISTS FOR ()-[t:SENT]-() ON (t.token_address)")
#         session.run("CREATE INDEX tx_hash_idx IF NOT EXISTS FOR ()-[t:SENT]-() ON (t.tx_hash)")
        
#         # Indexes for wallets
#         session.run("CREATE INDEX wallet_address_idx IF NOT EXISTS FOR (w:Wallet) ON (w.address)")
#         session.run("CREATE INDEX wallet_mixer_idx IF NOT EXISTS FOR (w:Wallet) ON (w.is_mixer)")
        
#         print("🔧 Created database indexes for faster queries")

# def verify_import():
#     """Verify the imported data has all required fields"""
#     print(f"\n{'='*60}")
#     print("🔍 VERIFYING IMPORTED DATA")
#     print(f"{'='*60}")
    
#     with driver.session() as session:
#         # Check total transactions
#         result = session.run("MATCH ()-[t:SENT]->() RETURN count(t) as total")
#         record = result.single()
#         total_tx = record['total']
#         print(f"📊 Total transactions: {total_tx}")
        
#         # Check unique tokens
#         result = session.run("MATCH ()-[t:SENT]->() RETURN collect(DISTINCT t.token_address) as tokens")
#         record = result.single()
#         tokens = [t for t in record['tokens'] if t]
#         print(f"📊 Unique tokens imported: {len(tokens)}")
        
#         # Check sample data structure
#         result = session.run("""
#             MATCH (s:Wallet)-[t:SENT]->(r:Wallet)
#             RETURN 
#                 keys(t) as tx_fields,
#                 keys(s) as sender_fields,
#                 keys(r) as receiver_fields,
#                 s.address as sender,
#                 r.address as receiver,
#                 t.amount as amount,
#                 t.currency as currency,
#                 t.token_address as token_address,
#                 t.time as time,
#                 t.tx_hash as tx_hash,
#                 s.annotation as sender_annotation,
#                 r.annotation as receiver_annotation,
#                 s.is_mixer as sender_is_mixer,
#                 r.is_mixer as receiver_is_mixer
#             LIMIT 3
#         """)
        
#         print("\n📋 SAMPLE TRANSACTIONS:")
#         for i, rec in enumerate(result):
#             print(f"\n  Transaction {i+1}:")
#             print(f"    Sender: {rec['sender'][:15]}... (Mixer: {rec['sender_is_mixer']})")
#             print(f"    Receiver: {rec['receiver'][:15]}... (Mixer: {rec['receiver_is_mixer']})")
#             print(f"    Amount: {rec['amount']} {rec['currency']}")
#             print(f"    Token: {rec['token_address'][:20]}...")
#             print(f"    Time: {rec['time']}")
#             print(f"    TX Hash: {rec['tx_hash'][:20]}...")
#             if rec['sender_annotation']:
#                 print(f"    Sender Annotation: {rec['sender_annotation'][:50]}...")
#             if rec['receiver_annotation']:
#                 print(f"    Receiver Annotation: {rec['receiver_annotation'][:50]}...")
        
#         # Check for mixer addresses
#         result = session.run("""
#             MATCH (w:Wallet)
#             WHERE w.is_mixer = true
#             RETURN w.address, w.annotation
#             LIMIT 10
#         """)
        
#         mixers = list(result)
#         print(f"\n⚠️  Detected Mixer Addresses: {len(mixers)}")
#         for rec in mixers[:5]:
#             print(f"  - {rec['w.address'][:20]}...: {rec['w.annotation'][:50]}...")

# if __name__ == "__main__":
#     # Import multiple tokens with complete data
#     import_multiple_tokens()
    
#     # Verify the import
#     verify_import()
    
#     print(f"\n{'='*60}")
#     print("✅ READY TO USE WITH MCP TOOL!")
#     print(f"Token addresses available in database:")
    
#     with driver.session() as session:
#         result = session.run("""
#             MATCH ()-[t:SENT]->()
#             WHERE t.token_address IS NOT NULL
#             RETURN DISTINCT t.token_address as token_address, 
#                    t.currency as symbol, 
#                    count(*) as tx_count
#             ORDER BY tx_count DESC
#         """)
        
#         for rec in result:
#             print(f"  - {rec['token_address']}")
#             print(f"    Symbol: {rec['symbol']}, Transactions: {rec['tx_count']}")
    
#     print(f"\n📌 Use these addresses in n8n AI Agent to test mixer detection!")
#     print(f"{'='*60}")
from neo4j import GraphDatabase
import requests
import json
import time
from datetime import datetime, timedelta
import sys

# ---------- CONFIGURATION ----------
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "NourIGL4"
BITQUERY_API_KEY = "ory_at_FDQCBD-inYXlqs23o6u2NioO9Yij9KNII2q0np7Cvz8.CSfseLjqDv8QMmKIh5_9u17uoQPcMNTNp0D5EbUdDqc"  # Get from https://graphql.bitquery.io/ide

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_valid_api_key():
    """Handle API key validation"""
    api_key = "ory_at_FDQCBD-inYXlqs23o6u2NioO9Yij9KNII2q0np7Cvz8.CSfseLjqDv8QMmKIh5_9u17uoQPcMNTNp0D5EbUdDqc"
    
    
    
    return api_key

def import_all_transactions_last_24h(limit=10000):
    """
    Import ALL Ethereum transfers from last 24 hours (any token)
    """
    api_key = get_valid_api_key()
    
    if not api_key:
        print("❌ No valid API key. Cannot fetch data.")
        return 0
    
    # Calculate date for last 24 hours
    since_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Query for ALL transfers (not limited to specific tokens)
    query = f"""
    {{
      ethereum(network: ethereum) {{
        transfers(
          options: {{limit: {limit}, desc: "block.timestamp.time"}}
          amount: {{gt: 0}}
          date: {{since: "{since_date}"}}
        ) {{
          block {{
            timestamp {{ 
              time(format: "%Y-%m-%dT%H:%M:%S") 
              iso8601
            }}
            height
          }}
          amount
          sender {{ 
            address 
            annotation
          }}
          receiver {{ 
            address 
            annotation
          }}
          currency {{ 
            symbol 
            address
            tokenType
          }}
          transaction {{ 
            hash
          }}
          external
        }}
      }}
    }}
    """
    
    print(f"📡 Fetching ALL transfers from last 24 hours (limit: {limit})...")
    print(f"📅 Since date: {since_date}")
    
    try:
        response = requests.post(
            "https://graphql.bitquery.io",
            json={"query": query},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            timeout=45
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return 0
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
            return 0
        
        transfers = data["data"]["ethereum"]["transfers"]
        print(f"✅ Fetched {len(transfers)} total transfers")
        
        if len(transfers) == 0:
            print("⚠️  No transfers found")
            return 0
        
        # Clear old data first (optional)
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🗑️ Cleared existing database")
        
        # Import in batches
        batch_size = 500
        imported_count = 0
        
        for i in range(0, len(transfers), batch_size):
            batch = transfers[i:i + batch_size]
            batch_transactions = []
            
            for transfer in batch:
                try:
                    # Extract token address (handle ETH case)
                    token_address = transfer["currency"].get("address")
                    if not token_address:
                        # For ETH transfers, use zero address or special marker
                        token_address = "0x0000000000000000000000000000000000000000"
                    
                    tx_data = {
                        'sender': transfer["sender"]["address"].lower(),
                        'receiver': transfer["receiver"]["address"].lower(),
                        'amount': float(transfer["amount"]),
                        'timestamp': transfer["block"]["timestamp"]["time"],
                        'timestamp_iso': transfer["block"]["timestamp"].get("iso8601", ""),
                        'currency': transfer["currency"].get("symbol", "UNKNOWN"),
                        'token_address': token_address.lower(),
                        'token_type': transfer["currency"].get("tokenType", "UNKNOWN"),
                        'tx_hash': transfer["transaction"]["hash"],
                        'block_height': transfer["block"]["height"],
                        'external': transfer.get("external", False),
                        'sender_annotation': transfer["sender"].get("annotation", ""),
                        'receiver_annotation': transfer["receiver"].get("annotation", "")
                    }
                    batch_transactions.append(tx_data)
                except Exception as e:
                    print(f"⚠️ Error parsing transfer: {e}")
                    continue
            
            # Import batch to Neo4j
            if batch_transactions:
                try:
                    with driver.session() as session:
                        result = session.run("""
                            UNWIND $batch AS tx
                            MERGE (s:Wallet {address: tx.sender})
                            SET s.annotation = tx.sender_annotation,
                                s.last_seen = tx.timestamp,
                                s.updated_at = datetime()
                            
                            MERGE (r:Wallet {address: tx.receiver})
                            SET r.annotation = tx.receiver_annotation,
                                r.last_seen = tx.timestamp,
                                r.updated_at = datetime()
                            
                            MERGE (s)-[t:SENT]->(r)
                            SET t.amount = tx.amount,
                                t.time = tx.timestamp,
                                t.timestamp_iso = tx.timestamp_iso,
                                t.currency = tx.currency,
                                t.token_address = tx.token_address,
                                t.token_type = tx.token_type,
                                t.tx_hash = tx.tx_hash,
                                t.block_height = tx.block_height,
                                t.external = tx.external,
                                t.imported_at = datetime(),
                                t.source = 'bitquery_24h'
                        """, batch=batch_transactions)
                        
                        summary = result.consume()
                        imported_count += len(batch_transactions)
                    
                    print(f"  Imported batch {i//batch_size + 1}/{(len(transfers)+batch_size-1)//batch_size} " +
                          f"({min(i+batch_size, len(transfers))}/{len(transfers)})")
                    
                except Exception as e:
                    print(f"⚠️ Error importing batch: {e}")
                    continue
        
        print(f"\n✅ Successfully imported {imported_count} transfers")
        
        # Create indexes for better query performance
        with driver.session() as session:
            session.run("CREATE INDEX IF NOT EXISTS FOR (w:Wallet) ON (w.address)")
            session.run("CREATE INDEX IF NOT EXISTS FOR ()-[t:SENT]-() ON (t.token_address)")
            session.run("CREATE INDEX IF NOT EXISTS FOR ()-[t:SENT]-() ON (t.tx_hash)")
            print("🔧 Created database indexes")
        
        # Verify import
        with driver.session() as session:
            result = session.run("""
                MATCH ()-[t:SENT]->()
                RETURN 
                    count(t) as total_transactions,
                    count(DISTINCT t.token_address) as unique_tokens,
                    collect(DISTINCT t.currency) as currencies
            """)
            
            record = result.single()
            print(f"\n📊 Database Summary:")
            print(f"  Total transactions: {record['total_transactions']}")
            print(f"  Unique token addresses: {record['unique_tokens']}")
            print(f"  Currencies found: {', '.join([c for c in record['currencies'] if c][:10])}")
        
        return imported_count
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return 0

def check_database_contents():
    """Check what's in the database"""
    print("\n🔍 Checking database contents...")
    
    with driver.session() as session:
        # Total transactions
        result = session.run("MATCH ()-[t:SENT]->() RETURN count(t) as total")
        total = result.single()['total']
        print(f"📊 Total transactions: {total}")
        
        # Top tokens by transaction count
        result = session.run("""
            MATCH ()-[t:SENT]->()
            WHERE t.token_address IS NOT NULL AND t.token_address <> '0x0000000000000000000000000000000000000000'
            RETURN t.currency as symbol, 
                   t.token_address as address,
                   count(*) as tx_count
            ORDER BY tx_count DESC
            LIMIT 10
        """)
        
        print("\n🏆 Top tokens in database:")
        for rec in result:
            print(f"  {rec['symbol']}: {rec['address'][:20]}... ({rec['tx_count']} txs)")
        
        # Sample transactions
        result = session.run("""
            MATCH (s:Wallet)-[t:SENT]->(r:Wallet)
            RETURN s.address as sender, 
                   r.address as receiver,
                   t.amount as amount,
                   t.currency as currency,
                   t.token_address as token_address,
                   t.time as time
            ORDER BY t.time DESC
            LIMIT 3
        """)
        
        print("\n📋 Latest transactions:")
        for rec in result:
            print(f"  {rec['sender'][:10]}... → {rec['receiver'][:10]}...")
            print(f"    {rec['amount']:.4f} {rec['currency']}")
            print(f"    Token: {rec['token_address'][:20]}...")
            print(f"    Time: {rec['time']}")
            print()

def get_token_transactions_from_db(token_address, limit=10000):
    """
    Get transactions for a specific token from the database
    This is what the AI Agent will use
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Wallet)-[t:SENT]->(r:Wallet)
            WHERE t.token_address = $token_address
            RETURN s.address as sender, 
                   r.address as receiver,
                   t.amount as amount,
                   t.time as timestamp,
                   t.currency as currency,
                   t.token_address as token_address,
                   t.tx_hash as tx_hash,
                   t.block_height as block_height
            ORDER BY t.time DESC
            LIMIT $limit
        """, token_address=token_address.lower(), limit=limit)
        
        transactions = []
        for rec in result:
            transactions.append({
                'sender': rec['sender'],
                'receiver': rec['receiver'],
                'amount': float(rec['amount']),
                'timestamp': rec['timestamp'],
                'currency': rec['currency'],
                'token_address': rec['token_address'],
                'tx_hash': rec.get('tx_hash', ''),
                'block_height': rec.get('block_height', 0)
            })
        
        print(f"📊 Found {len(transactions)} transactions for token {token_address}")
        return transactions

if __name__ == "__main__":
    print("=" * 60)
    print("📥 ETHEREUM TRANSACTION IMPORT TOOL")
    print("=" * 60)
    print("This will import ALL transfers from last 24 hours")
    print("Then the AI Agent can query for specific tokens")
    print("=" * 60)
    
    choice = input("\nChoose action:\n1. Import all transactions (last 24h)\n2. Check database contents\n3. Get token transactions\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        imported = import_all_transactions_last_24h(limit=10000)
        if imported > 0:
            print(f"\n🎉 Ready for AI Agent! Imported {imported} transactions.")
            print("You can now run the MCP tool to analyze specific tokens.")
    elif choice == "2":
        check_database_contents()
    elif choice == "3":
        token_addr = input("Enter token address: ").strip()
        if token_addr:
            txs = get_token_transactions_from_db(token_addr)
            print(f"Found {len(txs)} transactions")
    else:
        print("❌ Invalid choice")