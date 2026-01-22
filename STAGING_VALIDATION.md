# Staging Validation Checklist - India MVP (Jan 24)

## Overview
This checklist validates all critical MVP requirements before production deployment.

**Target Date:** January 24, 2026
**Environment:** Staging (https://msr-eventhub-chat-staging.azurewebsites.net)
**Sign-off Required:** Platform Team Lead

---

## ✅ Telemetry Events Validation

### Priority 1: Compliance Events (MUST PASS)

#### 1.1 AI Content Refusal (`ai_content_refusal`)
- [ ] **Trigger:** Submit query that violates content policy
- [ ] **Verify:** Event appears in Application Insights within 60s
- [ ] **Check Properties:**
  - `refusal_reason` = "azure_openai_filter" or "rate_limit"
  - `query_context` contains truncated query
  - `handler_name` is populated
  - `conversation_id` matches session
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "ai_content_refusal"
| where timestamp > ago(1h)
| project timestamp, customDimensions.refusal_reason, customDimensions.handler_name
```

#### 1.2 AI Edit Action (`ai_edit_action`)
- [ ] **Trigger:** POST to `/api/chat/telemetry/edit-action` with action="accept"
- [ ] **Verify:** Event logged with action type
- [ ] **Check Properties:**
  - `action` = "accept", "edit", or "reject"
  - `conversation_id` present
  - `edit_percentage` (if action=edit)
- [ ] **Test Cases:**
  - Accept: 100% acceptance
  - Edit: 50% edited
  - Reject: Full rejection
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "ai_edit_action"
| where timestamp > ago(1h)
| summarize count() by tostring(customDimensions.action)
```

#### 1.3 Rate Limit Exceeded (`rate_limit_exceeded`)
- [ ] **Trigger:** Send >20 requests/minute to `/api/chat/stream`
- [ ] **Verify:** 429 response after limit
- [ ] **Check Response:**
  - Status code = 429
  - `Retry-After` header present
  - Error message clear
- [ ] **Check Telemetry:**
  - Event logged with path, method, remote_addr
  - Linked to `ai_content_refusal` with reason="rate_limit"
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "rate_limit_exceeded"
| where timestamp > ago(1h)
| project timestamp, customDimensions.path, customDimensions.remote_addr
```

---

### Priority 2: User Engagement Events

#### 2.1 Event Visit (`event_visit`)
- [ ] **Trigger:** POST to `/api/chat/telemetry/event-visit`
- [ ] **Verify:** Event logged with visit_type
- [ ] **Test Cases:**
  - `pre_event` visit
  - `during_event` visit
  - `post_event` visit
- [ ] **Check Properties:**
  - `event_id` populated
  - `visit_type` correct
  - `session_duration_seconds` (if applicable)
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "event_visit"
| where timestamp > ago(1h)
| summarize count() by tostring(customDimensions.visit_type)
```

#### 2.2 Connection Initiated (`connection_initiated`)
- [ ] **Trigger:** POST to `/api/chat/telemetry/connection`
- [ ] **Verify:** Event logged with connection_type
- [ ] **Test Cases:**
  - Email presenter
  - Visit repository
  - LinkedIn connection
- [ ] **Check Properties:**
  - `connection_type` correct
  - `target_id` populated
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "connection_initiated"
| where timestamp > ago(1h)
| summarize count() by tostring(customDimensions.connection_type)
```

#### 2.3 Bookmark Action (`bookmark_action`)
- [ ] **Trigger:** Submit card action with `action: "bookmark"`
- [ ] **Verify:** Event logged (even though stub)
- [ ] **Check Properties:**
  - `item_type` present
  - `item_id` present
  - `action_type` = "bookmark"
- [ ] **Note:** Full persistence deferred to Phase 2
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "bookmark_action"
| where timestamp > ago(1h)
| project timestamp, customDimensions.item_type, customDimensions.item_id
```

---

### Priority 3: Routing Quality Events (NEW)

#### 3.1 Intent Classification (`intent_classification`)
- [ ] **Trigger:** Natural language query to `/api/chat/stream`
- [ ] **Verify:** Every query logged
- [ ] **Check Properties:**
  - `predicted_intent` present
  - `confidence` measurement recorded
  - `execution_path` = deterministic/llm_assisted/full_llm
  - `is_deterministic` boolean
- [ ] **Target:** >70% deterministic coverage
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(1h)
| summarize 
    total=count(),
    deterministic=countif(customDimensions.is_deterministic == "True")
| project deterministic_pct=deterministic*100.0/total
```

#### 3.2 Intent Feedback (`intent_feedback`)
- [ ] **Trigger:** Click thumbs up/down in chat UI
- [ ] **Verify:** Feedback logged
- [ ] **Check Properties:**
  - `feedback_type` = positive/negative/correction
  - `query_preview` present
- [ ] **KQL Query:**
```kusto
customEvents
| where name == "intent_feedback"
| where timestamp > ago(1h)
| summarize count() by tostring(customDimensions.feedback_type)
```

---

## ✅ Performance & Stability

### Load Test Validation

#### 4.1 MVP Load Test (CRITICAL)
- [ ] **Setup:** Install locust: `pip install -r tests/load/requirements.txt`
- [ ] **Run:** 
```bash
locust -f tests/load/locustfile.py \
    --host=https://msr-eventhub-chat-staging.azurewebsites.net \
    --users 1000 \
    --spawn-rate 10 \
    --run-time 30m \
    --headless \
    --html staging-load-test.html
```
- [ ] **Success Criteria:**
  - P99 latency < 2000ms ✅
  - Success rate > 99% ✅
  - Total RPS ~2000 ✅
  - No 500 errors
  - Rate limiting working (429s expected if >20 rps per IP)
- [ ] **Application Insights During Test:**
```kusto
requests
| where timestamp > ago(30m)
| summarize 
    p99=percentile(duration, 99),
    success_rate=100.0*countif(success==true)/count(),
    rps=count()/1800.0
```

#### 4.2 Latency Baseline
- [ ] **Measure:** `/api/chat/stream` P50, P95, P99
- [ ] **Target:** P99 < 2s
- [ ] **Check Cold Start:** First request after idle
- [ ] **KQL Query:**
```kusto
requests
| where name == "POST /api/chat/stream"
| where timestamp > ago(1h)
| summarize 
    p50=percentile(duration, 50),
    p95=percentile(duration, 95),
    p99=percentile(duration, 99)
```

---

## ✅ Compliance & Security

### 5.1 DOSA Fail-Closed
- [ ] **Rate Limiting:** Enforced at 20 req/min per IP
- [ ] **Error Handling:** 429 with clear message
- [ ] **Telemetry:** All refusals logged
- [ ] **Retry-After:** Header present in 429 responses

### 5.2 Content Filtering
- [ ] **Azure OpenAI Filters:** Enabled (hate/violence/sexual/self-harm = medium)
- [ ] **Refusal Logging:** All filtered content logged
- [ ] **User Message:** Clear, non-technical error message

### 5.3 PII Sanitization
- [ ] **Telemetry:** Query previews truncated to 100 chars
- [ ] **Logs:** No full queries with PII in logs
- [ ] **Test:** Submit query with email, phone number - verify sanitized

---

## ✅ Accessibility & UI

### 6.1 Accessibility Tests
- [ ] **Run Tests:** `cd web/chat && npm test`
- [ ] **All Pass:** No critical accessibility violations
- [ ] **Keyboard Nav:** Tab through chat interface
- [ ] **Screen Reader:** Test with NVDA/JAWS (basic navigation)
- [ ] **Test Cases:**
  - Welcome card: ARIA labels present
  - Project cards: Keyboard accessible
  - Feedback buttons: Labeled correctly

### 6.2 Feedback UI
- [ ] **Visible:** Thumbs up/down on assistant messages
- [ ] **Functional:** Click triggers API call
- [ ] **Thank You:** Confirmation message appears
- [ ] **Network:** Verify POST to `/api/chat/intent-feedback`

---

## ✅ API Endpoints Health

### 7.1 Core Endpoints
- [ ] `GET /api/chat/health` - 200 OK
- [ ] `GET /api/chat/welcome` - Returns adaptive card
- [ ] `POST /api/chat/stream` - Streaming response
- [ ] `GET /api/chat/config` - Returns routing config
- [ ] `GET /api/chat/metrics/routing-quality` - Returns coverage stats

### 7.2 Telemetry Endpoints
- [ ] `POST /api/chat/feedback` - Records user feedback
- [ ] `POST /api/chat/intent-feedback` - Records intent feedback
- [ ] `POST /api/chat/telemetry/event-visit` - Records visits
- [ ] `POST /api/chat/telemetry/connection` - Records connections
- [ ] `POST /api/chat/telemetry/edit-action` - Records edits

---

## ✅ Monitoring Dashboard

### 8.1 Application Insights Workbook
- [ ] **Created:** Azure Monitor Workbook with 10 key metrics
- [ ] **Tiles:**
  1. Deterministic Coverage (target >80%)
  2. Intent Distribution (pie chart)
  3. User Satisfaction (thumbs up/down ratio)
  4. Refusal Rate (target <1%)
  5. Edit Acceptance Rate
  6. Event Visits (pre/during/post)
  7. Connection/Leads Initiated
  8. Rate Limit Events
  9. P99 Latency Trend
  10. Error Rate

### 8.2 Alerts Configured
- [ ] **Deterministic Coverage <70%** (1 hour window)
- [ ] **Refusal Rate >5%** (1 hour window)
- [ ] **P99 Latency >3s** (15 min window)
- [ ] **Error Rate >1%** (15 min window)

---

## 📋 Pre-Launch Checklist

### Documentation
- [ ] ACCESSIBILITY.md reviewed
- [ ] ROUTING_QUALITY_IMPLEMENTATION.md complete
- [ ] APPLICATION_INSIGHTS_ROUTING_DASHBOARD.md queries validated
- [ ] Load test README.md clear

### Environment Variables
- [ ] `APPLICATIONINSIGHTS_CONNECTION_STRING` set
- [ ] `AZURE_OPENAI_ENDPOINT` configured
- [ ] `AZURE_OPENAI_DEPLOYMENT` specified
- [ ] `RATE_LIMIT_STORAGE_URI` set (Redis or memory://)

### Deployment
- [ ] All environment secrets in Azure Key Vault
- [ ] Managed identity has required RBAC roles
- [ ] App Service scaled to appropriate tier (P2V3 or higher for 1000 users)
- [ ] Auto-scaling configured

---

## 🎯 Go/No-Go Decision Matrix

| Criterion | Status | Blocker? |
|-----------|--------|----------|
| Telemetry wired (refusal, edit, visit, connection) | ☐ | YES |
| Load test passed (P99 <2s, 1000 users, 30 min) | ☐ | YES |
| Rate limiting enforced (20/min) | ☐ | YES |
| Accessibility tests passing | ☐ | NO (can launch with warnings) |
| Dashboard created | ☐ | NO (can create post-launch) |
| All endpoints 200 OK | ☐ | YES |

**Sign-off:**
- [ ] Platform Team Lead: _________________
- [ ] Date: _________________
- [ ] Decision: GO / NO-GO

---

## Post-Validation Actions

### If GO:
1. Deploy to production
2. Run smoke test (100 users, 5 min)
3. Monitor for first 2 hours
4. Weekly review scheduled

### If NO-GO:
1. Document blocking issues
2. Create fix tickets
3. Re-run validation after fixes
4. Reschedule launch

---

**Last Updated:** January 21, 2026
**Next Review:** Post-MVP (Feb 1, 2026)
