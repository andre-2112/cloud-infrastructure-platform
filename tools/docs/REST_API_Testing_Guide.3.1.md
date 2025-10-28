# Cloud Architecture v3.1 - REST API Testing Guide

**Version:** 3.1
**Last Updated:** 2025-10-09
**Status:** Production Ready

**Changes from v3.0:**
- Updated to version 3.1
- Fixed deployment directory naming to always use `<deployment-id>-<org>-<project>/` format
- Removed incorrect `src/` subdirectory references for deployment manifest
- Updated all document version references to 3.1
- Updated Pulumi stack naming to include stack name: `<deployment-id>-<stack-name>-<environment>`


---

## Table of Contents

1. [Overview](#overview)
2. [Testing Strategy](#testing-strategy)
3. [Test Environment Setup](#test-environment-setup)
4. [Unit Testing](#unit-testing)
5. [Integration Testing](#integration-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)
9. [WebSocket Testing](#websocket-testing)
10. [Test Data Management](#test-data-management)
11. [CI/CD Integration](#cicd-integration)
12. [Test Coverage Requirements](#test-coverage-requirements)

---

## Overview

This guide provides comprehensive testing strategies, tools, and examples for the Cloud Architecture v3.1 REST API. The testing framework ensures reliability, security, and performance across all API endpoints.

### Testing Objectives

- **Correctness**: Verify all endpoints return expected responses
- **Security**: Validate authentication, authorization, and data protection
- **Performance**: Ensure APIs meet latency and throughput requirements
- **Reliability**: Test error handling and edge cases
- **Integration**: Verify interactions with AWS services and Pulumi
- **Regression**: Prevent introduction of bugs in new releases

---

## Testing Strategy

### Testing Pyramid

```
        /\
       /E2E\          10% - End-to-End Tests
      /------\
     /  Integ \       30% - Integration Tests
    /----------\
   /    Unit    \     60% - Unit Tests
  /--------------\
```

### Test Types

| Test Type | Purpose | Tools | Coverage |
|-----------|---------|-------|----------|
| Unit | Test individual functions | Jest | 80%+ |
| Integration | Test API endpoints | Supertest, Jest | 70%+ |
| E2E | Test complete workflows | Postman, Newman | 50%+ |
| Performance | Test load/stress | k6, Artillery | Critical paths |
| Security | Test vulnerabilities | OWASP ZAP, Burp | All endpoints |
| Contract | Test API contracts | Pact | All integrations |

---

## Test Environment Setup

### Prerequisites

```bash
# Install dependencies
npm install --save-dev \
  jest \
  @types/jest \
  ts-jest \
  supertest \
  @types/supertest \
  nock \
  aws-sdk-mock \
  jest-junit

# Install performance testing tools
npm install -g k6 artillery

# Install security testing tools
docker pull owasp/zap2docker-stable
```

### Environment Configuration

```bash
# .env.test
NODE_ENV=test
API_BASE_URL=http://localhost:3000
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=111111111111
COGNITO_USER_POOL_ID=us-east-1_test123
COGNITO_CLIENT_ID=test-client-id
DYNAMODB_TABLE=cloud-deployments-test
S3_BUCKET=cloud-state-test
LOG_LEVEL=debug
```

### Jest Configuration

```typescript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/types/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  reporters: [
    'default',
    ['jest-junit', { outputDirectory: 'test-results', outputName: 'junit.xml' }],
  ],
};
```

---

## Unit Testing

### Testing Service Layer

```typescript
// tests/unit/deployment-service.test.ts
import { DeploymentService } from '../../src/services/deployment-service';
import { DynamoDB } from 'aws-sdk';
import AWSMock from 'aws-sdk-mock';

describe('DeploymentService', () => {
  let service: DeploymentService;

  beforeAll(() => {
    AWSMock.setSDKInstance(require('aws-sdk'));
  });

  afterAll(() => {
    AWSMock.restore();
  });

  beforeEach(() => {
    service = new DeploymentService();
  });

  describe('createDeployment', () => {
    test('should create deployment with valid parameters', async () => {
      AWSMock.mock('DynamoDB.DocumentClient', 'put', (params, callback) => {
        callback(null, { Item: params.Item });
      });

      const deployment = await service.createDeployment({
        org: 'TestOrg',
        project: 'TestProject',
        template: 'default',
        region: 'us-east-1',
        accountDev: '111111111111',
      });

      expect(deployment).toBeDefined();
      expect(deployment.id).toMatch(/^D[A-Z0-9]{6}$/);
      expect(deployment.org).toBe('TestOrg');
      expect(deployment.status).toBe('initialized');

      AWSMock.restore('DynamoDB.DocumentClient');
    });

    test('should throw error with invalid template', async () => {
      await expect(
        service.createDeployment({
          org: 'TestOrg',
          project: 'TestProject',
          template: 'invalid-template',
          region: 'us-east-1',
          accountDev: '111111111111',
        })
      ).rejects.toThrow('Invalid template');
    });

    test('should throw error with invalid AWS account', async () => {
      await expect(
        service.createDeployment({
          org: 'TestOrg',
          project: 'TestProject',
          template: 'default',
          region: 'us-east-1',
          accountDev: 'invalid',
        })
      ).rejects.toThrow('Invalid AWS account ID');
    });
  });

  describe('getDeployment', () => {
    test('should retrieve existing deployment', async () => {
      const mockDeployment = {
        id: 'D1BRV40',
        org: 'TestOrg',
        project: 'TestProject',
        status: 'deployed',
      };

      AWSMock.mock('DynamoDB.DocumentClient', 'get', (params, callback) => {
        callback(null, { Item: mockDeployment });
      });

      const deployment = await service.getDeployment('D1BRV40');

      expect(deployment).toEqual(mockDeployment);

      AWSMock.restore('DynamoDB.DocumentClient');
    });

    test('should return null for non-existent deployment', async () => {
      AWSMock.mock('DynamoDB.DocumentClient', 'get', (params, callback) => {
        callback(null, {});
      });

      const deployment = await service.getDeployment('DNOTFOUND');

      expect(deployment).toBeNull();

      AWSMock.restore('DynamoDB.DocumentClient');
    });
  });
});
```

### Testing Validation Logic

```typescript
// tests/unit/validators.test.ts
import {
  validateDeploymentId,
  validateEnvironment,
  validateStackName,
  validateTemplate,
} from '../../src/utils/validators';

describe('Validators', () => {
  describe('validateDeploymentId', () => {
    test('should validate correct deployment IDs', () => {
      expect(validateDeploymentId('D1BRV40')).toBe(true);
      expect(validateDeploymentId('DABC123')).toBe(true);
      expect(validateDeploymentId('D000000')).toBe(true);
    });

    test('should reject invalid deployment IDs', () => {
      expect(validateDeploymentId('D12345')).toBe(false);  // Too short
      expect(validateDeploymentId('D12345678')).toBe(false);  // Too long
      expect(validateDeploymentId('E1BRV40')).toBe(false);  // Wrong prefix
      expect(validateDeploymentId('d1brv40')).toBe(false);  // Lowercase
    });
  });

  describe('validateEnvironment', () => {
    test('should validate correct environments', () => {
      expect(validateEnvironment('dev')).toBe(true);
      expect(validateEnvironment('stage')).toBe(true);
      expect(validateEnvironment('prod')).toBe(true);
    });

    test('should reject invalid environments', () => {
      expect(validateEnvironment('staging')).toBe(false);  // Old naming
      expect(validateEnvironment('test')).toBe(false);
      expect(validateEnvironment('Dev')).toBe(false);  // Case sensitive
    });
  });

  describe('validateStackName', () => {
    test('should validate correct stack names', () => {
      expect(validateStackName('network')).toBe(true);
      expect(validateStackName('database-rds')).toBe(true);
      expect(validateStackName('compute-ec2')).toBe(true);
    });

    test('should reject invalid stack names', () => {
      expect(validateStackName('invalid_stack')).toBe(false);  // Underscore
      expect(validateStackName('Stack-1')).toBe(false);  // Uppercase
      expect(validateStackName('')).toBe(false);  // Empty
    });
  });

  describe('validateTemplate', () => {
    test('should validate correct templates', () => {
      expect(validateTemplate('default')).toBe(true);
      expect(validateTemplate('minimal')).toBe(true);
      expect(validateTemplate('microservices')).toBe(true);
      expect(validateTemplate('data-platform')).toBe(true);
    });

    test('should reject invalid templates', () => {
      expect(validateTemplate('custom')).toBe(false);
      expect(validateTemplate('Default')).toBe(false);  // Case sensitive
    });
  });
});
```

### Testing Dependency Resolution

```typescript
// tests/unit/dependency-resolver.test.ts
import { DependencyResolver } from '../../src/services/dependency-resolver';

describe('DependencyResolver', () => {
  let resolver: DependencyResolver;

  beforeEach(() => {
    resolver = new DependencyResolver();
  });

  describe('resolveLayers', () => {
    test('should resolve simple dependencies', () => {
      const stacks = [
        { name: 'network', dependencies: [] },
        { name: 'security', dependencies: ['network'] },
        { name: 'compute-ec2', dependencies: ['security'] },
      ];

      const layers = resolver.resolveLayers(stacks);

      expect(layers).toHaveLength(3);
      expect(layers[0]).toEqual(['network']);
      expect(layers[1]).toEqual(['security']);
      expect(layers[2]).toEqual(['compute-ec2']);
    });

    test('should resolve parallel dependencies', () => {
      const stacks = [
        { name: 'network', dependencies: [] },
        { name: 'security', dependencies: ['network'] },
        { name: 'storage', dependencies: ['network'] },
        { name: 'compute-ec2', dependencies: ['security', 'storage'] },
      ];

      const layers = resolver.resolveLayers(stacks);

      expect(layers).toHaveLength(3);
      expect(layers[0]).toEqual(['network']);
      expect(layers[1]).toContain('security');
      expect(layers[1]).toContain('storage');
      expect(layers[2]).toEqual(['compute-ec2']);
    });

    test('should detect circular dependencies', () => {
      const stacks = [
        { name: 'a', dependencies: ['b'] },
        { name: 'b', dependencies: ['c'] },
        { name: 'c', dependencies: ['a'] },
      ];

      expect(() => resolver.resolveLayers(stacks)).toThrow('Circular dependency detected');
    });

    test('should detect missing dependencies', () => {
      const stacks = [
        { name: 'security', dependencies: ['network'] },
      ];

      expect(() => resolver.resolveLayers(stacks)).toThrow('Missing dependency: network');
    });
  });
});
```

---

## Integration Testing

### Testing API Endpoints

```typescript
// tests/integration/deployments.test.ts
import request from 'supertest';
import { app } from '../../src/app';
import { getAuthToken } from '../helpers/auth';

describe('Deployments API', () => {
  let authToken: string;

  beforeAll(async () => {
    authToken = await getAuthToken();
  });

  describe('POST /api/v1/deployments', () => {
    test('should create new deployment', async () => {
      const response = await request(app)
        .post('/api/v1/deployments')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          org: 'TestOrg',
          project: 'TestProject',
          template: 'default',
          region: 'us-east-1',
          accountDev: '111111111111',
        })
        .expect(201);

      expect(response.body).toHaveProperty('id');
      expect(response.body.id).toMatch(/^D[A-Z0-9]{6}$/);
      expect(response.body.org).toBe('TestOrg');
      expect(response.body.status).toBe('initialized');
    });

    test('should return 400 for invalid request', async () => {
      const response = await request(app)
        .post('/api/v1/deployments')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          org: 'TestOrg',
          // Missing required fields
        })
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    test('should return 401 without authentication', async () => {
      await request(app)
        .post('/api/v1/deployments')
        .send({
          org: 'TestOrg',
          project: 'TestProject',
          template: 'default',
          region: 'us-east-1',
          accountDev: '111111111111',
        })
        .expect(401);
    });
  });

  describe('GET /api/v1/deployments/:id', () => {
    let deploymentId: string;

    beforeAll(async () => {
      const response = await request(app)
        .post('/api/v1/deployments')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          org: 'TestOrg',
          project: 'TestProject',
          template: 'default',
          region: 'us-east-1',
          accountDev: '111111111111',
        });

      deploymentId = response.body.id;
    });

    test('should retrieve existing deployment', async () => {
      const response = await request(app)
        .get(`/api/v1/deployments/${deploymentId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.id).toBe(deploymentId);
      expect(response.body.org).toBe('TestOrg');
    });

    test('should return 404 for non-existent deployment', async () => {
      await request(app)
        .get('/api/v1/deployments/DNOTFOUND')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });

  describe('POST /api/v1/deployments/:id/deploy', () => {
    let deploymentId: string;

    beforeAll(async () => {
      const response = await request(app)
        .post('/api/v1/deployments')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          org: 'TestOrg',
          project: 'TestProject',
          template: 'minimal',
          region: 'us-east-1',
          accountDev: '111111111111',
        });

      deploymentId = response.body.id;
    });

    test('should start deployment', async () => {
      const response = await request(app)
        .post(`/api/v1/deployments/${deploymentId}/deploy`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          environment: 'dev',
        })
        .expect(202);

      expect(response.body).toHaveProperty('jobId');
      expect(response.body.status).toBe('deploying');
    });

    test('should return 400 for invalid environment', async () => {
      await request(app)
        .post(`/api/v1/deployments/${deploymentId}/deploy`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          environment: 'invalid',
        })
        .expect(400);
    });
  });
});
```

### Testing Smart Skip Logic

```typescript
// tests/integration/smart-skip.test.ts
import request from 'supertest';
import { app } from '../../src/app';
import { getAuthToken } from '../helpers/auth';

describe('Smart Skip Logic', () => {
  let authToken: string;
  let deploymentId: string;

  beforeAll(async () => {
    authToken = await getAuthToken();

    // Create deployment
    const response = await request(app)
      .post('/api/v1/deployments')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        org: 'TestOrg',
        project: 'SkipTest',
        template: 'minimal',
        region: 'us-east-1',
        accountDev: '111111111111',
      });

    deploymentId = response.body.id;
  });

  test('should skip unchanged stacks on re-deployment', async () => {
    // First deployment
    await request(app)
      .post(`/api/v1/deployments/${deploymentId}/deploy`)
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        environment: 'dev',
      })
      .expect(202);

    // Wait for completion (mock or use shorter timeout in tests)
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Second deployment without changes
    const response = await request(app)
      .post(`/api/v1/deployments/${deploymentId}/deploy`)
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        environment: 'dev',
        smartSkip: true,
      })
      .expect(202);

    // Check status
    const statusResponse = await request(app)
      .get(`/api/v1/deployments/${deploymentId}/status?environment=dev`)
      .set('Authorization', `Bearer ${authToken}`)
      .expect(200);

    expect(statusResponse.body).toHaveProperty('stacksSkipped');
    expect(statusResponse.body.stacksSkipped.length).toBeGreaterThan(0);
  });
});
```

### Testing WebSocket Connections

```typescript
// tests/integration/websocket.test.ts
import WebSocket from 'ws';
import { getAuthToken } from '../helpers/auth';

