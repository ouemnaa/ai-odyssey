"""Mixer detection service - integrates with first-flow agent"""

import asyncio
import logging
import time
import json
import sys
import httpx
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Agent API configuration
AGENT_API_URL = "https://nonunified-maxwell-noisome.ngrok-free.dev/webhook/3fbd3590-4b09-48d7-8141-ce14f2038ef1"
AGENT_HEALTH_ENDPOINT = f"{AGENT_API_URL}/health"
AGENT_MIXER_ENDPOINT = AGENT_API_URL


class MixerDetectionService:
    """Service for mixer detection using first-flow agent"""
    
    def __init__(self):
        """Initialize mixer detection service"""
        self.agent = None
        logger.info(f"✓ Initialized mixer detection service")
        logger.info(f"  Agent API: {AGENT_MIXER_ENDPOINT}")
    
    async def initialize_agent(self) -> bool:
        """Check if agent API is available"""
        try:
            logger.info(f"🔍 Checking agent API at {AGENT_API_URL}")
            
            response = httpx.get(AGENT_HEALTH_ENDPOINT, timeout=10.0)
            
            if response.status_code == 200:
                logger.info("✓ Agent API is healthy and available")
                self.agent = True
                return True
            else:
                logger.warning(f"⚠️ Agent API returned status {response.status_code}")
                return False
                
        except httpx.ConnectError:
            logger.error(f"✗ Cannot connect to agent API at {AGENT_API_URL}")
            return False
        except Exception as e:
            logger.error(f"✗ Error checking agent health: {e}")
            return False
    
    async def analyze_token_for_mixers(
        self, 
        token_address: str,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze token for mixer connections and flagging.
        
        Args:
            token_address: Token contract address
            max_hops: Maximum hops for provenance tracing
            
        Returns:
            Complete mixer analysis report
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Starting mixer analysis for token: {token_address}")
            
            # Run analysis in thread pool to avoid blocking
            report = await asyncio.to_thread(
                self._run_mixer_analysis,
                token_address,
                max_hops
            )
            
            duration = time.time() - start_time
            logger.info(f"✓ Mixer analysis completed in {duration:.2f}s")
            
            return {
                "success": True,
                "token_address": token_address,
                "analysis_duration": f"{duration:.2f}s",
                "timestamp": datetime.utcnow().isoformat(),
                "report": report
            }
            
        except Exception as e:
            logger.error(f"✗ Mixer analysis failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "token_address": token_address,
                "error": str(e)
            }
    
    def _run_mixer_analysis(self, token_address: str, max_hops: int) -> Dict[str, Any]:
        """
        Run mixer analysis by calling the first-flow agent API.
        
        Makes a POST request to the agent's /mcp/detect_mixer_origins endpoint.
        """
        try:
            logger.info(f"🔍 Calling agent API for mixer detection: {token_address}")
            
            # Prepare request payload - ngrok webhook expects only 'token'
            payload = {
                "token": token_address
            }
            
            logger.info(f"Sending payload: {payload} to {AGENT_MIXER_ENDPOINT}")
            
            # Call agent API
            response = httpx.post(
                AGENT_MIXER_ENDPOINT,
                json=payload,
                timeout=120.0  # Agent analysis can take 30+ seconds
            )
            
            logger.info(f"Agent API response status: {response.status_code}")
            logger.info(f"Agent API response content length: {len(response.content)} bytes")
            logger.info(f"Agent API response text (first 500 chars): {response.text[:500]}")
            
            if response.status_code != 200:
                error_msg = f"Agent API error: {response.status_code}"
                logger.error(error_msg)
                logger.error(f"Response text: {response.text}")
                return {
                    "error": True,
                    "message": error_msg
                }
            
            # Check if response has content
            if not response.text or not response.text.strip():
                logger.error("Agent API returned empty response body")
                return {
                    "error": True,
                    "message": "Agent API returned empty response"
                }
            
            # Parse response
            try:
                response_data = response.json()
                logger.info(f"Agent API response keys: {list(response_data.keys())}")
                logger.info(f"Agent API full response (truncated):")
                response_str = json.dumps(response_data, indent=2)
                logger.info(response_str[:2000])  # Log first 2000 chars
                if len(response_str) > 2000:
                    logger.info(f"... (response too long, total {len(response_str)} chars)")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                logger.error(f"Response text: {response.text}")
                return {
                    "error": True,
                    "message": "Agent returned invalid JSON"
                }
            
            # The response directly contains output and output_json (not nested under 'result')
            if 'output' not in response_data and 'output_json' not in response_data:
                logger.error(f"Missing expected fields in response. Keys: {list(response_data.keys())}")
                return {
                    "error": True,
                    "message": "Agent returned response with unexpected format"
                }
            
            # Transform response to expected format
            transformed_report = self._transform_ngrok_response(response_data)
            
            logger.info(f"✓ Agent analysis complete")
            logger.info(f"  - Mixers detected: {transformed_report.get('mixer_detection_results', {}).get('summary', {}).get('total_mixers_detected', 0)}")
            logger.info(f"  - Wallets exposed: {transformed_report.get('wallet_exposure_analysis', {}).get('summary', {}).get('wallets_with_mixer_exposure', 0)}")
            logger.info(f"  - Analysis time: {transformed_report.get('execution_summary', {}).get('analysis_duration_seconds', 0)}s")
            
            return transformed_report
            
        except httpx.ConnectError:
            error_msg = f"Cannot connect to agent API at {AGENT_MIXER_ENDPOINT}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException:
            error_msg = "Agent API request timeout"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"✗ Error calling agent API: {str(e)}", exc_info=True)
            raise
    
    def _transform_ngrok_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform ngrok webhook response to backend report format.
        
        Ngrok returns:
        {
            'output': '**Mixer Detection Report** ...',
            'output_json': '[{"type":"text","text":"{...}"}]'
        }
        
        We need to parse output_json and build the report structure.
        """
        try:
            text_report = response_data.get('output', '')
            output_json = response_data.get('output_json', [])
            
            logger.info(f"\n{'='*80}")
            logger.info(f"TRANSFORM NGROK RESPONSE - DEBUG")
            logger.info(f"{'='*80}")
            logger.info(f"Raw output_json type: {type(output_json)}")
            logger.info(f"Raw output_json length: {len(output_json) if isinstance(output_json, (list, str)) else 'N/A'}")
            logger.info(f"Raw output_json content (first 1000 chars): {str(output_json)[:1000]}")
            
            # Parse output_json which is an array with text field
            viz_data = {}
            if output_json:
                try:
                    # Handle both string and already-parsed JSON
                    if isinstance(output_json, str):
                        logger.info("→ output_json is string, parsing as JSON...")
                        try:
                            output_json = json.loads(output_json)
                            logger.info(f"✓ Successfully parsed output_json string")
                        except json.JSONDecodeError as e:
                            logger.error(f"✗ Failed to parse output_json string: {e}")
                            logger.error(f"Raw string (first 200 chars): {output_json[:200]}")
                            output_json = []
                    
                    logger.info(f"Parsed output_json type: {type(output_json)}, is_list: {isinstance(output_json, list)}")
                    
                    if isinstance(output_json, list) and len(output_json) > 0:
                        logger.info(f"→ output_json is list with {len(output_json)} items")
                        item = output_json[0]
                        logger.info(f"First item type: {type(item)}")
                        logger.info(f"First item: {item}")
                        
                        json_text = item.get('text', '{}') if isinstance(item, dict) else '{}'
                        logger.info(f"→ json_text type: {type(json_text)}, length: {len(json_text) if isinstance(json_text, str) else 0}")
                        logger.info(f"json_text (first 500 chars): {str(json_text)[:500]}")
                        
                        if isinstance(json_text, str) and json_text.strip():
                            try:
                                viz_data = json.loads(json_text)
                                logger.info(f"✓ Successfully parsed viz_data")
                                logger.info(f"viz_data keys: {list(viz_data.keys())}")
                            except json.JSONDecodeError as e:
                                logger.error(f"✗ Failed to parse json_text: {e}")
                                logger.error(f"json_text (first 300 chars): {json_text[:300]}")
                        else:
                            logger.warning(f"json_text is not a valid string or is empty")
                            viz_data = json_text if isinstance(json_text, dict) else {}
                    else:
                        logger.warning(f"output_json is not a list or is empty. Type: {type(output_json)}")
                        
                except Exception as e:
                    logger.error(f"✗ Error parsing output_json: {e}", exc_info=True)
            
            # Extract summary data
            summary = viz_data.get('summary', {})
            mixers = viz_data.get('mixers', [])
            wallet_exposures = viz_data.get('wallet_exposures', {})
            network_stats = viz_data.get('network_stats', {})
            top_exposed = wallet_exposures.get('top_exposed', []) if isinstance(wallet_exposures, dict) else []
            
            logger.info(f"\n→ EXTRACTED DATA:")
            logger.info(f"Summary: {summary}")
            logger.info(f"Mixers type: {type(mixers)}, length: {len(mixers) if isinstance(mixers, (list, dict)) else 'N/A'}")
            logger.info(f"Mixers content: {mixers}")
            logger.info(f"Wallet exposures type: {type(wallet_exposures)}")
            logger.info(f"Top exposed type: {type(top_exposed)}, length: {len(top_exposed) if isinstance(top_exposed, list) else 'N/A'}")
            logger.info(f"Top exposed: {top_exposed}")
            
            # Build standardized report structure
            report = {
                'execution_summary': {
                    'token_address': summary.get('token', 'unknown'),
                    'analysis_duration_seconds': float(summary.get('analysis_time', '0s').rstrip('s')),
                    'data_processed': {
                        'transactions_analyzed': summary.get('transactions_analyzed', 0),
                        'unique_wallets': summary.get('unique_wallets', 0),
                    }
                },
                'mixer_detection_results': {
                    'summary': {
                        'total_mixers_detected': len(mixers) if isinstance(mixers, list) else (len(mixers) if isinstance(mixers, dict) else 0)
                    },
                    'detailed_mixer_reports': [
                        {
                            'address': m.get('address', ''),
                            'score': m.get('score', 0),
                            'mixer_type': m.get('type', 'behavioral'),
                            'heuristic_scores': m.get('reasoning', {})
                        }
                        for m in (mixers if isinstance(mixers, list) else [])
                    ]
                },
                'wallet_exposure_analysis': {
                    'summary': {
                        'wallets_with_mixer_exposure': len(top_exposed),
                        'total_wallets_exposed': wallet_exposures.get('total_wallets_exposed', 0) if isinstance(wallet_exposures, dict) else 0
                    },
                    'high_risk_wallets': [
                        {
                            'address': w.get('wallet', ''),
                            'risk_assessment': {
                                'risk_level': 'HIGH' if w.get('mixer_count', 0) > 0 else 'LOW',
                                'risk_score': 0.7 if w.get('mixer_count', 0) > 0 else 0.3
                            }
                        }
                        for w in (top_exposed if isinstance(top_exposed, list) else [])
                    ]
                },
                'network_analysis': {
                    'graph_statistics': network_stats
                },
                'visualization_data': {
                    'nodes': self._build_nodes_from_viz_data(mixers if isinstance(mixers, list) else [], top_exposed if isinstance(top_exposed, list) else []),
                    'edges': []
                },
                'actionable_insights': {
                    'immediate_actions': [],
                    'recommendations': ['Monitor detected mixers for suspicious activity']
                }
            }
            
            logger.info(f"\n✓ REPORT BUILD COMPLETE:")
            logger.info(f"Total nodes built: {len(report['visualization_data']['nodes'])}")
            logger.info(f"Total mixers: {report['mixer_detection_results']['summary']['total_mixers_detected']}")
            logger.info(f"Total wallets: {len(top_exposed)}")
            logger.info(f"{'='*80}\n")
            
            return report
            
        except Exception as e:
            logger.error(f"✗ Error transforming ngrok response: {e}", exc_info=True)
            return {}
    
    def _build_nodes_from_viz_data(self, mixers: List[Dict], wallets: List[Dict]) -> List[Dict[str, Any]]:
        """Build graph nodes from mixer and wallet data"""
        nodes = []
        
        logger.info(f"_build_nodes_from_viz_data called:")
        logger.info(f"  - mixers type: {type(mixers)}, length: {len(mixers) if isinstance(mixers, (list, dict)) else 'N/A'}")
        logger.info(f"  - wallets type: {type(wallets)}, length: {len(wallets) if isinstance(wallets, (list, dict)) else 'N/A'}")
        
        # Add mixer nodes
        if isinstance(mixers, list):
            for mixer in mixers:
                try:
                    node = {
                        'id': mixer.get('address', 'unknown'),
                        'label': mixer.get('address', 'unknown')[:12] + '...',
                        'type': 'mixer',
                        'risk_score': mixer.get('score', 0),
                        'size': 15,
                        'mixer_type': mixer.get('type', 'behavioral')
                    }
                    nodes.append(node)
                    logger.info(f"  ✓ Added mixer node: {node['id']}")
                except Exception as e:
                    logger.error(f"  ✗ Error adding mixer node: {e}")
        else:
            logger.warning(f"  ⚠️  Mixers is not a list, it's {type(mixers)}")
        
        # Add wallet nodes
        if isinstance(wallets, list):
            for wallet in wallets:
                try:
                    node = {
                        'id': wallet.get('wallet', 'unknown'),
                        'label': wallet.get('wallet', 'unknown')[:12] + '...',
                        'type': 'wallet',
                        'risk_score': 0.7 if wallet.get('mixer_count', 0) > 0 else 0.3,
                        'size': 10
                    }
                    nodes.append(node)
                    logger.info(f"  ✓ Added wallet node: {node['id']}")
                except Exception as e:
                    logger.error(f"  ✗ Error adding wallet node: {e}")
        else:
            logger.warning(f"  ⚠️  Wallets is not a list, it's {type(wallets)}")
        
        logger.info(f"✓ Built {len(nodes)} total nodes")
        return nodes
    
    def _build_nodes_from_report(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visualization nodes from mixer detection report"""
        nodes = []
        
        # Add mixer nodes
        for mixer in report.get('mixer_detection_results', {}).get('detailed_mixer_reports', []):
            nodes.append({
                'id': mixer.get('address', 'unknown'),
                'label': mixer.get('address', 'unknown')[:10] + '...',
                'type': 'mixer',
                'risk_score': mixer.get('score', 0),
                'size': 15,
                'mixer_type': mixer.get('mixer_type', 'behavioral')
            })
        
        # Add wallet nodes from exposure analysis
        for wallet in report.get('wallet_exposure_analysis', {}).get('high_risk_wallets', []):
            nodes.append({
                'id': wallet.get('address', 'unknown'),
                'label': wallet.get('address', 'unknown')[:10] + '...',
                'type': 'wallet',
                'risk_score': wallet.get('risk_assessment', {}).get('risk_score', 0.5),
                'size': 10
            })
        
        return nodes


# Singleton instance
_mixer_service: Optional[MixerDetectionService] = None


def get_mixer_service() -> MixerDetectionService:
    """Get or create mixer detection service"""
    global _mixer_service
    if _mixer_service is None:
        _mixer_service = MixerDetectionService()
    return _mixer_service
