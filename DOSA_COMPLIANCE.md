# DOSA Compliance & Fail-Closed Pattern

## Overview

This document outlines how MSR Event Hub implements DOSA (Data Operations Security Assurance) compliance with a fail-closed security pattern for the India MVP launch.

**Status:** ✅ Implemented
**Launch Date:** January 24, 2026
**Compliance Framework:** DOSA + Microsoft RAI

---

## Fail-Closed Pattern

### Principle
**Fail-Closed:** When security controls fail or are uncertain, the system denies access rather than allowing potentially unsafe operations.

### Implementation

#### 1. Rate Limiting (Fail-Closed)
```python
# main.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
    strategy="fixed-window"
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    # FAIL-CLOSED: Log refusal + return 429
    log_refusal(
        refusal_reason="rate_limit_exceeded",
        query_context=f"{request.method} {request.url.path}",
        handler_name="rate_limiter"
    )
    return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
```

**Behavior:**
- ✅ Limit exceeded → 429 response + telemetry
- ✅ Rate limiter fails → Allows request but logs warning (graceful degradation)
- ✅ All refusals logged to Application Insights for audit

#### 2. Content Filtering (Fail-Closed)
```python
# Azure OpenAI content filters
if resp.status_code == 400:  # Content filter triggered
    log_refusal(
        refusal_reason="azure_openai_filter",
        query_context=detail[:200],
        handler_name="azure_openai_forward"
    )
    raise HTTPException(status_code=400, detail=detail)
```

**Behavior:**
- ✅ Content violation → Request blocked + logged
- ✅ Filter service unavailable → Fail-closed (no response generated)
- ✅ All filtered content logged for compliance audit

#### 3. Authentication (Fail-Closed via Bridge)
**Note:** Authentication handled by `msr-event-agent-bridge` (not in chat service)

Bridge implements:
- Microsoft Entra ID authentication
- DOSA-compliant session management
- User context forwarding via headers

**Chat Service:** Trusts forwarded headers from bridge (private network)

---

## Rate Limiting Details

### Limits (DOSA Compliant)

| Endpoint | Limit | Window | Enforcement |
|----------|-------|--------|-------------|
| `/api/chat/stream` | 20 req/min | Per IP | Fail-closed |
| `/api/chat/*` (other) | 100 req/min | Per IP | Fail-closed |
| Global default | 1000 req/hour | Per IP | Fail-closed |

### Configuration

**Environment Variables:**
```bash
# Redis for distributed rate limiting (production)
RATE_LIMIT_STORAGE_URI=redis://redis-cache.redis.cache.windows.net:6380?password=...&ssl=true

# In-memory for development (not distributed)
RATE_LIMIT_STORAGE_URI=memory://
```

**Storage Options:**
- **Production:** Redis (distributed, persistent)
- **Staging:** Redis or memory:// (testing)
- **Local Dev:** memory:// (single instance)

### Telemetry on Rate Limit

Every rate limit triggers:
1. **Refusal Log** (`ai_content_refusal`)
   - `refusal_reason` = "rate_limit_exceeded"
   - `query_context` = endpoint path
   - `user_id` = from x-user-id header (if present)

2. **Event** (`rate_limit_exceeded`)
   - `path` = endpoint
   - `method` = HTTP method
   - `remote_addr` = IP address
   - `user_agent` = browser/client

---

## Compliance Audit Trail

### What Gets Logged

#### ✅ All Refusals
- Content filter violations
- Rate limit exceeded
- Missing configuration
- Service unavailable

#### ✅ User Actions
- Chat queries (preview only, 100 chars)
- Feedback (thumbs up/down)
- Edit actions (accept/edit/reject)
- Event visits (pre/during/post)
- Connections initiated (email/repo/linkedin)

#### ✅ System Events
- Model inference (tokens, latency)
- API requests (duration, status)
- Errors and exceptions

### What Does NOT Get Logged

#### ❌ Full User Queries
- Only 100-character preview logged
- PII sanitized before logging

