# Forensic Graph Agent (`work.py`)

## Overview
- Fetches on-chain data from BitQuery (transfers, internal calls, token holders), builds directed graphs, and detects suspicious clusters (wash trading, mixers, Ponzi-like, cascades, whales).
- Computes risk scores and prints a report, then exports JSON and CSV summaries.
- Measures fetch durations for external calls to help troubleshoot latency.

## Requirements
- Python 3.10+ (tested on 3.x).
- Packages: `networkx`, `python-louvain` (imported as `community`), `requests`. Install with:
```powershell
pip install networkx python-louvain requests
```
- A BitQuery API key.

## Configuration
- Update the `BITQUERY_API_KEY` value in `main_real_data` or read it from an environment variable before creating `ForensicGraphAgent` if you prefer not to hardcode it.
- Default token analyzed in `__main__` is `0x6982508145454ce325ddbe47a25d4ec3d2311933`. Set `token = None` at the bottom of the file to run generic ETH/token analysis, or change it to the contract you want to inspect.

## Quickstart
```powershell
cd for
python -m venv venv
venv\Scripts\activate
pip install networkx python-louvain requests
python work.py
```
- To analyze another token, edit the `token` variable near the bottom or call `main_real_data(token_contract_address="<token>")` from another script.
- The script currently comments out argparse parsing; re-enable it if you want CLI flags (`--token`, `--days`, `--limit`).

## Processing Flow
1. `fetch_real_transactions` pulls recent transfers (optionally by token contract) and logs fetch time.
2. `fetch_real_internal_transactions` pulls smart contract calls tied to observed addresses and logs fetch time.
3. `fetch_real_token_holders` gathers holder balances for a token and logs fetch time.
4. `build_graph_from_real_data` builds directed graphs for normal and internal flows.
5. Detection passes: `detect_funding_patterns`, `_detect_cascade_funding`, `detect_wash_trading_patterns`, `detect_mixer_patterns`, `detect_ponzi_patterns`, plus clustering helpers for common sources, highly connected groups, amount-based clusters, and whales.
6. `calculate_advanced_risk_metrics` enriches clusters with scores/levels; `generate_real_data_report` prints a readable summary.
7. `export_results` writes JSON and CSV (`forensic_real_YYYYMMDD_HHMMSS.*` or `forensic_token_<addr>_...`).

## Outputs
- JSON: full cluster data.
- CSV: concise per-cluster summary (`type`, `risk_level`, `risk_score`, `size`, `whale_count`, `total_amount`, `description`).
- Console: progress, sample transactions, fetch timings, and risk highlights.

## Notes
- Fetch limits default to high values (e.g., 5000) — reduce them if BitQuery quotas or latency are an issue.
- Graphs live in memory (`self.G`, `self.internal_G`, `self.combined_G`); export routines do not persist the graph structures.
- Timing logs use `time.time()` and are printed in seconds for quick diagnostics.
