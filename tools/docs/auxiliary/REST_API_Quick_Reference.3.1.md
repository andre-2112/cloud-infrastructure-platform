# Cloud Architecture v3.1 - REST API Quick Reference

**Version:** 3.1
**Last Updated:** 2025-10-09
**Base URL:** `https://api.example.com/api/v1`

---

## New in v3.1

### Performance Enhancements
- **Smart Skip Logic:** Automatically skips unchanged stacks during deployment, reducing execution time
- **Layer-Based Parallel Execution:** Executes independent stacks in parallel within dependency layers
- **Template-Based Dependency Resolution:** Enhanced dependency graph resolution using deployment templates

### Monitoring Improvements
- **WebSocket Monitoring:** Real-time progress updates via WebSocket connections (ws:// endpoints)
- **Enhanced Logging:** Improved structured logging with deployment-level and stack-level granularity

### Stack Naming
- **New Format:** `<deployment-id>-<environment>` (e.g., "D1BRV40-network-dev")
- **Old Format (v2.x):** `<org>/<stack>/<env>` (e.g., "myorg/network/dev")

---

## Authentication Endpoints

### User Login
Authenticate user and receive JWT tokens
```http
POST /auth/login
```

### User Logout
Invalidate current access token
```http
POST /auth/logout
```

### Refresh Token
Refresh access token using refresh token
```http
POST /auth/refresh
```

### Generate API Key
Generate API key for programmatic access
```http
POST /auth/api-keys
```

### List API Keys
List all API keys for current user
```http
GET /auth/api-keys
```

### Revoke API Key
Revoke an API key
```http
DELETE /auth/api-keys/:keyId
```

---

## Deployment Endpoints

### Create Deployment
Create new deployment (equivalent to cloud init)
```http
POST /deployments
```

### List Deployments
List all deployments with filtering and pagination
```http
GET /deployments
```

### Get Deployment Details
Get detailed information about a specific deployment
```http
GET /deployments/:deploymentId
```

### Update Deployment
Update deployment configuration
```http
PUT /deployments/:deploymentId
```

### Delete Deployment
Delete deployment (must destroy all stacks first)
```http
DELETE /deployments/:deploymentId
```

### Deploy All Stacks
Deploy all stacks in deployment (equivalent to cloud deploy)
```http
POST /deployments/:deploymentId/deploy
```

### Destroy All Stacks
Destroy all stacks in deployment (equivalent to cloud destroy)
```http
POST /deployments/:deploymentId/destroy
```

### Validate Deployment
Validate deployment configuration (equivalent to cloud validate)
```http
POST /deployments/:deploymentId/validate
```

### Get Operation Status
Get status of deployment operation (deploy, destroy, etc.)
```http
GET /deployments/:deploymentId/operations/:operationId
```

---

## Stack Endpoints

### List Stacks
List all registered stacks in the platform
```http
GET /stacks
```

### Get Stack Details
Get detailed information about a specific stack type
```http
GET /stacks/:stackName
```

### Register Stack
Register new stack type (equivalent to cloud register-stack)
```http
POST /stacks
```

### Update Stack Definition
Update existing stack definition
```http
PUT /stacks/:stackName
```

### Unregister Stack
Remove stack type from platform (equivalent to cloud unregister-stack)
```http
DELETE /stacks/:stackName
```

### Deploy Single Stack
Deploy single stack in deployment (equivalent to cloud deploy-stack)
```http
POST /deployments/:deploymentId/stacks/:stackName/deploy
```

### Destroy Single Stack
Destroy single stack in deployment (equivalent to cloud destroy-stack)
```http
POST /deployments/:deploymentId/stacks/:stackName/destroy
```

### Get Stack Status
Get status of stack within deployment
```http
GET /deployments/:deploymentId/stacks/:stackName/status
```

---

## Environment Endpoints

### List Environments
List all environments for a deployment
```http
GET /deployments/:deploymentId/environments
```

### Enable Environment
Enable environment for deployment (equivalent to cloud enable-environment)
```http
POST /deployments/:deploymentId/environments/:environmentName/enable
```

### Disable Environment
Disable environment (equivalent to cloud disable-environment)
```http
POST /deployments/:deploymentId/environments/:environmentName/disable
```

---

## Template Endpoints

### List Templates
List all available deployment templates
```http
GET /templates
```

### Get Template Details
Get detailed information about a specific template
```http
GET /templates/:templateName
```

### Create Template
Create new custom deployment template
```http
POST /templates
```

### Update Template
Update existing template definition
```http
PUT /templates/:templateName
```

### Delete Template
Delete custom template
```http
DELETE /templates/:templateName
```

### Validate Template
Validate template definition and configuration
```http
POST /templates/:templateName/validate
```

---

## State Management Endpoints

### Export State
Export deployment state (equivalent to pulumi stack export)
```http
GET /deployments/:deploymentId/state/export
```

### Import State
Import deployment state (equivalent to pulumi stack import)
```http
POST /deployments/:deploymentId/state/import
```

### Sync State
Sync state with Pulumi Cloud
```http
POST /deployments/:deploymentId/state/sync
```

---

## Monitoring Endpoints

### Get Deployment Logs
Get deployment and stack operation logs
```http
GET /deployments/:deploymentId/logs
```

### Get Deployment Metrics
Get deployment metrics and statistics
```http
GET /deployments/:deploymentId/metrics
```

### API Health Check
Check API health status
```http
GET /health
```

---

## WebSocket Channels

### Deployment Operation Updates
Real-time updates for specific deployment operation
```
ws://api.example.com/ws
Channel: deployments/:deploymentId/operations/:operationId
```

### All Deployment Events
All events for a specific deployment
```
ws://api.example.com/ws
Channel: deployments/:deploymentId
```

### Stack Events
Events for specific stack within deployment
```
ws://api.example.com/ws
Channel: deployments/:deploymentId/stacks/:stackName
```

### Environment Events
Environment-specific events
```
ws://api.example.com/ws
Channel: deployments/:deploymentId/environments/:environmentName
```

---

## Authentication

### JWT Bearer Token
Include JWT token in Authorization header
```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key
Include API key in X-API-Key header
```http
X-API-Key: msk_live_1234567890abcdef
```

---

## Common Response Format

### Success Response
All successful responses follow this structure
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
All error responses follow this structure
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success (GET, PUT, PATCH, DELETE) |
| 201 | Resource created (POST) |
| 202 | Async operation started |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict |
| 422 | Validation failed |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | Upstream service error |
| 503 | Service unavailable |

---

## Rate Limits

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|--------------|
| Free | 60 | 1,000 | 10,000 |
| Standard | 300 | 10,000 | 100,000 |
| Enterprise | 1,000 | 50,000 | Unlimited |

---

**Total Endpoints:** 45+
**Endpoint Categories:** 7
**WebSocket Channels:** 4

For detailed documentation, see: REST_API_Documentation.3.1.md
