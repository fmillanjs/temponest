# Critical Flows Manual Testing Guide

**Purpose**: Validate critical user journeys work end-to-end
**When to Use**: Pre-deployment (staging), Post-deployment (production), Regression testing
**Time Required**: ~45 minutes for full suite

---

## Testing Environment Setup

### Test Accounts

**Admin User**:
- Email: `admin-test@temponest.io`
- Password: `[From password manager]`
- Permissions: All

**Standard User**:
- Email: `user-test@temponest.io`
- Password: `[From password manager]`
- Permissions: Limited

**Create Fresh Test User** (for registration flow):
```bash
# Generate unique email
TEST_EMAIL="test-$(date +%s)@example.com"
echo "Test email: $TEST_EMAIL"
```

### Test Data Cleanup

```bash
# Before testing, clean up old test data
docker exec postgres psql -U postgres -d agentic -c "
  DELETE FROM task_executions WHERE task_description LIKE '%TEST:%';
  DELETE FROM scheduled_tasks WHERE name LIKE '%TEST:%';
  DELETE FROM webhooks WHERE url LIKE '%webhook.site%';
"
```

---

## Flow 1: User Authentication & Authorization

### Estimated Time: 5 minutes

#### 1.1 User Registration

**Steps**:
1. Navigate to: `https://[environment]/register`
2. Fill in registration form:
   - Email: `[Fresh email address]`
   - Password: `TestPass123!`
   - Confirm Password: `TestPass123!`
   - Accept Terms: ✅
3. Click "Register"

**Expected Results**:
- ✅ Registration succeeds (status 201)
- ✅ Confirmation email sent (check email or logs)
- ✅ Redirected to dashboard or login page
- ✅ User record created in database

**Verification**:
```bash
# Check user was created
docker exec postgres psql -U postgres -d agentic -c \
  "SELECT email, created_at FROM users WHERE email = '[test-email]';"
```

**Failure Scenarios to Test**:
- [ ] Duplicate email → Shows error "Email already registered"
- [ ] Weak password → Shows error "Password too weak"
- [ ] Mismatched passwords → Shows error "Passwords don't match"

#### 1.2 User Login

**Steps**:
1. Navigate to: `https://[environment]/login`
2. Enter credentials:
   - Email: `admin-test@temponest.io`
   - Password: `[Admin password]`
3. Click "Login"

**Expected Results**:
- ✅ Login succeeds
- ✅ JWT token issued
- ✅ Redirected to dashboard
- ✅ User info displayed in header

**Verification**:
```bash
# Check JWT token in browser DevTools → Application → Cookies
# Token should be present and valid
```

**Failure Scenarios to Test**:
- [ ] Wrong password → Shows error "Invalid credentials"
- [ ] Non-existent email → Shows error "User not found"
- [ ] Account locked → Shows error "Account locked"

#### 1.3 Token Refresh

**Steps**:
1. After login, wait 5 minutes (token near expiry)
2. Make an API request
3. Observe token refresh

**Expected Results**:
- ✅ Token automatically refreshed
- ✅ No session interruption
- ✅ New token issued

#### 1.4 Permissions Check

**Steps**:
1. Login as standard user
2. Attempt to access admin-only feature
3. Observe permission denial

**Expected Results**:
- ✅ Access denied (403)
- ✅ Error message: "Insufficient permissions"

#### 1.5 Logout

**Steps**:
1. Click user menu → Logout
2. Attempt to access protected page

**Expected Results**:
- ✅ User logged out
- ✅ JWT token removed
- ✅ Redirected to login
- ✅ Protected pages inaccessible

---

## Flow 2: Agent Execution (Core Feature)

### Estimated Time: 10 minutes

#### 2.1 Simple Agent Execution

**Steps**:
1. Navigate to: `https://[environment]/agents`
2. Select agent type: **"Developer"**
3. Fill in task form:
   ```
   Task Description: TEST: Create a Python function to calculate fibonacci numbers
   Priority: Normal
   Max Tokens: 2000
   ```
4. Click "Execute"

