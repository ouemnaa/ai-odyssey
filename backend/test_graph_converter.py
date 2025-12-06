#!/usr/bin/env python
"""Quick test to verify graph converter works with real node data"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.utils.graph_converter import _extract_nodes
from app.schemas.graph import NodeModel

# Create a mock graph with problematic node data
class MockGraph:
    def __init__(self):
        self._nodes = {
            "0x1234567890123456789012345678901234567890": {
                "annotation": None,  # This is the problematic case
                "type": "wallet"
            },
            "0x0987654321098765432109876543210987654321": {
                "annotation": "Valid Label",
                "type": "wallet"
            },
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd": {
                "type": "wallet"
                # No annotation key at all
            }
        }
        self._predecessors = {
            node: [] for node in self._nodes
        }
        
    def nodes(self):
        return self._nodes.keys()
    
    def __getitem__(self, node):
        return self._nodes[node]
    
    def predecessors(self, node):
        return iter(self._predecessors.get(node, []))
    
    def in_degree(self, node):
        return 0
    
    def out_degree(self, node):
        return 1

# Test the extraction
if __name__ == "__main__":
    print("Testing graph converter with edge cases...")
    
    graph = MockGraph()
    clusters = []
    
    try:
        nodes = _extract_nodes(graph, clusters)
        
        print(f"✅ Successfully extracted {len(nodes)} nodes")
        for node in nodes:
            print(f"  - {node.id}: label='{node.label}' (length={len(node.label)})")
            assert isinstance(node.label, str), f"Label should be string, got {type(node.label)}"
            assert node.label, f"Label should not be empty"
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
