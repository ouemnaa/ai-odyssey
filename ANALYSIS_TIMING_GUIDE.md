# Analysis Timing & Performance Tracking

## Overview

The analysis service now tracks timing for each operation step. You can view detailed performance metrics during and after analysis completion.

## Timing Features

### ✅ Per-Step Timing

Each of the 8 analysis steps is individually timed:

```
1. Initialize Agent           → X.XXs
2. Fetch Transactions         → X.XXs (e.g., 45.23s)
3. Fetch Internal Transactions → X.XXs
4. Build Graph                → X.XXs
5. Fetch Token Holders        → X.XXs
6. Detect Suspicious Patterns → X.XXs
7. Calculate Risk Metrics     → X.XXs
8. Convert to Frontend Format → X.XXs
```

### ✅ Total Duration

After analysis completes, total time is displayed:

```
✅ Analysis 8d14c327... completed in 128.45s
```

### ✅ Detailed Logging

Console logs show real-time progress:

```
✓ Step 1 (Initialize Agent): 2.34s
✓ Step 2 (Fetch Transactions): 45.23s - Got 10000 transactions
✓ Step 3 (Fetch Internal Transactions): 8.15s - Got 245 transactions
✓ Step 4 (Build Graph): 3.21s
✓ Step 5 (Fetch Token Holders): 1.89s - Got 50 holders
✓ Step 6 (Detect Patterns): 15.67s - Found 12 clusters
✓ Step 7 (Calculate Metrics): 8.92s
✓ Step 8 (Convert to Frontend): 2.18s
✅ Analysis 8d14c327... completed in 128.45s
   Timings: {'1_initialize_agent': '2.34s', '2_fetch_transactions': '45.23s', ...}
```

## API Response

### Status Endpoint `/api/v1/analysis/{id}/status`

Now includes timing information:

```json
{
  "analysisId": "8d14c327-a97d-40df-b78d-2551c688c991",
  "status": "completed",
  "progress": 100,
  "currentStep": "Analysis complete",
  "startedAt": "2025-12-06T14:30:22.123Z",
  "completedAt": "2025-12-06T14:32:30.456Z",
  "totalDuration": "128.45s",
  "stepTimings": {
    "1_initialize_agent": "2.34s",
    "2_fetch_transactions": "45.23s",
    "3_fetch_internal_txs": "8.15s",
    "4_build_graph": "3.21s",
    "5_fetch_token_holders": "1.89s",
    "6_detect_patterns": "15.67s",
    "7_calculate_metrics": "8.92s",
    "8_convert_to_frontend": "2.18s"
  },
  "errorMessage": null
}
```

## Performance Interpretation

### Typical Timings (by step)

| Step                   | Typical Time | Notes                              |
| ---------------------- | ------------ | ---------------------------------- |
| 1. Initialize Agent    | 2-5s         | Network I/O for connecting         |
| 2. Fetch Transactions  | 30-60s       | **Longest** - BitQuery API calls   |
| 3. Fetch Internal Txs  | 5-15s        | Fewer calls than main transactions |
| 4. Build Graph         | 2-5s         | NetworkX graph construction        |
| 5. Fetch Token Holders | 1-3s         | Quick token metadata fetch         |
| 6. Detect Patterns     | 10-30s       | Graph traversal algorithms         |
| 7. Calculate Metrics   | 5-15s        | PageRank, Gini calculations        |
| 8. Convert to Frontend | 1-5s         | Data transformation                |
| **TOTAL**              | **60-140s**  | Varies by token complexity         |

### What Affects Performance

**Slower:**

- Larger tokens (more holders, more transactions)
- Complex transaction patterns (more clusters to detect)
- Slower network connection (BitQuery API calls)

**Faster:**

- Smaller tokens (fewer transactions)
- Simple transaction patterns
- Cached API responses

## Monitoring & Debugging

### View in Logs

Timing information appears in backend logs:

```
backend/app/services/analysis_service.py
```

Look for lines like:

```
✓ Step X (Name): X.XXs
✅ Analysis ... completed in XXX.XXs
```

### Check Frontend

Query the status endpoint during analysis to see current progress:

```bash
curl http://localhost:8000/api/v1/analysis/{analysis_id}/status
```

Response shows:

- Current step being executed
- Progress percentage (10%, 20%, 50%, etc.)
- Timing data (if analysis is complete)

## Example Analysis Flow

### Step-by-Step Execution

```
Start Analysis
├─ 🟡 Initialize Agent (2.34s elapsed)
├─ 🟡 Fetch Transactions (47.57s elapsed) ← BitQuery throttling
├─ 🟡 Fetch Internal Transactions (55.72s elapsed)
├─ 🟡 Build Graph (58.93s elapsed)
├─ 🟡 Fetch Token Holders (60.82s elapsed)
├─ 🟡 Detect Patterns (76.49s elapsed) ← Pattern detection
├─ 🟡 Calculate Metrics (85.41s elapsed) ← PageRank computation
├─ 🟡 Convert Results (87.59s elapsed)
└─ ✅ Complete! (Total: 128.45s)
```

## Performance Optimization Tips

### If Analysis is Too Slow

1. **Reduce sample size**: Fetch fewer transactions (5000 instead of 10000)

   - May miss some patterns but faster analysis
   - Trade-off: Speed vs. Accuracy

2. **Reduce scope**: Use smaller time window (days_back=1 instead of 7)

   - Less historical data = less to process
   - May miss long-term patterns

3. **Check network**: Ensure good connection to BitQuery API

   - Steps 2-3 are API-dependent
   - Network latency directly impacts total time

4. **Token selection**: Analyze less complex tokens first
   - Tokens with fewer holders/transactions are faster
   - Start with established stablecoins to test

## Frontend Display

The frontend can display timing information:

```jsx
// Example: Show timing breakdown
<div className="timing-info">
  <h3>Analysis Timings</h3>
  <ul>
    {Object.entries(stepTimings).map(([step, time]) => (
      <li key={step}>
        {step}: {time}
      </li>
    ))}
  </ul>
  <strong>Total: {totalDuration}</strong>
</div>
```

## Implementation Details

### Code Changes

- **File**: `backend/app/services/analysis_service.py`
- **Import Added**: `import time`
- **Tracking**: `step_start = time.time()` before each operation
- **Storage**: Results stored in `analysis['stepTimings']`
- **Logging**: Each step logs with checkmark ✓ showing duration

### Timing Precision

- Measured in seconds with 2 decimal places (e.g., "45.23s")
- Includes I/O time (API calls, database operations)
- Does NOT include idle time waiting for other processes

---

**Status**: ✅ IMPLEMENTED

Timing feature is now active. Start an analysis and check `/api/v1/analysis/{id}/status` to see timing data!