**Expected Results**:
- ✅ Task created (status 201)
- ✅ Task ID returned
- ✅ Status: "queued"
- ✅ Execution starts within 10 seconds
- ✅ Status updates to "running"
- ✅ Status updates to "completed" (30-60 seconds)
- ✅ Output contains Python code
- ✅ Cost calculated and recorded

**Real-Time Monitoring**:
```bash
# Watch execution progress
watch -n 2 'curl -s http://localhost:9000/agents/executions/[task-id] | jq ".status,.output"'
```

**Verification**:
```bash
# Check execution in database
docker exec postgres psql -U postgres -d agentic -c \
  "SELECT status, agent_name, total_tokens, total_cost_usd
   FROM task_executions WHERE task_id = '[task-id]';"

# Expected:
# status: completed
# agent_name: developer
# total_tokens: > 0
# total_cost_usd: > 0
```

#### 2.2 Agent Execution with Context/Memory

**Steps**:
1. Create first execution:
   ```
   Task: TEST: Explain what is Docker
   Agent: Developer
   ```
2. Wait for completion
3. Create follow-up execution:
   ```
   Task: TEST: Now explain Docker Compose
   Agent: Developer
   Context: [Reference first task ID]
   ```

**Expected Results**:
- ✅ Second task references first task's context
- ✅ Agent provides coherent follow-up answer
- ✅ Context preserved in memory

#### 2.3 Agent Execution with Citations/RAG

**Steps**:
1. Upload a document to knowledge base (if implemented)
2. Execute task that references the document:
   ```
   Task: TEST: Summarize the uploaded document about [topic]
   Agent: Developer
   Use RAG: ✅
   ```

**Expected Results**:
- ✅ Agent retrieves relevant context from vector DB
- ✅ Response includes citations
- ✅ Citations link to source documents

#### 2.4 Concurrent Executions

**Steps**:
1. Trigger 5 agent executions simultaneously:
   ```bash
   for i in {1..5}; do
     curl -X POST http://localhost:9000/agents/execute \
       -H "Authorization: Bearer $TOKEN" \
       -H "Content-Type: application/json" \
       -d '{
         "agent_type": "developer",
         "task": "TEST: Generate random number '$i'",
         "tenant_id": "'$TENANT_ID'"
       }' &
   done
   wait
   ```

**Expected Results**:
- ✅ All 5 tasks accepted
- ✅ Tasks queued properly
- ✅ Tasks execute in parallel (if workers available)
- ✅ No race conditions or deadlocks
- ✅ All tasks complete successfully

#### 2.5 Agent Execution Failure Handling

**Steps**:
1. Create execution with invalid input:
   ```
   Task: [Empty or invalid]
   Agent: [Invalid agent name]
   ```

**Expected Results**:
- ✅ Validation error returned (400)
- ✅ Clear error message
- ✅ No task created

2. Create execution that will timeout:
   ```
   Task: TEST: Generate 100000 lines of code
   Max Tokens: 50
   ```

**Expected Results**:
- ✅ Task starts
- ✅ Timeout after configured limit
- ✅ Status: "failed"
- ✅ Error message: "Timeout exceeded"

---

## Flow 3: Dashboard & Metrics

### Estimated Time: 5 minutes

#### 3.1 Dashboard Load

**Steps**:
1. Navigate to: `https://[environment]/dashboard`
2. Wait for dashboard to load

**Expected Results**:
- ✅ Page loads within 3 seconds
- ✅ All metrics displayed:
  - Total executions
  - Total cost
  - Total tokens
  - Success rate
- ✅ Charts render correctly
- ✅ No console errors

**Performance Check**:
```bash
# Measure dashboard load time
curl -w "@curl-format.txt" -o /dev/null -s https://[environment]/dashboard
# Expected: time_total < 3 seconds
```

#### 3.2 Date Range Filtering

**Steps**:
1. On dashboard, select date range:
   - Start: 7 days ago
   - End: Today
2. Click "Apply Filter"

**Expected Results**:
- ✅ Metrics update within 2 seconds
- ✅ Data filtered correctly
- ✅ Charts update
- ✅ No 500 errors (this was the bug we fixed!)

