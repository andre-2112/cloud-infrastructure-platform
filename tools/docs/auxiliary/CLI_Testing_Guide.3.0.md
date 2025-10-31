# CLI Testing Guide v3.0

**Note:** This document will be moved to ./cloud/tools/docs/ when the new directory structure is created in Session 2.

**Version:** 3.0
**Date:** 2025-10-09
**Platform:** Cloud Infrastructure Orchestration Platform (cloud-0.7)
**Status:** Complete Testing Specification

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Command-Specific Tests](#command-specific-tests)
7. [Error Handling Tests](#error-handling-tests)
8. [Performance Testing](#performance-testing)
9. [Test Automation](#test-automation)
10. [Continuous Integration](#continuous-integration)

---

## Testing Overview

### Testing Strategy

The Cloud CLI testing strategy encompasses multiple levels:

1. **Unit Tests** - Test individual functions and modules
2. **Integration Tests** - Test CLI commands with mock backends
3. **End-to-End Tests** - Test complete workflows with real AWS/Pulumi
4. **Performance Tests** - Test deployment speed and resource usage
5. **Error Handling Tests** - Test failure scenarios and recovery

### Test Coverage Goals

- **Unit Tests:** >80% code coverage
- **Integration Tests:** All CLI commands
- **E2E Tests:** All common workflows
- **Error Tests:** All error paths
- **Performance Tests:** All deployment scenarios

---

## Test Environment Setup

### Prerequisites

```bash
# Install testing frameworks
npm install --save-dev jest ts-jest @types/jest
npm install --save-dev @pulumi/pulumi
npm install --save-dev aws-sdk-mock
npm install --save-dev nock supertest

# Install CLI globally for testing
cd ./cloud/tools/cli
npm install
npm run build
npm link
```

### Test Directory Structure

```
./cloud/tools/cli/tests/
├── unit/
│   ├── commands/
│   ├── orchestrator/
│   ├── templates/
│   ├── deployment/
│   └── utils/
├── integration/
│   ├── init.test.ts
│   ├── deploy.test.ts
│   ├── destroy.test.ts
│   └── ...
├── e2e/
│   ├── workflows/
│   ├── scenarios/
│   └── fixtures/
├── fixtures/
│   ├── templates/
│   ├── manifests/
│   └── configs/
└── helpers/
    ├── mock-aws.ts
    ├── mock-pulumi.ts
    └── test-utils.ts
```

### Test Configuration

**jest.config.js:**
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/index.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

---

## Unit Testing

### Testing Individual Commands

**Example: Testing `init` command logic**

```typescript
// tests/unit/commands/init.test.ts
import { generateDeploymentId } from '../../src/deployment/id-generator';
import { sanitizeName } from '../../src/utils/sanitizer';

describe('Init Command - ID Generation', () => {
  test('should generate valid deployment ID', () => {
    const id = generateDeploymentId();

    expect(id).toMatch(/^D[0-9A-Z]{6}$/);
    expect(id.length).toBe(7);
  });

  test('should generate unique IDs', () => {
    const id1 = generateDeploymentId();
    const id2 = generateDeploymentId();

    expect(id1).not.toBe(id2);
  });
});

describe('Init Command - Name Sanitization', () => {
  test('should sanitize organization names', () => {
    expect(sanitizeName('Company-A')).toBe('companya');
    expect(sanitizeName('Company A & B')).toBe('companya-b');
    expect(sanitizeName('Company_123')).toBe('company123');
  });

  test('should handle special characters', () => {
    expect(sanitizeName('Test@#$%')).toBe('test');
    expect(sanitizeName('Test---Name')).toBe('test-name');
  });
});
```

### Testing Template System

```typescript
// tests/unit/templates/template-loader.test.ts
import { loadTemplate } from '../../src/templates/template-loader';
import { validateTemplate } from '../../src/templates/validator';

describe('Template System', () => {
  test('should load default template', () => {
    const template = loadTemplate('default');

    expect(template).toBeDefined();
    expect(template.stacks).toHaveLength(16);
    expect(template.environments).toContain('dev');
    expect(template.environments).toContain('stage');
    expect(template.environments).toContain('prod');
  });

  test('should validate template structure', () => {
    const template = loadTemplate('default');
    const result = validateTemplate(template);

    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test('should detect missing dependencies', () => {
    const invalidTemplate = {
      stacks: [
        { name: 'compute', dependencies: ['nonexistent'] }
      ]
    };

    const result = validateTemplate(invalidTemplate);

    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Dependency not found: nonexistent');
  });
});
```

### Testing Dependency Resolution

```typescript
// tests/unit/orchestrator/dependency-resolver.test.ts
import { resolveDependencies } from '../../src/orchestrator/dependency-resolver';

describe('Dependency Resolver', () => {
  test('should resolve simple dependencies', () => {
    const stacks = [
      { name: 'network', dependencies: [] },
      { name: 'security', dependencies: ['network'] }
    ];

    const layers = resolveDependencies(stacks);

    expect(layers).toHaveLength(2);
    expect(layers[0]).toContain('network');
    expect(layers[1]).toContain('security');
  });

  test('should detect circular dependencies', () => {
    const stacks = [
      { name: 'a', dependencies: ['b'] },
      { name: 'b', dependencies: ['a'] }
    ];

    expect(() => resolveDependencies(stacks)).toThrow('Circular dependency');
  });

  test('should handle complex dependency graphs', () => {
    const stacks = [
      { name: 'dns', dependencies: [] },
      { name: 'network', dependencies: [] },
      { name: 'security', dependencies: ['network'] },
      { name: 'database', dependencies: ['network', 'security'] },
      { name: 'compute', dependencies: ['network', 'security'] }
    ];

    const layers = resolveDependencies(stacks);

    expect(layers[0]).toEqual(expect.arrayContaining(['dns', 'network']));
    expect(layers[1]).toContain('security');
    expect(layers[2]).toEqual(expect.arrayContaining(['database', 'compute']));
  });
});
```

### Running Unit Tests

```bash
# Run all unit tests
npm run test:unit

# Run with coverage
npm run test:unit -- --coverage

# Run specific test file
npm run test:unit -- tests/unit/commands/init.test.ts

# Watch mode
npm run test:unit -- --watch
```

---

## Integration Testing

### Testing Complete Commands

**Example: Testing `init` command end-to-end**

```typescript
// tests/integration/init.test.ts
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

describe('cloud init command', () => {
  const testDir = './test-deployments';

  beforeAll(() => {
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
  });

  afterAll(() => {
    // Cleanup
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true });
    }
  });

  test('should initialize deployment with all required files', () => {
    const output = execSync(
      `cloud init D1TEST01 \
        --org "TestOrg" \
        --project "test-project" \
        --domain "test.example.com" \
        --template minimal \
        --region us-east-1 \
        --account-dev 111111111111`,
      { encoding: 'utf-8', cwd: testDir }
    );

    expect(output).toContain('D1TEST01');
    expect(output).toContain('Created');

    // Verify directory structure
    const deployPath = path.join(testDir, 'cloud/deploy/D1TEST01-testorg-test-project');
    expect(fs.existsSync(deployPath)).toBe(true);
    expect(fs.existsSync(path.join(deployPath, 'src/Deployment_Manifest.yaml'))).toBe(true);
    expect(fs.existsSync(path.join(deployPath, 'config'))).toBe(true);
    expect(fs.existsSync(path.join(deployPath, 'logs/init.log'))).toBe(true);
  });

  test('should generate correct number of config files', () => {
    const deployPath = './test-deployments/cloud/deploy/D1TEST01-testorg-test-project';
    const configFiles = fs.readdirSync(path.join(deployPath, 'config'));

    // Minimal template: 3 stacks × 1 environment = 3 config files
    expect(configFiles).toHaveLength(3);
    expect(configFiles).toContain('network.dev.yaml');
    expect(configFiles).toContain('dns.dev.yaml');
    expect(configFiles).toContain('security.dev.yaml');
  });

  test('should fail with missing required parameters', () => {
    expect(() => {
      execSync('cloud init --org "TestOrg"', { encoding: 'utf-8' });
    }).toThrow();
  });
});
```

### Testing Deploy Command

```typescript
// tests/integration/deploy.test.ts
import { execSync } from 'child_process';

describe('cloud deploy command', () => {
  test('should validate deployment before execution', () => {
    const output = execSync(
      'cloud deploy D1TEST01 --environment dev --preview',
      { encoding: 'utf-8' }
    );

    expect(output).toContain('Validating deployment');
    expect(output).toContain('Execution plan');
    expect(output).toContain('Layer 1');
  });

  test('should show smart skip logic', () => {
    // Deploy once
    execSync('cloud deploy D1TEST01 --environment dev');

    // Deploy again without changes
    const output = execSync(
      'cloud deploy D1TEST01 --environment dev',
      { encoding: 'utf-8' }
    );

    expect(output).toContain('Smart skip');
    expect(output).toContain('unchanged');
  });
});
```

### Testing Validation Commands

```typescript
// tests/integration/validate.test.ts
describe('cloud validate command', () => {
  test('should validate correct manifest', () => {
    const output = execSync(
      'cloud validate D1TEST01',
      { encoding: 'utf-8' }
    );

    expect(output).toContain('valid');
    expect(output).not.toContain('error');
  });

  test('should detect circular dependencies', () => {
    // Modify manifest to create circular dependency
    // ... test implementation

    expect(() => {
      execSync('cloud validate D1TEST01', { encoding: 'utf-8' });
    }).toThrow('Circular dependency');
  });
});
```

### Running Integration Tests

```bash
# Run all integration tests
npm run test:integration

# Run specific test
npm run test:integration -- tests/integration/init.test.ts

# With verbose output
npm run test:integration -- --verbose
```

---

## End-to-End Testing

### Complete Workflow Tests

**Workflow 1: Full Deployment Lifecycle**

```typescript
// tests/e2e/workflows/full-lifecycle.test.ts
describe('E2E: Full Deployment Lifecycle', () => {
  const deploymentId = `D1E2E${Date.now().toString(36).toUpperCase()}`;

  test('Initialize → Validate → Deploy → Destroy', async () => {
    // Step 1: Initialize
    const initOutput = execSync(
      `cloud init ${deploymentId} \
        --org "E2ETest" \
        --project "test" \
        --domain "test.e2e.com" \
        --template minimal \
        --region us-east-1 \
        --account-dev ${process.env.AWS_ACCOUNT_DEV}`,
      { encoding: 'utf-8' }
    );
    expect(initOutput).toContain(deploymentId);

    // Step 2: Validate
    const validateOutput = execSync(
      `cloud validate ${deploymentId}`,
      { encoding: 'utf-8' }
    );
    expect(validateOutput).toContain('valid');

    // Step 3: Deploy (preview mode for E2E safety)
    const deployOutput = execSync(
      `cloud deploy ${deploymentId} --environment dev --preview`,
      { encoding: 'utf-8' }
    );
    expect(deployOutput).toContain('Execution plan');

    // Step 4: Check status
    const statusOutput = execSync(
      `cloud status ${deploymentId} --environment dev`,
      { encoding: 'utf-8' }
    );
    expect(statusOutput).toContain(deploymentId);

    // Note: Actual deployment and destroy skipped in E2E to avoid AWS costs
    // In production E2E, these would be executed
  }, 300000); // 5 minute timeout
});
```

**Workflow 2: Environment Promotion**

```typescript
// tests/e2e/workflows/environment-promotion.test.ts
describe('E2E: Environment Promotion', () => {
  test('Dev → Stage → Prod promotion flow', () => {
    const deploymentId = 'D1E2E02';

    // Deploy to dev
    execSync(`cloud deploy ${deploymentId} --environment dev --preview`);

    // Enable stage
    const enableOutput = execSync(
      `cloud enable-environment ${deploymentId} stage`,
      { encoding: 'utf-8' }
    );
    expect(enableOutput).toContain('enabled');

    // Deploy to stage
    execSync(`cloud deploy ${deploymentId} --environment stage --preview`);

    // Enable prod
    execSync(`cloud enable-environment ${deploymentId} prod`);

    // Deploy to prod
    execSync(`cloud deploy ${deploymentId} --environment prod --preview`);

    // Verify all environments
    const listOutput = execSync(
      `cloud list-environments ${deploymentId}`,
      { encoding: 'utf-8' }
    );
    expect(listOutput).toContain('dev');
    expect(listOutput).toContain('stage');
    expect(listOutput).toContain('prod');
  });
});
```

### Running E2E Tests

```bash
# Run all E2E tests (requires AWS credentials)
export AWS_ACCOUNT_DEV=111111111111
export AWS_REGION=us-east-1
npm run test:e2e

# Run specific workflow
npm run test:e2e -- tests/e2e/workflows/full-lifecycle.test.ts

# Skip E2E tests (faster CI)
npm run test -- --testPathIgnorePatterns=e2e
```

---

## Command-Specific Tests

### Init Command Tests

```typescript
describe('cloud init', () => {
  test('generates valid deployment ID', () => { /* ... */ });
  test('creates directory structure', () => { /* ... */ });
  test('generates manifest from template', () => { /* ... */ });
  test('creates config files', () => { /* ... */ });
  test('handles interactive mode', () => { /* ... */ });
  test('loads from config file', () => { /* ... */ });
});
```

### Deploy Command Tests

```typescript
describe('cloud deploy', () => {
  test('validates before deployment', () => { /* ... */ });
  test('resolves dependencies', () => { /* ... */ });
  test('executes layers in order', () => { /* ... */ });
  test('applies smart skip logic', () => { /* ... */ });
  test('handles parallel execution', () => { /* ... */ });
  test('rolls back on failure', () => { /* ... */ });
  test('emits WebSocket events', () => { /* ... */ });
});
```

### Validate Command Tests

```typescript
describe('cloud validate', () => {
  test('validates manifest syntax', () => { /* ... */ });
  test('checks dependencies', () => { /* ... */ });
  test('verifies configuration', () => { /* ... */ });
  test('detects circular dependencies', () => { /* ... */ });
  test('validates runtime placeholders', () => { /* ... */ });
});
```

### Register-Stack Command Tests

```typescript
describe('cloud register-stack', () => {
  test('validates stack directory', () => { /* ... */ });
  test('parses Pulumi.yaml', () => { /* ... */ });
  test('creates template file', () => { /* ... */ });
  test('adds to registry', () => { /* ... */ });
  test('handles dependencies', () => { /* ... */ });
});
```

---

## Error Handling Tests

### Testing Error Scenarios

```typescript
// tests/unit/error-handling.test.ts
describe('Error Handling', () => {
  test('handles missing deployment', () => {
    expect(() => {
      execSync('cloud deploy NONEXISTENT', { encoding: 'utf-8' });
    }).toThrow('Deployment not found');
  });

  test('handles invalid AWS credentials', () => {
    // Mock invalid credentials
    expect(() => {
      execSync('cloud deploy D1TEST01 --environment dev', {
        env: { ...process.env, AWS_ACCESS_KEY_ID: 'invalid' }
      });
    }).toThrow('AWS credentials invalid');
  });

  test('handles Pulumi authentication failure', () => {
    // Mock Pulumi auth failure
    expect(() => {
      execSync('cloud deploy D1TEST01', {
        env: { ...process.env, PULUMI_ACCESS_TOKEN: '' }
      });
    }).toThrow('Not logged in to Pulumi');
  });

  test('handles circular dependencies', () => {
    // Create manifest with circular deps
    expect(() => {
      execSync('cloud validate D1CIRCULAR');
    }).toThrow('Circular dependency detected');
  });

  test('provides actionable error messages', () => {
    try {
      execSync('cloud deploy NONEXISTENT');
    } catch (error) {
      expect(error.message).toContain('Solution:');
      expect(error.message).toContain('cloud list');
    }
  });
});
```

### Testing Recovery Scenarios

```typescript
describe('Recovery Scenarios', () => {
  test('automatic rollback on deployment failure', () => {
    // Simulate deployment failure
    // Verify rollback executed
  });

  test('state lock timeout handling', () => {
    // Simulate state lock
    // Verify timeout and retry logic
  });

  test('partial deployment recovery', () => {
    // Simulate partial deployment
    // Verify resumption from checkpoint
  });
});
```

---

## Performance Testing

### Deployment Speed Tests

```typescript
// tests/performance/deployment-speed.test.ts
describe('Performance: Deployment Speed', () => {
  test('full deployment completes within time limit', async () => {
    const start = Date.now();

    // Execute deployment (mocked)
    await mockDeployment('D1PERF01', {
      stacks: 16,
      environment: 'dev'
    });

    const duration = Date.now() - start;

    // Should complete within 45 minutes (2700 seconds)
    expect(duration).toBeLessThan(2700000);
  }, 3000000);

  test('smart skip reduces deployment time', async () => {
    // First deployment
    const firstDuration = await measureDeployment('D1PERF02');

    // Second deployment (no changes)
    const secondDuration = await measureDeployment('D1PERF02');

    // Second should be significantly faster (>70% reduction)
    expect(secondDuration).toBeLessThan(firstDuration * 0.3);
  });

  test('parallel execution improves speed', async () => {
    const sequential = await measureDeployment('D1PERF03', { parallel: 1 });
    const parallel = await measureDeployment('D1PERF03', { parallel: 3 });

    // Parallel should be faster
    expect(parallel).toBeLessThan(sequential);
  });
});
```

### Resource Usage Tests

```typescript
describe('Performance: Resource Usage', () => {
  test('memory usage stays within limits', async () => {
    const memoryBefore = process.memoryUsage().heapUsed;

    // Execute large deployment
    await mockDeployment('D1PERF04', { stacks: 16 });

    const memoryAfter = process.memoryUsage().heapUsed;
    const memoryIncrease = memoryAfter - memoryBefore;

    // Should not exceed 500MB increase
    expect(memoryIncrease).toBeLessThan(500 * 1024 * 1024);
  });

  test('handles concurrent deployments', async () => {
    const deployments = Array(5).fill(0).map((_, i) =>
      mockDeployment(`D1PERF0${i + 5}`)
    );

    await Promise.all(deployments);

    // All should complete successfully
    expect(true).toBe(true);
  });
});
```

### Running Performance Tests

```bash
# Run performance tests
npm run test:performance

# With detailed profiling
npm run test:performance -- --verbose

# Generate performance report
npm run test:performance -- --json --outputFile=performance-report.json
```

---

## Test Automation

### NPM Test Scripts

**package.json:**
```json
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest tests/unit",
    "test:integration": "jest tests/integration",
    "test:e2e": "jest tests/e2e",
    "test:performance": "jest tests/performance",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2"
  }
}
```

### Pre-commit Hooks

**.husky/pre-commit:**
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run unit tests before commit
npm run test:unit

# Run linter
npm run lint
```

### Automated Test Suite

```bash
# Run complete test suite
npm test

# Quick test (unit + integration)
npm run test:unit && npm run test:integration

# Full test (including E2E)
npm run test:unit && npm run test:integration && npm run test:e2e
```

---

## Continuous Integration

### GitHub Actions Workflow

**.github/workflows/test.yml:**
```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [18.x, 20.x]

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}

    - name: Install dependencies
      run: |
        cd ./cloud/tools/cli
        npm ci

    - name: Run linter
      run: npm run lint

    - name: Run unit tests
      run: npm run test:unit -- --coverage

    - name: Run integration tests
      run: npm run test:integration

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage/coverage-final.json

    - name: Build CLI
      run: npm run build

  e2e:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: 18.x

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Install dependencies
      run: |
        cd ./cloud/tools/cli
        npm ci

    - name: Run E2E tests
      run: npm run test:e2e
      env:
        AWS_ACCOUNT_DEV: ${{ secrets.AWS_ACCOUNT_DEV }}
```

### Test Coverage Reports

```bash
# Generate coverage report
npm run test:coverage

# View HTML report
open coverage/lcov-report/index.html

# Check coverage thresholds
npm run test:coverage -- --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

## Best Practices

### Test Writing Guidelines

1. **Descriptive Test Names**
   ```typescript
   // Good
   test('should generate valid deployment ID with correct format', () => {});

   // Bad
   test('test1', () => {});
   ```

2. **Arrange-Act-Assert Pattern**
   ```typescript
   test('example', () => {
     // Arrange
     const input = 'test-input';

     // Act
     const result = processInput(input);

     // Assert
     expect(result).toBe('expected-output');
   });
   ```

3. **One Assertion Per Test**
   ```typescript
   // Good - focused test
   test('should sanitize org name', () => {
     expect(sanitizeName('Test-Org')).toBe('testorg');
   });

   test('should handle special characters', () => {
     expect(sanitizeName('Test@#$')).toBe('test');
   });
   ```

4. **Use Test Fixtures**
   ```typescript
   const testManifest = require('../fixtures/minimal-manifest.json');
   const result = validateManifest(testManifest);
   ```

5. **Mock External Dependencies**
   ```typescript
   jest.mock('aws-sdk');
   jest.mock('@pulumi/pulumi');
   ```

### Continuous Improvement

- Review and update tests with each feature addition
- Maintain >80% code coverage
- Run full test suite before releases
- Monitor test execution time
- Refactor slow tests

---

## Troubleshooting Tests

### Common Test Issues

**Tests timing out:**
```typescript
// Increase timeout for slow tests
test('slow operation', async () => {
  // ...
}, 30000); // 30 second timeout
```

**Flaky tests:**
```typescript
// Add retries for flaky tests
jest.retryTimes(3);
```

**Mock not working:**
```typescript
// Ensure mocks are cleared between tests
beforeEach(() => {
  jest.clearAllMocks();
});
```

**Coverage not counting:**
```typescript
// Ensure test files match pattern
// Check jest.config.js testMatch setting
```

---

## Conclusion

Comprehensive testing ensures the Cloud CLI operates reliably across all scenarios. Follow this guide to:

- Write effective unit, integration, and E2E tests
- Achieve high code coverage
- Automate testing in CI/CD pipelines
- Maintain code quality and reliability

For additional information:
- **CLI Reference:** `CLI_Commands_Reference.3.0.md`
- **Architecture:** `Multi-Stack-Architecture-3.0.md`

---

**Document Version:** 3.0.0
**Last Updated:** 2025-10-09
**Status:** Complete Testing Guide