describe('WebSocket Real-Time Updates', () => {
  let authToken: string;
  let ws: WebSocket;

  beforeAll(async () => {
    authToken = await getAuthToken();
  });

  afterEach(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });

  test('should connect to WebSocket with valid token', (done) => {
    ws = new WebSocket(`ws://localhost:3000/deployments/D1BRV40-network-dev?token=${authToken}`);

    ws.on('open', () => {
      expect(ws.readyState).toBe(WebSocket.OPEN);
      done();
    });

    ws.on('error', (error) => {
      fail(`WebSocket error: ${error.message}`);
    });
  });

  test('should receive deployment progress updates', (done) => {
    ws = new WebSocket(`ws://localhost:3000/deployments/D1BRV40-network-dev?token=${authToken}`);

    ws.on('message', (data) => {
      const message = JSON.parse(data.toString());

      expect(message).toHaveProperty('type');
      expect(message).toHaveProperty('timestamp');

      if (message.type === 'progress') {
        expect(message).toHaveProperty('stack');
        expect(message).toHaveProperty('status');
        expect(message).toHaveProperty('progress');
      }

      done();
    });
  });

  test('should reject connection without authentication', (done) => {
    ws = new WebSocket('ws://localhost:3000/deployments/D1BRV40-network-dev');

    ws.on('error', (error) => {
      expect(error).toBeDefined();
      done();
    });

    ws.on('open', () => {
      fail('WebSocket should not connect without authentication');
    });
  });
});
```

---

## End-to-End Testing

### Postman Collection

```json
{
  "info": {
    "name": "Cloud Architecture v3.1 API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Complete Deployment Workflow",
      "item": [
        {
          "name": "1. Create Deployment",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 201', function () {",
                  "    pm.response.to.have.status(201);",
                  "});",
                  "",
                  "pm.test('Response has deployment ID', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData).to.have.property('id');",
                  "    pm.collectionVariables.set('deploymentId', jsonData.id);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"org\": \"TestOrg\",\n  \"project\": \"E2ETest\",\n  \"template\": \"default\",\n  \"region\": \"us-east-1\",\n  \"accountDev\": \"111111111111\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{baseUrl}}/api/v1/deployments",
              "host": ["{{baseUrl}}"],
              "path": ["api", "v1", "deployments"]
            }
          }
        },
        {
          "name": "2. Validate Deployment",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Validation passes', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.valid).to.be.true;",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "url": {
              "raw": "{{baseUrl}}/api/v1/deployments/{{deploymentId}}/validate",
              "host": ["{{baseUrl}}"],
              "path": ["api", "v1", "deployments", "{{deploymentId}}", "validate"]
            }
          }
        },
        {
          "name": "3. Deploy to Dev",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 202', function () {",
                  "    pm.response.to.have.status(202);",
                  "});",
                  "",
                  "pm.test('Deployment started', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.status).to.equal('deploying');",
                  "    pm.collectionVariables.set('jobId', jsonData.jobId);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "body": {
              "mode": "raw",
              "raw": "{\n  \"environment\": \"dev\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{baseUrl}}/api/v1/deployments/{{deploymentId}}/deploy",
              "host": ["{{baseUrl}}"],
              "path": ["api", "v1", "deployments", "{{deploymentId}}", "deploy"]
            }
          }
        },
        {
          "name": "4. Check Deployment Status",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Deployment completed or in progress', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(['deploying', 'deployed']).to.include(jsonData.status);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{baseUrl}}/api/v1/deployments/{{deploymentId}}/status?environment=dev",
              "host": ["{{baseUrl}}"],
              "path": ["api", "v1", "deployments", "{{deploymentId}}", "status"],
              "query": [
                {
                  "key": "environment",
                  "value": "dev"
                }
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### Newman CLI Execution

```bash
# Run collection
newman run cloud-api-tests.json \
  --environment cloud-api-env.json \
  --reporters cli,junit,html \
  --reporter-junit-export results/junit.xml \
  --reporter-html-export results/report.html

# Run with specific environment
newman run cloud-api-tests.json \
  --environment prod-env.json \
  --bail
```

---

## Performance Testing

### k6 Load Test Script

```javascript
// tests/performance/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],     // Less than 1% errors
    errors: ['rate<0.1'],                // Less than 10% errors
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:3000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN;

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  };

  // Test GET /deployments
  let response = http.get(`${BASE_URL}/api/v1/deployments`, params);
  check(response, {
    'GET /deployments status is 200': (r) => r.status === 200,
    'GET /deployments response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Test GET /deployments/:id
  response = http.get(`${BASE_URL}/api/v1/deployments/D1BRV40`, params);
  check(response, {
    'GET /deployments/:id status is 200': (r) => r.status === 200,
    'GET /deployments/:id response time < 300ms': (r) => r.timings.duration < 300,
  }) || errorRate.add(1);

  sleep(1);
}
```

### Artillery Test Configuration

```yaml
# tests/performance/artillery-config.yml
config:
  target: "http://localhost:3000"
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 300
      arrivalRate: 20
      name: "Sustained load"
    - duration: 120
      arrivalRate: 50
      name: "Spike test"
  payload:
    path: "test-data.csv"
    fields:
      - deploymentId
      - environment
  defaults:
    headers:
      Authorization: "Bearer {{authToken}}"

scenarios:
  - name: "List Deployments"
    weight: 30
    flow:
      - get:
          url: "/api/v1/deployments"
          expect:
            - statusCode: 200
            - contentType: "application/json"

  - name: "Get Deployment Details"
    weight: 40
    flow:
      - get:
          url: "/api/v1/deployments/{{deploymentId}}"
          expect:
            - statusCode: 200

  - name: "Deploy Stack"
    weight: 20
    flow:
      - post:
          url: "/api/v1/deployments/{{deploymentId}}/deploy"
          json:
            environment: "{{environment}}"
          expect:
            - statusCode: 202

  - name: "Check Status"
    weight: 10
    flow:
      - get:
          url: "/api/v1/deployments/{{deploymentId}}/status"
          qs:
            environment: "{{environment}}"
          expect:
            - statusCode: 200
```

---

## Security Testing

### OWASP ZAP Automated Scan

```bash
# Run baseline scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:3000/api/v1 \
  -r zap-report.html

# Run full scan
docker run -t owasp/zap2docker-stable zap-full-scan.py \
  -t http://localhost:3000/api/v1 \
  -r zap-full-report.html

# Run API scan with OpenAPI spec
docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable \
  zap-api-scan.py \
  -t openapi.json \
  -f openapi \
  -r zap-api-report.html
```

### Authentication & Authorization Tests

```typescript
// tests/security/auth.test.ts
import request from 'supertest';
import { app } from '../../src/app';

describe('Security - Authentication & Authorization', () => {
  describe('Authentication', () => {
    test('should reject requests without token', async () => {
      await request(app)
        .get('/api/v1/deployments')
        .expect(401);
    });

    test('should reject requests with invalid token', async () => {
      await request(app)
        .get('/api/v1/deployments')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });

    test('should reject requests with expired token', async () => {
      const expiredToken = 'expired-jwt-token';

      await request(app)
        .get('/api/v1/deployments')
        .set('Authorization', `Bearer ${expiredToken}`)
        .expect(401);
    });
  });

  describe('Authorization', () => {
    test('should prevent access to other org resources', async () => {
      const token = await getAuthToken({ org: 'OrgA' });

      // Try to access OrgB deployment
      await request(app)
        .get('/api/v1/deployments/DORGB01')
        .set('Authorization', `Bearer ${token}`)
        .expect(403);
    });

    test('should prevent deployment without deploy permission', async () => {
      const token = await getAuthToken({ role: 'viewer' });

      await request(app)
        .post('/api/v1/deployments/D1BRV40/deploy')
        .set('Authorization', `Bearer ${token}`)
        .send({ environment: 'dev' })
        .expect(403);
    });

    test('should prevent prod deployment without prod permission', async () => {
      const token = await getAuthToken({ role: 'developer' });

      await request(app)
        .post('/api/v1/deployments/D1BRV40/deploy')
        .set('Authorization', `Bearer ${token}`)
        .send({ environment: 'prod' })
        .expect(403);
    });
  });

  describe('Input Validation', () => {
    test('should prevent SQL injection attempts', async () => {
      const token = await getAuthToken();

      await request(app)
        .get('/api/v1/deployments/D1BRV40\'; DROP TABLE deployments;--')
        .set('Authorization', `Bearer ${token}`)
        .expect(400);
    });

    test('should prevent XSS attempts', async () => {
      const token = await getAuthToken();

      await request(app)
        .post('/api/v1/deployments')
        .set('Authorization', `Bearer ${token}`)
        .send({
          org: '<script>alert("XSS")</script>',
          project: 'TestProject',
          template: 'default',
          region: 'us-east-1',
          accountDev: '111111111111',
        })
        .expect(400);
    });
  });
});
```

---

## Test Data Management

### Test Data Factory

```typescript
// tests/helpers/factories.ts
import { faker } from '@faker-js/faker';

export class DeploymentFactory {
  static create(overrides = {}) {
    return {
      id: `D${faker.random.alphaNumeric(6).toUpperCase()}`,
      org: faker.company.name(),
      project: faker.commerce.productName(),
      template: faker.helpers.arrayElement(['default', 'minimal', 'microservices']),
      region: 'us-east-1',
      accountDev: '111111111111',
      status: 'initialized',
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }

  static createMany(count: number, overrides = {}) {
    return Array.from({ length: count }, () => this.create(overrides));
  }
}

export class StackFactory {
  static create(overrides = {}) {
    return {
      name: faker.helpers.arrayElement([
        'network',
        'security',
        'database-rds',
        'compute-ec2',
      ]),
      status: 'pending',
      dependencies: [],
      ...overrides,
    };
  }
}
```

### Database Seeding

```typescript
// tests/helpers/seed.ts
import { DynamoDB } from 'aws-sdk';
import { DeploymentFactory } from './factories';

const dynamodb = new DynamoDB.DocumentClient({
  region: 'us-east-1',
  endpoint: 'http://localhost:8000', // Local DynamoDB
});

export async function seedDeployments(count: number = 10) {
  const deployments = DeploymentFactory.createMany(count);

  for (const deployment of deployments) {
    await dynamodb.put({
      TableName: 'cloud-deployments-test',
      Item: deployment,
    }).promise();
  }

  return deployments;
}

export async function clearDatabase() {
  const result = await dynamodb.scan({
    TableName: 'cloud-deployments-test',
  }).promise();

  if (result.Items) {
    for (const item of result.Items) {
      await dynamodb.delete({
        TableName: 'cloud-deployments-test',
        Key: { id: item.id },
      }).promise();
    }
  }
}
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/api-tests.yml
name: REST API Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest

    services:
      dynamodb:
        image: amazon/dynamodb-local
        ports:
          - 8000:8000

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Setup test database
        run: npm run db:setup:test

      - name: Run integration tests
        run: npm run test:integration
        env:
          DYNAMODB_ENDPOINT: http://localhost:8000

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: integration-test-results
          path: test-results/

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Start API server
        run: npm start &
        env:
          NODE_ENV: test

      - name: Wait for server
        run: npx wait-on http://localhost:3000/health

      - name: Run E2E tests
        run: npm run test:e2e

  security-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run OWASP ZAP scan
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: 'http://localhost:3000/api/v1'

  performance-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Setup k6
        run: |
          curl https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz -L | tar xvz
          sudo mv k6-v0.45.0-linux-amd64/k6 /usr/local/bin

      - name: Run performance tests
        run: k6 run tests/performance/load-test.js
```

---

## Test Coverage Requirements

### Coverage Thresholds

| Component | Line Coverage | Branch Coverage | Function Coverage |
|-----------|---------------|-----------------|-------------------|
| Services | 85% | 80% | 90% |
| Controllers | 80% | 75% | 85% |
| Middleware | 90% | 85% | 95% |
| Utils | 85% | 80% | 90% |
| **Overall** | **80%** | **70%** | **85%** |

### Coverage Report

```bash
# Generate coverage report
npm run test:coverage

# View HTML report
open coverage/lcov-report/index.html

# Check coverage thresholds
npm run test:coverage:check
```

### Package.json Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --testPathPattern=tests/unit",
    "test:integration": "jest --testPathPattern=tests/integration --runInBand",
    "test:e2e": "jest --testPathPattern=tests/e2e --runInBand",
    "test:coverage": "jest --coverage",
    "test:coverage:check": "jest --coverage --coverageThreshold='{\"global\":{\"lines\":80,\"branches\":70,\"functions\":85}}'",
    "test:watch": "jest --watch",
    "test:performance": "k6 run tests/performance/load-test.js",
    "test:security": "docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:3000"
  }
}
```

---

## Conclusion

This comprehensive testing guide ensures the Cloud Architecture v3.1 REST API maintains high quality, security, and performance standards. Regular execution of all test types—unit, integration, E2E, performance, and security—is essential for reliable production deployments.

**Next Steps:**
1. Implement all test suites
2. Integrate with CI/CD pipeline
3. Monitor test results and coverage
4. Update tests as API evolves
5. Review and improve test coverage quarterly

For additional testing resources, see:
- CLI Testing Guide 3.0
- WebSocket Testing Addendum
- Performance Benchmarking Guide
