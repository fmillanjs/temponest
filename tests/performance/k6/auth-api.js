/**
 * K6 Load Test for TempoNest Auth API
 *
 * Usage:
 *   k6 run tests/performance/k6/auth-api.js
 *   k6 run --vus 10 --duration 30s tests/performance/k6/auth-api.js
 *   k6 run --vus 50 --duration 5m tests/performance/k6/auth-api.js --out json=reports/auth-api-results.json
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const authFailureRate = new Rate('auth_failures');
const authDuration = new Trend('auth_duration');
const registrationCounter = new Counter('registrations');
const loginCounter = new Counter('logins');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 100 }, // Spike to 100 users
    { duration: '1m', target: 100 },  // Stay at 100 users
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'], // 95% of requests should be below 200ms
    http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
    auth_duration: ['p(95)<300'],     // 95% of auth operations under 300ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:9002';

// Generate random email
function randomEmail() {
  return `k6test-${Date.now()}-${Math.floor(Math.random() * 100000)}@example.com`;
}

// Generate random tenant ID
function randomTenant() {
  return `k6-tenant-${Math.floor(Math.random() * 100)}`;
}

export default function () {
  const email = randomEmail();
  const password = 'K6TestPassword123!';
  const tenantId = randomTenant();

  // Test 1: Register a new user
  const registerPayload = JSON.stringify({
    email: email,
    password: password,
    tenant_id: tenantId,
  });

  const registerHeaders = { 'Content-Type': 'application/json' };
  const registerRes = http.post(
    `${BASE_URL}/auth/register`,
    registerPayload,
    { headers: registerHeaders }
  );

  const registerSuccess = check(registerRes, {
    'register status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    'register returns user_id': (r) => r.json('user_id') !== undefined,
  });

  authFailureRate.add(!registerSuccess);
  if (registerSuccess) {
    registrationCounter.add(1);
  }

  sleep(1);

  // Test 2: Login with the registered user
  const loginPayload = JSON.stringify({
    email: email,
    password: password,
  });

  const loginStart = Date.now();
  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    loginPayload,
    { headers: registerHeaders }
  );
  const loginDuration = Date.now() - loginStart;

  const loginSuccess = check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login returns access_token': (r) => r.json('access_token') !== undefined,
    'login returns refresh_token': (r) => r.json('refresh_token') !== undefined,
    'login duration < 300ms': () => loginDuration < 300,
  });

  authFailureRate.add(!loginSuccess);
  authDuration.add(loginDuration);

  if (loginSuccess) {
    loginCounter.add(1);
    const accessToken = loginRes.json('access_token');

    sleep(1);

    // Test 3: Verify token with protected endpoint
    const verifyHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    };

    const verifyRes = http.get(`${BASE_URL}/auth/me`, { headers: verifyHeaders });

    check(verifyRes, {
      'verify status is 200': (r) => r.status === 200,
      'verify returns user info': (r) => r.json('email') === email,
    });

    sleep(1);

    // Test 4: Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      'health check status is 200': (r) => r.status === 200,
      'health check returns status': (r) => r.json('status') !== undefined,
    });
  }

  sleep(2);
}

export function handleSummary(data) {
  return {
    'reports/k6-auth-summary.json': JSON.stringify(data),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const colors = options.enableColors;

  let summary = '\n' + indent + '='.repeat(60) + '\n';
  summary += indent + 'K6 Auth API Load Test Summary\n';
  summary += indent + '='.repeat(60) + '\n\n';

  // Request metrics
  summary += indent + 'HTTP Requests:\n';
  summary += indent + `  Total: ${data.metrics.http_reqs.values.count}\n`;
  summary += indent + `  Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s\n`;
  summary += indent + `  Failed: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n\n`;

  // Response time metrics
  summary += indent + 'Response Times:\n';
  summary += indent + `  Average: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += indent + `  Median: ${data.metrics.http_req_duration.values.med.toFixed(2)}ms\n`;
  summary += indent + `  95th: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += indent + `  99th: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n\n`;

  // Custom metrics
  summary += indent + 'Auth Metrics:\n';
  summary += indent + `  Registrations: ${data.metrics.registrations.values.count}\n`;
  summary += indent + `  Logins: ${data.metrics.logins.values.count}\n`;
  summary += indent + `  Auth Failures: ${(data.metrics.auth_failures.values.rate * 100).toFixed(2)}%\n`;
  summary += indent + `  Auth Duration (95th): ${data.metrics.auth_duration.values['p(95)'].toFixed(2)}ms\n\n`;

  summary += indent + '='.repeat(60) + '\n';

  return summary;
}