**Verification**:
```bash
# Check API response
curl -s "http://localhost:8082/api/costs/summary?start_date=2025-11-06&end_date=2025-11-13" | jq

# Expected: Valid JSON with metrics
```

#### 3.3 Export Metrics

**Steps**:
1. Click "Export" button
2. Select format: CSV or JSON
3. Download file

**Expected Results**:
- ✅ File downloads successfully
- ✅ Data formatted correctly
- ✅ All metrics included

---

## Flow 4: Scheduled Tasks

### Estimated Time: 10 minutes

#### 4.1 Create Scheduled Task

**Steps**:
1. Navigate to: `https://[environment]/scheduler`
2. Click "New Schedule"
3. Fill in form:
   ```
   Name: TEST: Hourly Health Check
   Description: Check system health every hour
   Cron Schedule: 0 * * * * (every hour)
   Agent Type: Developer
   Task: Check if all services are running and report status
   Enabled: ✅
   ```
4. Click "Save"

**Expected Results**:
- ✅ Schedule created (status 201)
- ✅ Schedule appears in list
- ✅ Status: "Active"
- ✅ Next run time calculated correctly

**Verification**:
```bash
# Check schedule in database
docker exec postgres psql -U postgres -d agentic -c \
  "SELECT name, cron_schedule, enabled, next_run
   FROM scheduled_tasks WHERE name LIKE 'TEST:%';"
```

#### 4.2 Trigger Manual Run

**Steps**:
1. Find the test schedule in list
2. Click "Run Now" button

**Expected Results**:
- ✅ Execution triggered immediately
- ✅ Status updates to "running"
- ✅ Execution completes
- ✅ Result stored
- ✅ Next scheduled run unaffected

#### 4.3 Wait for Automatic Trigger

**Steps**:
1. Create schedule with cron: `* * * * *` (every minute)
2. Wait 1-2 minutes
3. Check execution history

**Expected Results**:
- ✅ Task executes automatically at scheduled time
- ✅ Multiple executions visible in history
- ✅ Each execution tracked separately

**Verification**:
```bash
# Check recent executions
docker exec postgres psql -U postgres -d agentic -c \
  "SELECT scheduled_task_id, status, started_at, completed_at
   FROM task_executions
   WHERE scheduled_task_id = '[schedule-id]'
   ORDER BY started_at DESC LIMIT 5;"
```

#### 4.4 Update Schedule

**Steps**:
1. Edit existing schedule
2. Change cron to: `0 */2 * * *` (every 2 hours)
3. Save changes

**Expected Results**:
- ✅ Schedule updated
- ✅ Next run time recalculated
- ✅ Old schedule invalidated

#### 4.5 Disable Schedule

**Steps**:
1. Toggle "Enabled" switch to OFF
2. Save

**Expected Results**:
- ✅ Schedule disabled
- ✅ No future executions triggered
- ✅ Can be re-enabled later

#### 4.6 Delete Schedule

**Steps**:
1. Click "Delete" on test schedule
2. Confirm deletion

**Expected Results**:
- ✅ Schedule deleted from database
- ✅ Historical executions preserved
- ✅ No future executions

**Cleanup**:
```bash
# Remove all test schedules
docker exec postgres psql -U postgres -d agentic -c \
  "DELETE FROM scheduled_tasks WHERE name LIKE 'TEST:%';"
```

---

## Flow 5: Webhooks

### Estimated Time: 10 minutes

#### 5.1 Create Webhook Subscription

**Setup**:
1. Go to https://webhook.site
2. Copy your unique URL

**Steps**:
1. Navigate to: `https://[environment]/webhooks`
2. Click "New Webhook"
3. Fill in form:
   ```
   Name: TEST: Execution Completed Webhook
   URL: https://webhook.site/[your-unique-id]
   Events: ["agent.execution.completed", "agent.execution.failed"]
   Enabled: ✅
   ```
4. Click "Save"

**Expected Results**:
- ✅ Webhook created
- ✅ Appears in webhook list
- ✅ Status: "Active"

