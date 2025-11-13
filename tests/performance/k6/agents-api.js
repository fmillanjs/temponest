/**
 * K6 Load Test for TempoNest Agents API
 *
 * Usage:
 *   k6 run tests/performance/k6/agents-api.js
 *   k6 run --vus 20 --duration 3m tests/performance/k6/agents-api.js
 *   k6 run tests/performance/k6/agents-api.js --out json=reports/agents-api-results.json
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const agentCreationRate = new Rate('agent_creation_success');
const agentListDuration = new Trend('agent_list_duration');
const agentExecutionDuration = new Trend('agent_execution_duration');
const agentCounter = new Counter('agents_created');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 users
    { duration: '1m', target: 20 },   // Ramp up to 20 users
    { duration: '2m', target: 20 },   // Stay at 20 users
    { duration: '1m', target: 50 },   // Spike to 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],      // 95% under 2s (agents can be slow)
    http_req_failed: ['rate<0.05'],         // Error rate under 5%
    agent_list_duration: ['p(95)<200'],     // List operations fast
    agent_execution_duration: ['p(95)<2000'], // Execution under 2s (target)
  },
};

const AUTH_URL = __ENV.AUTH_URL || 'http://localhost:9002';
const AGENTS_URL = __ENV.AGENTS_URL || 'http://localhost:9000';

let accessToken = null;
let tenantId = null;

export function setup() {
  // Setup: Create a test user and get token
  const email = `k6-agent-test-${Date.now()}@example.com`;
  const password = 'K6TestPassword123!';
  const tenant = `k6-tenant-${Date.now()}`;

  // Register
  const registerRes = http.post(
    `${AUTH_URL}/auth/register`,
    JSON.stringify({ email, password, tenant_id: tenant }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  // Login
  const loginRes = http.post(
    `${AUTH_URL}/auth/login`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (loginRes.status === 200) {
    return {
      token: loginRes.json('access_token'),
      tenant: tenant,
    };
  }

  throw new Error('Failed to setup test user');
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`,
  };

  // Test 1: List agents (high frequency)
  const listStart = Date.now();
  const listRes = http.get(`${AGENTS_URL}/agents/`, { headers });
  const listDuration = Date.now() - listStart;

  check(listRes, {
    'list agents status is 200': (r) => r.status === 200,
    'list agents duration < 200ms': () => listDuration < 200,
  });

  agentListDuration.add(listDuration);
  sleep(1);

  // Test 2: Create an agent (medium frequency)
  const agentTypes = ['developer', 'qa_tester', 'designer', 'devops', 'analyst'];
  const createPayload = JSON.stringify({
    name: `K6 Agent ${Date.now()}-${Math.random()}`,
    type: agentTypes[Math.floor(Math.random() * agentTypes.length)],
    description: 'K6 load test agent',
    provider: 'anthropic',
    model: 'claude-3-5-sonnet-20241022',
    system_prompt: 'You are a test agent for performance testing.',
    tenant_id: data.tenant,
  });

  const createRes = http.post(`${AGENTS_URL}/agents/`, createPayload, { headers });

  const createSuccess = check(createRes, {
    'create agent status is 200/201': (r) => r.status === 200 || r.status === 201,
    'create agent returns id': (r) => r.json('id') !== undefined,
  });

  agentCreationRate.add(createSuccess);

  let agentId = null;
  if (createSuccess) {
    agentCounter.add(1);
    agentId = createRes.json('id');
    sleep(1);

    // Test 3: Get agent details (high frequency)
    const getRes = http.get(`${AGENTS_URL}/agents/${agentId}`, { headers });

    check(getRes, {
      'get agent status is 200': (r) => r.status === 200,
      'get agent returns correct id': (r) => r.json('id') === agentId,
    });

    sleep(1);

    // Test 4: Update agent (low frequency)
    const updatePayload = JSON.stringify({
      name: `K6 Agent Updated ${Date.now()}`,
      description: 'Updated by K6 load test',
    });

    const updateRes = http.patch(
      `${AGENTS_URL}/agents/${agentId}`,
      updatePayload,
      { headers }
    );

    check(updateRes, {
      'update agent status is 200': (r) => r.status === 200,
    });

    sleep(2);

    // Test 5: Execute agent (low frequency, slow operation)
    // Note: This is commented out as it's expensive and slow
    // Uncomment for full load testing
    /*
    const executePayload = JSON.stringify({
      task: 'Write a brief hello message',
      context: { test: true },
    });

    const execStart = Date.now();
    const execRes = http.post(
      `${AGENTS_URL}/agents/${agentId}/execute`,
      executePayload,
      { headers, timeout: '30s' }
    );
    const execDuration = Date.now() - execStart;

    check(execRes, {
      'execute agent status is 200': (r) => r.status === 200,
      'execute agent duration < 2s': () => execDuration < 2000,
    });

    agentExecutionDuration.add(execDuration);
    sleep(3);
    */

    // Test 6: Delete agent (cleanup)
    const deleteRes = http.del(`${AGENTS_URL}/agents/${agentId}`, { headers });

    check(deleteRes, {
      'delete agent status is 200/204': (r) => r.status === 200 || r.status === 204,
    });
  }

  sleep(2);
}

export function handleSummary(data) {
  return {
    'tests/performance/reports/k6-agents-summary.json': JSON.stringify(data),
    stdout: textSummary(data),
  };
}

function textSummary(data) {
  let summary = '\n' + '='.repeat(60) + '\n';
  summary += 'K6 Agents API Load Test Summary\n';
  summary += '='.repeat(60) + '\n\n';

  summary += 'HTTP Requests:\n';
  summary += `  Total: ${data.metrics.http_reqs.values.count}\n`;
  summary += `  Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s\n`;
  summary += `  Failed: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n\n`;

  summary += 'Response Times:\n';
  summary += `  Average: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `  Median: ${data.metrics.http_req_duration.values.med.toFixed(2)}ms\n`;
  summary += `  95th: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  99th: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n\n`;

  summary += 'Agent Metrics:\n';
  summary += `  Agents Created: ${data.metrics.agents_created.values.count}\n`;
  summary += `  Creation Success Rate: ${(data.metrics.agent_creation_success.values.rate * 100).toFixed(2)}%\n`;
  summary += `  List Duration (95th): ${data.metrics.agent_list_duration.values['p(95)'].toFixed(2)}ms\n\n`;

  summary += '='.repeat(60) + '\n';

  return summary;
}
