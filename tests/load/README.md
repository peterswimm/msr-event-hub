# Load Testing for MSR Event Hub

## Quick Start

### 1. Install Dependencies
```bash
pip install -r tests/load/requirements.txt
```

### 2. Run Load Test (Web UI)
```bash
# Start Locust web interface
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure: 1000 users, spawn rate 10/sec, run 30 min
```

### 3. Run Headless (CI/CD)
```bash
# MVP test: 1000 users @ 2 rps for 30 min
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 1000 \
    --spawn-rate 10 \
    --run-time 30m \
    --headless \
    --html report.html

# Check report.html for results
```

## MVP Requirements

**Target:** 1000 concurrent users @ 2 rps/user for 30 minutes

**Success Criteria:**
- ✅ P99 latency < 2000ms
- ✅ Success rate > 99%
- ✅ Total RPS ~2000 (1000 users × 2 rps)

## Test Scenarios

### Normal Load (ChatUser)
Simulates typical user behavior:
- 70% natural language queries
- 30% card actions
- 2 requests per second per user
- Feedback submission
- Metrics checking

### Stress Test (StressTestUser)
High-intensity load testing:
- 5-10 rps per user
- Tests rate limiting
- Use separately: `locust -f tests/load/locustfile.py --host=http://localhost:8000 --class-picker`

## Quick Validation Test

For rapid iteration during development:

```bash
# Light load: 10 users, 1 minute
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 10 \
    --spawn-rate 2 \
    --run-time 1m \
    --headless
```

## Staging Environment Test

```bash
# Against staging
locust -f tests/load/locustfile.py \
    --host=https://msr-eventhub-chat-staging.azurewebsites.net \
    --users 1000 \
    --spawn-rate 10 \
    --run-time 30m \
    --headless \
    --html staging-report.html
```

## Production Pre-Launch Test

```bash
# Final validation before India MVP
locust -f tests/load/locustfile.py \
    --host=https://msr-eventhub-chat-prod.azurewebsites.net \
    --users 1000 \
    --spawn-rate 10 \
    --run-time 30m \
    --headless \
    --html prod-validation.html

# Review report.html - ensure all MVP criteria pass
```

## Monitoring During Load Test

Watch Application Insights during test:

```kusto
// Real-time latency
requests
| where timestamp > ago(5m)
| summarize 
    p50=percentile(duration, 50),
    p95=percentile(duration, 95),
    p99=percentile(duration, 99),
    rps=count()/300.0
| project p50, p95, p99, rps

// Error rate
requests
| where timestamp > ago(5m)
| summarize 
    total=count(),
    errors=countif(success == false)
| project error_rate=errors*100.0/total
```

## Troubleshooting

### High Latency
- Check Application Insights for slow dependencies
- Review Azure OpenAI throttling
- Check database connection pool

### High Error Rate
- Check rate limiting (429 errors)
- Review Application Insights exceptions
- Verify Azure services health

### Low RPS
- Increase spawn rate
- Check network bandwidth
- Verify Locust worker count