#### 5.2 Trigger Webhook Event

**Steps**:
1. Create and complete an agent execution
2. Wait 5-10 seconds for webhook delivery
3. Check webhook.site for incoming request

**Expected Results**:
- ✅ Webhook delivered to webhook.site
- ✅ Delivery time < 5 seconds
- ✅ Payload includes:
  - Event type
  - Timestamp
  - Task ID
  - Status
  - Output (if completed)
  - Error (if failed)
- ✅ Headers include signature (if configured)

**Verification**:
```bash
# Check webhook delivery in database
docker exec postgres psql -U postgres -d agentic -c \
  "SELECT webhook_id, status, response_code, attempts, delivered_at
   FROM webhook_deliveries
   WHERE webhook_id = '[webhook-id]'
   ORDER BY created_at DESC LIMIT 5;"

# Expected:
# status: delivered
# response_code: 200
# attempts: 1
```

#### 5.3 Webhook Retry on Failure

**Steps**:
1. Create webhook with invalid URL:
   ```
   URL: https://invalid-domain-12345.com/webhook
   ```
2. Trigger event
3. Wait for retry attempts

**Expected Results**:
- ✅ Initial delivery fails (connection error)
- ✅ Status: "pending"
- ✅ Retry scheduled
- ✅ Multiple retry attempts made (exponential backoff)
- ✅ After max retries, status: "failed"

**Verification**:
```bash
# Check retry attempts
docker exec postgres psql -U postgres -d agentic -c \
  "SELECT id, status, attempts, last_attempt_at, error_message
   FROM webhook_deliveries
   WHERE status IN ('pending', 'failed')
   ORDER BY created_at DESC LIMIT 5;"
```

#### 5.4 Webhook Rate Limiting

**Steps**:
1. Trigger 100 events rapidly:
   ```bash
   for i in {1..100}; do
     # Create execution to trigger webhooks
     curl -X POST http://localhost:9000/agents/execute [...] &
   done
   wait
   ```

**Expected Results**:
- ✅ Webhooks queued properly
- ✅ No more than 10 concurrent deliveries
- ✅ All eventually delivered
- ✅ No overwhelming of webhook endpoint

#### 5.5 Delete Webhook

**Steps**:
1. Click "Delete" on test webhook
2. Confirm deletion

**Expected Results**:
- ✅ Webhook deleted
- ✅ No future deliveries
- ✅ Historical deliveries preserved

**Cleanup**:
```bash
# Remove test webhooks
docker exec postgres psql -U postgres -d agentic -c \
  "DELETE FROM webhooks WHERE url LIKE '%webhook.site%';"
```

---

## Flow 6: Cost Tracking & Budgets

### Estimated Time: 5 minutes

#### 6.1 View Cost Summary

**Steps**:
1. Navigate to: `https://[environment]/costs`
2. View cost summary

**Expected Results**:
- ✅ Total cost displayed
- ✅ Cost by agent type
- ✅ Cost by model
- ✅ Cost trend chart
- ✅ Token usage breakdown

#### 6.2 Cost by Date Range

**Steps**:
1. Select date range: Last 30 days
2. Apply filter

**Expected Results**:
- ✅ Costs filtered by date
- ✅ Chart updates
- ✅ Summary recalculated

#### 6.3 Export Cost Report

**Steps**:
1. Click "Export Report"
2. Select format: CSV
3. Download

**Expected Results**:
- ✅ CSV file downloads
- ✅ Contains all cost data
- ✅ Properly formatted

#### 6.4 Budget Alert (If Implemented)

**Steps**:
1. Set budget limit: $10
2. Trigger executions until approaching limit
3. Check for alert

**Expected Results**:
- ✅ Alert triggered at 80% of budget
- ✅ Warning displayed in UI
- ✅ Notification sent (email/Slack)
- ✅ Executions blocked at 100% (optional)

---

## Flow 7: Error Handling & Edge Cases

### Estimated Time: 5 minutes

#### 7.1 Network Error Simulation

**Steps**:
1. Disconnect network
2. Attempt to create execution
3. Reconnect network