#### ❌ Model Responses
- Responses not logged (too large, privacy)
- Only metadata logged (token count, latency)

#### ❌ Credentials
- No API keys, passwords, or tokens in logs
- All secrets in Azure Key Vault

---

## KQL Queries for Compliance Audit

### Monthly Refusal Report
```kusto
customEvents
| where name == "ai_content_refusal"
| where timestamp between(startofmonth(now()) .. now())
| summarize 
    total_refusals=count(),
    by_reason=make_bag(pack(tostring(customDimensions.refusal_reason), count()))
| project total_refusals, by_reason
```

### Rate Limit Compliance Check
```kusto
customEvents
| where name == "rate_limit_exceeded"
| where timestamp > ago(7d)
| summarize count() by bin(timestamp, 1h), tostring(customDimensions.path)
| render timechart
```

### Content Filter Effectiveness
```kusto
customEvents
| where name == "ai_content_refusal"
| where customDimensions.refusal_reason == "azure_openai_filter"
| where timestamp > ago(30d)
| summarize count() by bin(timestamp, 1d)
| render timechart
```

### User Impact Analysis
```kusto
let total_requests = requests
    | where timestamp > ago(1h)
    | where name == "POST /api/chat/stream"
    | count;
let refusals = customEvents
    | where timestamp > ago(1h)
    | where name == "ai_content_refusal"
    | count;
print 
    total_requests,
    refusals,
    refusal_rate_pct=refusals*100.0/total_requests,
    compliance_status=iff(refusals*100.0/total_requests < 5, "✅ COMPLIANT", "⚠️ HIGH REFUSAL RATE")
```

---

## Security Controls

### 1. Transport Security
- ✅ HTTPS enforced (no HTTP)
- ✅ TLS 1.2+ required
- ✅ Azure App Service managed certificates

### 2. Input Validation
- ✅ Request size limits (FastAPI default: 16MB)
- ✅ JSON schema validation (Pydantic models)
- ✅ Rate limiting per endpoint

### 3. Output Filtering
- ✅ Azure OpenAI content filters
- ✅ PII sanitization in logs
- ✅ Error message sanitization (no stack traces to users)

### 4. Monitoring & Alerting
- ✅ Real-time refusal tracking
- ✅ Rate limit alerts (>5% requests limited)
- ✅ Error rate alerts (>1% errors)
- ✅ Latency alerts (P99 >3s)

---

## Incident Response

### High Rate Limit Events

**Trigger:** >100 rate limit events in 1 hour
**Action:**
1. Check Application Insights for source IPs
2. Verify legitimate traffic vs. attack
3. If attack: Add IP to Azure Front Door WAF blocklist
4. If legitimate: Consider increasing limits

### Content Filter Spike

**Trigger:** >50 content filter refusals in 1 hour
**Action:**
1. Review query patterns in Application Insights
2. Check for coordinated abuse
3. Notify security team if malicious
4. Document patterns for model training

### Compliance Violation

**Trigger:** Audit finds logging gap
**Action:**
1. Immediate code fix to log missing events
2. Deploy hotfix to production
3. Backfill audit trail if possible
4. Update compliance documentation

---

## Production Readiness

### Pre-Launch Checklist
- [x] Rate limiting implemented with fail-closed
- [x] All refusals logged to Application Insights
- [x] Content filters configured (medium sensitivity)
- [x] HTTPS enforced
- [x] Monitoring dashboard created
- [x] Alerts configured
- [ ] Security review completed (in progress)
- [ ] Compliance sign-off (pending)

### Post-Launch Monitoring (First 30 Days)
- **Daily:** Review refusal rate and patterns
- **Weekly:** Audit rate limit effectiveness
- **Monthly:** Compliance report for stakeholders

---

## Contact

**Compliance Questions:** [email protected]
**Security Incidents:** [email protected]
**Platform Team:** [email protected]

**Last Updated:** January 21, 2026
**Next Review:** Post-MVP (February 1, 2026)
