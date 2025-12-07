"""Test script to check mixer API response"""
import httpx
import json

AGENT_API_URL = "https://nonunified-maxwell-noisome.ngrok-free.dev/webhook/3fbd3590-4b09-48d7-8141-ce14f2038ef1"

async def test():
    token = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    payload = {"token": token}
    
    print(f"Testing API: {AGENT_API_URL}")
    print(f"Payload: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(AGENT_API_URL, json=payload)
            print(f"\nStatus: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"\nFull Response:\n{json.dumps(response.json(), indent=2)[:1000]}")
            
            # Check specific fields
            data = response.json()
            print(f"\nKeys: {list(data.keys())}")
            
            if 'output_json' in data:
                output_json = data['output_json']
                print(f"\noutput_json type: {type(output_json)}")
                print(f"output_json (first 500 chars): {str(output_json)[:500]}")
                
                # Try to parse
                if isinstance(output_json, str):
                    try:
                        parsed = json.loads(output_json)
                        print(f"\nParsed output_json type: {type(parsed)}")
                        if isinstance(parsed, list):
                            print(f"List length: {len(parsed)}")
                            if len(parsed) > 0:
                                print(f"First item type: {type(parsed[0])}")
                                print(f"First item keys: {list(parsed[0].keys()) if isinstance(parsed[0], dict) else 'N/A'}")
                                if isinstance(parsed[0], dict) and 'text' in parsed[0]:
                                    text_field = parsed[0]['text']
                                    print(f"\ntext field type: {type(text_field)}")
                                    print(f"text field (first 300 chars): {str(text_field)[:300]}")
                                    
                                    # Try to parse the text field
                                    try:
                                        viz_data = json.loads(text_field)
                                        print(f"\nViz data keys: {list(viz_data.keys())}")
                                        print(f"Mixers: {len(viz_data.get('mixers', []))} items")
                                        print(f"Wallet exposures: {list(viz_data.get('wallet_exposures', {}).keys())}")
                                    except Exception as e:
                                        print(f"Failed to parse text field: {e}")
                    except Exception as e:
                        print(f"Failed to parse output_json: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