**Expected Results**:
- ✅ Clear error message: "Network error"
- ✅ UI remains functional
- ✅ Retry button available
- ✅ After reconnect, retry succeeds

#### 7.2 Session Expiry

**Steps**:
1. Login
2. Wait for token expiry (or manually delete cookie)
3. Attempt protected action

**Expected Results**:
- ✅ Session expired message
- ✅ Redirect to login
- ✅ After login, return to original page

#### 7.3 Large Payload Handling

**Steps**:
1. Create execution with very large task description:
   ```
   Task: [10,000+ characters]
   ```

**Expected Results**:
- ✅ Validation error if exceeds limit
- ✅ Or: Task created and handled properly
- ✅ No server crash

#### 7.4 Concurrent User Actions

**Steps**:
1. Open 2 browser windows with same user
2. Perform actions in both simultaneously

**Expected Results**:
- ✅ Both sessions work independently
- ✅ No race conditions
- ✅ Data consistency maintained

---

## Test Results Template

### Execution Report

```markdown
# Critical Flows Test Report

**Date**: [Date]
**Environment**: [staging/production]
**Tester**: [Name]
**Build Version**: v1.8.0

## Summary
- **Total Flows**: 7
- **Tests Passed**: __/45
- **Tests Failed**: __/45
- **Tests Skipped**: __/45
- **Overall Result**: PASS / FAIL

## Detailed Results

### Flow 1: Authentication ✅ / ❌
- Registration: ✅ / ❌ [Notes]
- Login: ✅ / ❌ [Notes]
- Token Refresh: ✅ / ❌ [Notes]
- Permissions: ✅ / ❌ [Notes]
- Logout: ✅ / ❌ [Notes]

### Flow 2: Agent Execution ✅ / ❌
- Simple Execution: ✅ / ❌ [Notes]
- With Context: ✅ / ❌ [Notes]
- With RAG: ✅ / ❌ [Notes]
- Concurrent: ✅ / ❌ [Notes]
- Failure Handling: ✅ / ❌ [Notes]

### Flow 3: Dashboard & Metrics ✅ / ❌
- Dashboard Load: ✅ / ❌ [Notes]
- Date Filtering: ✅ / ❌ [Notes]
- Export: ✅ / ❌ [Notes]

### Flow 4: Scheduled Tasks ✅ / ❌
- Create: ✅ / ❌ [Notes]
- Manual Trigger: ✅ / ❌ [Notes]
- Auto Trigger: ✅ / ❌ [Notes]
- Update: ✅ / ❌ [Notes]
- Disable: ✅ / ❌ [Notes]
- Delete: ✅ / ❌ [Notes]

### Flow 5: Webhooks ✅ / ❌
- Create: ✅ / ❌ [Notes]
- Trigger: ✅ / ❌ [Notes]
- Retry: ✅ / ❌ [Notes]
- Rate Limiting: ✅ / ❌ [Notes]
- Delete: ✅ / ❌ [Notes]

### Flow 6: Cost Tracking ✅ / ❌
- View Summary: ✅ / ❌ [Notes]
- Date Filter: ✅ / ❌ [Notes]
- Export: ✅ / ❌ [Notes]
- Budget Alert: ✅ / ❌ [Notes]

### Flow 7: Error Handling ✅ / ❌
- Network Error: ✅ / ❌ [Notes]
- Session Expiry: ✅ / ❌ [Notes]
- Large Payload: ✅ / ❌ [Notes]
- Concurrent Actions: ✅ / ❌ [Notes]

## Issues Found

| # | Flow | Severity | Description | Status |
|---|------|----------|-------------|--------|
| 1 | [Flow] | Critical/High/Medium/Low | [Description] | Open/Fixed |

## Recommendations

1. [Recommendation]
2. [Recommendation]

## Sign-Off

**Testing Complete**: ☐ YES ☐ NO
**Ready for Production**: ☐ YES ☐ NO (reason: ______)

**Tester Signature**: _______________ Date: _______
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Owner**: QA Team
**Next Review**: Before each deployment
