#!/usr/bin/env python3
"""Test script for mixer backend integration"""

import asyncio
import httpx
import json

async def test_mixer_endpoint():
    """Test the mixer analysis endpoint"""
    
    # Test token: WETH
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    
    print("=" * 80)
    print("🧪 MIXER ANALYSIS BACKEND TEST")
    print("=" * 80)
    print(f"\n📍 Testing token: {token_address}")
    print(f"📍 Endpoint: http://localhost:8000/api/v1/mixer/analyze/{token_address}")
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Test health check first
            print("\n[1/2] Testing health endpoint...")
            health_response = await client.get("http://localhost:8000/api/v1/mixer/health")
            print(f"Health Status: {health_response.status_code}")
            print(f"Health Response: {health_response.json()}")
            
            # Test analysis endpoint
            print("\n[2/2] Testing mixer analysis endpoint...")
            analysis_response = await client.post(
                f"http://localhost:8000/api/v1/mixer/analyze/{token_address}?max_hops=3"
            )
            
            print(f"\nStatus Code: {analysis_response.status_code}")
            
            if analysis_response.status_code == 200:
                data = analysis_response.json()
                print("\n✅ Analysis Response Structure:")
                print(f"  - Status: {data.get('status')}")
                print(f"  - Analysis ID: {data.get('analysisId')}")
                
                result = data.get('result', {})
                
                # Check text report
                text_report = result.get('textReport', '')
                print(f"\n📝 Text Report (first 500 chars):")
                print(f"  {text_report[:500]}...")
                
                # Check graph data
                graph_data = result.get('graphData', {})
                print(f"\n📊 Graph Data:")
                print(f"  - Nodes: {len(graph_data.get('nodes', []))}")
                print(f"  - Edges: {len(graph_data.get('edges', []))}")
                print(f"  - Statistics: {graph_data.get('statistics', {})}")
                
                # Check summary
                summary = result.get('summary', {})
                print(f"\n📈 Summary:")
                print(f"  - Token Address: {summary.get('tokenAddress')}")
                print(f"  - Analysis Time: {summary.get('analysisTime')}")
                print(f"  - Timestamp: {summary.get('timestamp')}")
                print(f"  - Mixers Detected: {summary.get('mixersDetected')}")
                print(f"  - Wallets Exposed: {summary.get('walletsExposed')}")
                
                # Detailed output
                print("\n📋 Full Response:")
                print(json.dumps(data, indent=2))
                
            else:
                print(f"\n❌ Error: {analysis_response.status_code}")
                print(f"Response: {analysis_response.text}")
                
    except httpx.ConnectError:
        print("\n❌ ERROR: Cannot connect to backend")
        print("Make sure backend is running: cd backend && .\\run_backend.bat")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_mixer_endpoint())
