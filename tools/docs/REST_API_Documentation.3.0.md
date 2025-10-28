# Cloud Architecture v3.0 - REST API Documentation

**Version:** 3.0
**Last Updated:** 2025-10-09
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Installation & Setup](#installation--setup)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Endpoints Reference](#api-endpoints-reference)
6. [WebSocket Real-Time Updates](#websocket-real-time-updates)
7. [Request/Response Schemas](#requestresponse-schemas)
8. [Error Handling](#error-handling)
9. [Rate Limiting & Quotas](#rate-limiting--quotas)
10. [Integration Examples](#integration-examples)
11. [OpenAPI Specification](#openapi-specification)
12. [Deployment Guide](#deployment-guide)
13. [Monitoring & Observability](#monitoring--observability)
14. [Security Considerations](#security-considerations)
15. [Versioning Strategy](#versioning-strategy)
16. [Troubleshooting](#troubleshooting)

---

## Executive Summary

The Cloud Architecture v3.0 REST API provides programmatic access to all deployment management, template operations, stack orchestration, and environment configuration capabilities. This API enables integration with CI/CD pipelines, custom dashboards, automated workflows, and third-party tools.

### Key Features

- **Complete Feature Parity**: All 25+ CLI commands available as REST endpoints
- **Enterprise Authentication**: AWS Cognito + JWT with multi-factor authentication
- **Role-Based Access Control**: Granular permissions for deployments, stacks, and environments
- **Real-Time Updates**: WebSocket connections for deployment progress streaming via ws:// endpoints
- **Smart Skip Logic**: Automatically skips stacks with no configuration changes for faster deployments
- **Layer-Based Parallel Execution**: Deploys/destroys stacks in parallel within dependency layers
- **Template-Based Dependency Resolution**: Intelligent dependency graph resolution from templates
- **OpenAPI 3.0 Specification**: Complete schema for code generation and documentation
- **Serverless Deployment**: AWS Lambda + API Gateway for scalability and cost efficiency
- **Multi-Tenancy Support**: Organization-level isolation and resource management
- **Audit Logging**: Complete request/response tracking for compliance

### API Statistics

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 45+ |
| **Endpoint Categories** | 7 |
| **Authentication Methods** | 2 (JWT, API Keys) |
| **WebSocket Channels** | 4 |
| **Supported HTTP Methods** | GET, POST, PUT, PATCH, DELETE |
| **API Version** | v1 |
| **OpenAPI Version** | 3.0.3 |

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Clients                              │
│  (Web UI, CLI, CI/CD Pipelines, Custom Tools, Mobile Apps)      │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                    │
             │ HTTPS/WSS                          │ HTTPS/WSS
             │                                    │
┌────────────▼────────────────────────────────────▼────────────────┐
│                    AWS API Gateway                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  - Request Validation        - Rate Limiting              │   │
│  │  - CORS Handling             - Request/Response Transform │   │
│  │  - API Key Management        - WebSocket Support          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────┬─────────────────────────────────────┬───────────────┘
             │                                     │
             │ Lambda Proxy Integration            │ WebSocket
             │                                     │
┌────────────▼─────────────────────────┐  ┌────────▼───────────────┐
│     Lambda: API Handler              │  │  Lambda: WebSocket     │
│  ┌────────────────────────────────┐  │  │  Handler               │
│  │  - Express.js/Fastify          │  │  │  ┌──────────────────┐  │
│  │  - JWT Validation              │  │  │  │  - Connection    │  │
│  │  - RBAC Enforcement            │  │  │  │    Management    │  │
│  │  - Business Logic              │  │  │  │  - Event         │  │
│  │  - Pulumi API Integration      │  │  │  │    Broadcasting  │  │
│  └────────────────────────────────┘  │  │  └──────────────────┘  │
└────────────┬─────────────────────────┘  └────────┬───────────────┘
             │                                     │
    ┌────────┼─────────────────────────────────────┼────────┐
    │        │                                     │        │
    │        │      AWS Services Layer             │        │
    │  ┌─────▼──────┐  ┌──────────┐  ┌───────────▼─────┐  │
    │  │  Cognito   │  │   S3     │  │  DynamoDB       │  │
    │  │  (Auth)    │  │ (State)  │  │  (Metadata)     │  │
    │  └────────────┘  └──────────┘  └─────────────────┘  │
    │                                                       │
    │  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │
    │  │  CloudWatch│  │   SQS    │  │  EventBridge    │  │
    │  │  (Logs)    │  │ (Queue)  │  │  (Events)       │  │
    │  └────────────┘  └──────────┘  └─────────────────┘  │
    └───────────────────────────────────────────────────────┘
                              │
                ┌─────────────▼──────────────┐
                │   Pulumi Cloud State       │
                │   (Stack State Management) │
                └────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | Express.js / Fastify | HTTP request handling |
| **Runtime** | Node.js 20.x | Lambda execution environment |
| **Authentication** | AWS Cognito + JWT | User authentication & token management |
| **Authorization** | Custom RBAC Middleware | Permission enforcement |
| **API Gateway** | AWS API Gateway (REST + WebSocket) | Request routing & management |
| **State Storage** | AWS S3 + Pulumi Cloud | Deployment state persistence |
| **Metadata Storage** | AWS DynamoDB | Deployment metadata & audit logs |
| **WebSocket** | API Gateway WebSocket API | Real-time updates |
| **Monitoring** | AWS CloudWatch | Logging & metrics |
| **Async Processing** | AWS SQS + Lambda | Long-running deployment operations |
| **Event Bus** | AWS EventBridge | Event-driven architecture |
| **Documentation** | OpenAPI 3.0 + Swagger UI | API documentation |

### API Request Flow

```
1. Client Request
   │
   ├─> API Gateway (Entry Point)
   │   ├─> Request Validation (Schema, Size, Format)
   │   ├─> Rate Limiting Check
   │   └─> CORS Headers
   │
2. Authentication
   │
   ├─> JWT Token Extraction & Validation
   │   ├─> Cognito Token Verification
   │   ├─> Token Expiry Check
   │   └─> User Identity Resolution
   │
3. Authorization
   │
   ├─> RBAC Permission Check
   │   ├─> Load User Roles
   │   ├─> Load Resource Permissions
   │   └─> Evaluate Access Rules
   │
4. Business Logic
   │
   ├─> Request Processing
   │   ├─> Input Validation
   │   ├─> Business Rules Enforcement
   │   └─> Pulumi API Integration
   │
5. State Management
   │
   ├─> State Operations
   │   ├─> S3 State Read/Write
   │   ├─> DynamoDB Metadata Update
   │   └─> Pulumi Cloud Sync
   │
6. Response Generation
   │
   └─> Response Formatting
       ├─> Success/Error Response
       ├─> Response Transformation
       └─> Audit Log Creation
```

---

## Installation & Setup

### Prerequisites

- **AWS Account**: Active AWS account with appropriate permissions
- **Node.js**: Version 20.x or later
- **AWS CLI**: Configured with credentials
- **Pulumi Account**: Active Pulumi Cloud account
- **Domain**: Custom domain for API (optional but recommended)

### Deployment Steps

#### Step 1: Configure Environment Variables

Create `.env` file with required configuration:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Cognito Configuration
COGNITO_USER_POOL_ID=us-east-1_ABC123DEF
COGNITO_CLIENT_ID=abcdef123456789
COGNITO_DOMAIN=auth.example.com

# API Configuration
API_VERSION=v1
API_DOMAIN=api.example.com
API_STAGE=prod

# Pulumi Configuration
PULUMI_ACCESS_TOKEN=pul-xxxxxxxxxxxxx
PULUMI_ORG=my-organization

# DynamoDB Configuration
DYNAMODB_DEPLOYMENTS_TABLE=cloud-deployments
DYNAMODB_AUDIT_TABLE=cloud-audit-logs

# S3 Configuration
S3_STATE_BUCKET=cloud-state-prod
S3_CONFIG_BUCKET=cloud-config-prod

# WebSocket Configuration
WEBSOCKET_API_ENDPOINT=wss://ws.api.example.com

# Security Configuration
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60000

# Logging
LOG_LEVEL=info
LOG_RETENTION_DAYS=30
```

#### Step 2: Deploy Infrastructure

The API service is deployed using the `api-service` stack:

```bash
# Navigate to API service stack
cd ./cloud/stacks/api-service

# Install dependencies
npm install

# Configure Pulumi stack
pulumi stack init prod
pulumi config set aws:region us-east-1
pulumi config set apiDomain api.example.com

# Deploy API infrastructure
pulumi up
```

This deploys:
- API Gateway (REST + WebSocket)
- Lambda functions (API Handler, WebSocket Handler)
- Cognito User Pool & Client
- DynamoDB tables
- S3 buckets
- IAM roles & policies
- CloudWatch log groups

#### Step 3: Configure Cognito

```bash
# Create initial admin user
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_ABC123DEF \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password TempPass123!

# Add user to admin group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id us-east-1_ABC123DEF \
  --username admin@example.com \
  --group-name Administrators
```

#### Step 4: Configure API Gateway Custom Domain

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS \
  --region us-east-1

# Create API Gateway custom domain
aws apigatewayv2 create-domain-name \
  --domain-name api.example.com \
  --domain-name-configurations CertificateArn=arn:aws:acm:...

# Create Route53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://dns-record.json
```

#### Step 5: Verify Installation

```bash
# Health check
curl https://api.example.com/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "3.0.0",
#   "timestamp": "2025-10-09T12:00:00Z"
# }

# API version info
curl https://api.example.com/api/v1/info

# Expected response:
# {
#   "apiVersion": "v1",
#   "platformVersion": "3.0.0",
#   "endpoints": 45,
#   "authentication": "AWS Cognito + JWT"
# }
```

### Local Development Setup

For local development and testing:

```bash
# Clone repository
git clone https://github.com/your-org/cloud-platform
cd cloud-platform

# Install dependencies
npm install

# Start local API server
npm run dev:api

# API available at: http://localhost:3000
```

---

## Authentication & Authorization

### Authentication Flow

#### 1. User Login (AWS Cognito)

```
Client Application
  │
  ├─> POST /api/v1/auth/login
  │   Body: { "username": "user@example.com", "password": "***" }
  │
  └─> AWS Cognito User Pool
      │
      ├─> Validate Credentials
      ├─> Check MFA (if enabled)
      │
      └─> Return Tokens
          {
            "accessToken": "eyJhbGc...",
            "idToken": "eyJhbGc...",
            "refreshToken": "eyJhbGc...",
            "expiresIn": 3600
          }
```

#### 2. API Request with JWT

```
Client Application
  │
  ├─> GET /api/v1/deployments
  │   Headers: { "Authorization": "Bearer eyJhbGc..." }
  │
API Gateway
  │
  ├─> Lambda Authorizer
  │   ├─> Extract JWT from Authorization header
  │   ├─> Verify JWT signature with Cognito public keys
  │   ├─> Check token expiration
  │   ├─> Extract user claims (sub, email, groups)
  │   │
  │   └─> Generate IAM Policy
  │       {
  │         "principalId": "user-123",
  │         "policyDocument": { "Allow": [...] },
  │         "context": { "userId": "...", "roles": [...] }
  │       }
  │
  └─> Lambda Function (API Handler)
      ├─> Access user context from authorizer
      ├─> Enforce RBAC rules
      └─> Process request
```

#### 3. Token Refresh

```
Client Application (Token Expired)
  │
  ├─> POST /api/v1/auth/refresh
  │   Body: { "refreshToken": "eyJhbGc..." }
  │
  └─> AWS Cognito
      │
      ├─> Validate Refresh Token
      │
      └─> Return New Access Token
          {
            "accessToken": "eyJhbGc...",
            "idToken": "eyJhbGc...",
            "expiresIn": 3600
          }
```

### Authorization (RBAC)

#### Role Definitions

| Role | Description | Permissions |
|------|-------------|-------------|
| **Administrator** | Full platform access | All operations on all resources |
| **Deployment Manager** | Manage deployments | Create, update, deploy, destroy deployments |
| **Stack Operator** | Manage stacks | Deploy, destroy stacks within deployments |
| **Environment Manager** | Manage environments | Enable, disable environments |
| **Template Editor** | Manage templates | Create, update, delete templates |
| **Auditor** | Read-only access | View all resources, download audit logs |
| **Developer** | Limited access | View deployments, view stacks, view logs |

#### Permission Matrix

| Endpoint | Administrator | Deployment Manager | Stack Operator | Environment Manager | Template Editor | Auditor | Developer |
|----------|---------------|-------------------|----------------|---------------------|----------------|---------|-----------|
| **POST /deployments** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **GET /deployments** | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| **PUT /deployments/:id** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **DELETE /deployments/:id** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **POST /deployments/:id/deploy** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **POST /deployments/:id/destroy** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **POST /stacks/:id/deploy** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **POST /stacks/:id/destroy** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **POST /environments/:id/enable** | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **POST /environments/:id/disable** | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **POST /templates** | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **PUT /templates/:id** | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **DELETE /templates/:id** | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **GET /audit-logs** | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| **GET /*/logs** | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |

#### RBAC Enforcement Flow

```
Incoming Request
  │
  ├─> Extract User Context (from Lambda Authorizer)
  │   {
  │     "userId": "user-123",
  │     "email": "user@example.com",
  │     "roles": ["Deployment Manager", "Developer"]
  │   }
  │
  ├─> Extract Resource & Action
  │   {
  │     "resource": "deployment",
  │     "action": "deploy",
  │     "resourceId": "D1BRV40"
  │   }
  │
  ├─> Load Permission Rules
  │   [
  │     { "role": "Deployment Manager", "resource": "deployment", "actions": ["create", "read", "update", "delete", "deploy", "destroy"] },
  │     { "role": "Developer", "resource": "deployment", "actions": ["read"] }
  │   ]
  │
  ├─> Evaluate Permissions
  │   - Check if any user role has permission for this action
  │   - Result: ALLOWED (Deployment Manager role has "deploy" permission)
  │
  └─> Allow Request / Deny with 403 Forbidden
```

### API Key Authentication (Alternative)

For service-to-service communication and CI/CD pipelines:

```bash
# Generate API key
curl -X POST https://api.example.com/api/v1/auth/api-keys \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "description": "GitHub Actions deployment key",
    "expiresIn": 31536000,
    "permissions": ["deployments:deploy", "stacks:deploy"]
  }'

# Response
{
  "apiKey": "msk_live_1234567890abcdef",
  "keyId": "key-abc123",
  "createdAt": "2025-10-09T12:00:00Z",
  "expiresAt": "2026-10-06T12:00:00Z"
}

# Use API key in requests
curl -X POST https://api.example.com/api/v1/deployments/D1BRV40/deploy \
  -H "X-API-Key: msk_live_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{ "environment": "dev" }'
```

---

## API Endpoints Reference

### Base URL

```
Production: https://api.example.com/api/v1
Stage: https://stage-api.example.com/api/v1
Development: http://localhost:3000/api/v1
```

### Endpoint Categories

1. [Authentication](#authentication-endpoints) - Login, logout, token management
2. [Deployments](#deployment-endpoints) - CRUD operations, deploy, destroy
3. [Stacks](#stack-endpoints) - Stack management, individual deployment
4. [Environments](#environment-endpoints) - Enable, disable, list environments
5. [Templates](#template-endpoints) - Template CRUD, validation
6. [State Management](#state-endpoints) - Export, import, sync
7. [Monitoring](#monitoring-endpoints) - Status, logs, metrics

---

### Authentication Endpoints

#### POST /auth/login

Authenticate user and receive JWT tokens.

**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "SecurePassword123!",
  "mfaCode": "123456"  // Optional, if MFA enabled
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "idToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600,
    "tokenType": "Bearer",
    "user": {
      "id": "user-123",
      "email": "user@example.com",
      "name": "John Doe",
      "roles": ["Deployment Manager", "Developer"]
    }
  }
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account locked or disabled
- `400 Bad Request`: Missing or invalid MFA code

---

#### POST /auth/logout

Invalidate current access token.

**Request:**
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

---

#### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "idToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600,
    "tokenType": "Bearer"
  }
}
```

---

#### POST /auth/api-keys

Generate API key for programmatic access.

**Request:**
```http
POST /api/v1/auth/api-keys
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "CI/CD Pipeline Key",
  "description": "GitHub Actions deployment automation",
  "expiresIn": 31536000,  // 1 year in seconds
  "permissions": [
    "deployments:read",
    "deployments:deploy",
    "stacks:deploy",
    "logs:read"
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "apiKey": "msk_live_1234567890abcdef1234567890abcdef",
    "keyId": "key-abc123",
    "name": "CI/CD Pipeline Key",
    "createdAt": "2025-10-09T12:00:00Z",
    "expiresAt": "2026-10-06T12:00:00Z",
    "permissions": [
      "deployments:read",
      "deployments:deploy",
      "stacks:deploy",
      "logs:read"
    ]
  },
  "warning": "This API key will only be displayed once. Store it securely."
}
```

---

#### GET /auth/api-keys

List all API keys for current user.

**Request:**
```http
GET /api/v1/auth/api-keys
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "apiKeys": [
      {
        "keyId": "key-abc123",
        "name": "CI/CD Pipeline Key",
        "createdAt": "2025-10-09T12:00:00Z",
        "expiresAt": "2026-10-06T12:00:00Z",
        "lastUsedAt": "2025-10-09T14:30:00Z",
        "status": "active"
      }
    ],
    "total": 1
  }
}
```

---

#### DELETE /auth/api-keys/:keyId

Revoke API key.

**Request:**
```http
DELETE /api/v1/auth/api-keys/key-abc123
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "API key revoked successfully"
}
```

---

### Deployment Endpoints

#### POST /deployments

Create new deployment (equivalent to `cloud init`).

**Request:**
```http
POST /api/v1/deployments
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "organization": "CompanyA",
  "project": "ecommerce",
  "domain": "ecommerce.companyA.com",
  "template": "default",
  "region": "us-east-1",
  "accounts": {
    "dev": "111111111111",
    "stage": "222222222222",
    "prod": "333333333333"
  },
  "contact": {
    "email": "devops@companyA.com",
    "team": "Platform Team"
  },
  "tags": {
    "Department": "Engineering",
    "CostCenter": "CC-1234"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "organization": "CompanyA",
    "project": "ecommerce",
    "domain": "ecommerce.companyA.com",
    "template": "default",
    "status": "initialized",
    "createdAt": "2025-10-09T12:00:00Z",
    "createdBy": "user@example.com",
    "directory": "./cloud/deploy/D1BRV40-CompanyA-ecommerce",
    "environments": [
      {
        "name": "dev",
        "enabled": true,
        "region": "us-east-1",
        "account": "111111111111",
        "status": "ready"
      },
      {
        "name": "stage",
        "enabled": false,
        "region": "us-east-1",
        "account": "222222222222",
        "status": "disabled"
      },
      {
        "name": "prod",
        "enabled": false,
        "region": "us-west-2",
        "account": "333333333333",
        "status": "disabled"
      }
    ],
    "stacks": [
      {
        "name": "network",
        "layer": 1,
        "status": "pending",
        "dependencies": []
      },
      {
        "name": "security",
        "layer": 2,
        "status": "pending",
        "dependencies": ["network"]
      }
      // ... (all 16 stacks)
    ]
  }
}
```

---

#### GET /deployments

List all deployments.

**Request:**
```http
GET /api/v1/deployments?page=1&limit=20&status=active&organization=CompanyA
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (initialized, deploying, deployed, failed, destroying)
- `organization` (string): Filter by organization
- `project` (string): Filter by project
- `template` (string): Filter by template
- `environment` (string): Filter by environment
- `sortBy` (string): Sort field (createdAt, updatedAt, deploymentId)
- `sortOrder` (string): Sort order (asc, desc)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deployments": [
      {
        "deploymentId": "D1BRV40",
        "organization": "CompanyA",
        "project": "ecommerce",
        "domain": "ecommerce.companyA.com",
        "template": "default",
        "status": "deployed",
        "environments": {
          "dev": { "enabled": true, "status": "deployed" },
          "stage": { "enabled": true, "status": "deployed" },
          "prod": { "enabled": false, "status": "disabled" }
        },
        "createdAt": "2025-10-09T12:00:00Z",
        "updatedAt": "2025-10-09T14:30:00Z",
        "lastDeployedAt": "2025-10-09T14:30:00Z"
      }
      // ... more deployments
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "totalPages": 3
    }
  }
}
```

---

#### GET /deployments/:deploymentId

Get deployment details.

**Request:**
```http
GET /api/v1/deployments/D1BRV40
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "organization": "CompanyA",
    "project": "ecommerce",
    "domain": "ecommerce.companyA.com",
    "template": "default",
    "status": "deployed",
    "directory": "./cloud/deploy/D1BRV40-CompanyA-ecommerce",
    "createdAt": "2025-10-09T12:00:00Z",
    "updatedAt": "2025-10-09T14:30:00Z",
    "createdBy": "user@example.com",
    "lastDeployedAt": "2025-10-09T14:30:00Z",
    "lastDeployedBy": "user@example.com",
    "contact": {
      "email": "devops@companyA.com",
      "team": "Platform Team"
    },
    "tags": {
      "Department": "Engineering",
      "CostCenter": "CC-1234"
    },
    "environments": [
      {
        "name": "dev",
        "enabled": true,
        "region": "us-east-1",
        "account": "111111111111",
        "status": "deployed",
        "stacksDeployed": 16,
        "stacksFailed": 0,
        "lastDeployedAt": "2025-10-09T14:30:00Z",
        "endpoints": {
          "apiGateway": "https://api-dev.ecommerce.companyA.com",
          "cloudfront": "https://cdn-dev.ecommerce.companyA.com"
        }
      }
    ],
    "stacks": [
      {
        "name": "network",
        "layer": 1,
        "status": "deployed",
        "dependencies": [],
        "outputs": {
          "vpcId": "vpc-0abc123",
          "privateSubnetIds": ["subnet-111", "subnet-222"]
        },
        "resourceCount": 15,
        "lastDeployedAt": "2025-10-09T14:10:00Z"
      }
      // ... all stacks
    ],
    "manifest": {
      "version": "3.0",
      "template": "default",
      "environments": [...],
      "stacks": [...]
    },
    "metrics": {
      "totalResources": 245,
      "deploymentDuration": 1825,  // seconds
      "estimatedMonthlyCost": 1250.50  // USD
    }
  }
}
```

---

#### PUT /deployments/:deploymentId

Update deployment configuration.

**Request:**
```http
PUT /api/v1/deployments/D1BRV40
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "contact": {
    "email": "new-devops@companyA.com",
    "team": "Platform Engineering"
  },
  "tags": {
    "Department": "Engineering",
    "CostCenter": "CC-5678",
    "Environment": "Production"
  },
  "manifest": {
    // Updated manifest content
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "updatedAt": "2025-10-09T15:00:00Z",
    "updatedBy": "user@example.com",
    "changes": [
      "contact.email: devops@companyA.com → new-devops@companyA.com",
      "contact.team: Platform Team → Platform Engineering",
      "tags.CostCenter: CC-1234 → CC-5678",
      "tags.Environment: <new> → Production"
    ]
  }
}
```

---

#### DELETE /deployments/:deploymentId

Delete deployment (must destroy all stacks first).

**Request:**
```http
DELETE /api/v1/deployments/D1BRV40?force=false
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `force` (boolean): Force delete without destroying stacks (dangerous, default: false)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Deployment D1BRV40 deleted successfully",
  "data": {
    "deploymentId": "D1BRV40",
    "deletedAt": "2025-10-09T15:30:00Z",
    "deletedBy": "user@example.com"
  }
}
```

**Error (400 Bad Request) - Stacks still deployed:**
```json
{
  "success": false,
  "error": {
    "code": "DEPLOYMENT_HAS_ACTIVE_STACKS",
    "message": "Cannot delete deployment with active stacks",
    "details": {
      "activeStacks": ["network", "security", "compute-ec2"],
      "environments": ["dev", "stage"],
      "suggestion": "Run destroy operation first or use force=true to delete"
    }
  }
}
```

---

#### POST /deployments/:deploymentId/deploy

Deploy all stacks in deployment (equivalent to `cloud deploy`).

**v3.0 Features:**
- **Smart Skip Logic**: Automatically skips stacks with no configuration changes
- **Layer-Based Parallel Execution**: Deploys stacks in parallel within dependency layers
- **WebSocket Monitoring**: Real-time progress updates via WebSocket connections (ws://)
- **Template-Based Dependency Resolution**: Intelligent dependency graph resolution

**Request:**
```http
POST /api/v1/deployments/D1BRV40/deploy
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev",
  "preview": false,
  "parallel": true,
  "continueOnError": false,
  "smartSkip": true,  // v3.0: Skip unchanged stacks
  "stackFilter": ["network", "security", "compute-*"],  // Optional: deploy specific stacks
  "webhookUrl": "https://webhook.example.com/deployment-status"  // Optional: status callbacks
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Deployment started",
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "operationId": "op-abc123",
    "status": "in_progress",
    "startedAt": "2025-10-09T16:00:00Z",
    "startedBy": "user@example.com",
    "estimatedDuration": 1800,  // seconds
    "stacksToDeploy": [
      {
        "name": "network",
        "layer": 1,
        "status": "pending",
        "estimatedDuration": 300
      },
      {
        "name": "security",
        "layer": 2,
        "status": "pending",
        "estimatedDuration": 180
      }
      // ... all stacks
    ],
    "stacksSkipped": [
      {
        "name": "monitoring",
        "layer": 5,
        "reason": "No configuration changes detected",
        "lastDeployed": "2025-10-08T10:00:00Z"
      }
    ],
    "websocketChannel": "ws://api.example.com/deployments/D1BRV40/operations/op-abc123",
    "statusUrl": "/api/v1/deployments/D1BRV40/operations/op-abc123"
  }
}
```

---

#### POST /deployments/:deploymentId/destroy

Destroy all stacks in deployment (equivalent to `cloud destroy`).

**v3.0 Features:**
- **Layer-Based Parallel Execution**: Destroys stacks in parallel within reverse dependency layers
- **WebSocket Monitoring**: Real-time progress updates via ws:// endpoints

**Request:**
```http
POST /api/v1/deployments/D1BRV40/destroy
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev",
  "preview": false,
  "skipConfirmation": false,
  "stackFilter": ["compute-*", "data-*"]  // Optional: destroy specific stacks
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Destroy operation started",
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "operationId": "op-def456",
    "status": "in_progress",
    "startedAt": "2025-10-09T16:30:00Z",
    "startedBy": "user@example.com",
    "estimatedDuration": 1200,
    "stacksToDestroy": [
      // ... stacks in reverse dependency order
    ],
    "websocketChannel": "deployments/D1BRV40/operations/op-def456",
    "statusUrl": "/api/v1/deployments/D1BRV40/operations/op-def456"
  }
}
```

---

#### POST /deployments/:deploymentId/validate

Validate deployment configuration (equivalent to `cloud validate`).

**Request:**
```http
POST /api/v1/deployments/D1BRV40/validate
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev",
  "checks": [
    "manifest",
    "dependencies",
    "aws-credentials",
    "pulumi-state",
    "runtime-placeholders"
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "valid": true,
    "checks": [
      {
        "name": "manifest",
        "status": "passed",
        "message": "Manifest syntax valid"
      },
      {
        "name": "dependencies",
        "status": "passed",
        "message": "No circular dependencies detected"
      },
      {
        "name": "aws-credentials",
        "status": "passed",
        "message": "AWS credentials valid for account 111111111111"
      },
      {
        "name": "pulumi-state",
        "status": "passed",
        "message": "All stack states accessible"
      },
      {
        "name": "runtime-placeholders",
        "status": "passed",
        "message": "All placeholders resolvable"
      }
    ],
    "warnings": [
      {
        "code": "HIGH_ESTIMATED_COST",
        "message": "Estimated monthly cost ($1250.50) exceeds typical range",
        "severity": "warning"
      }
    ],
    "errors": []
  }
}
```

**Response (200 OK) - Validation Failed:**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "valid": false,
    "checks": [
      {
        "name": "dependencies",
        "status": "failed",
        "message": "Circular dependency detected",
        "details": {
          "cycle": ["compute-ec2", "data-rds", "compute-ec2"]
        }
      },
      {
        "name": "runtime-placeholders",
        "status": "failed",
        "message": "Unresolvable placeholders found",
        "details": {
          "placeholders": [
            "{{RUNTIME:nonexistent-stack:vpcId}}"
          ]
        }
      }
    ],
    "errors": [
      {
        "code": "CIRCULAR_DEPENDENCY",
        "message": "Circular dependency: compute-ec2 → data-rds → compute-ec2",
        "stack": "compute-ec2"
      },
      {
        "code": "UNRESOLVABLE_PLACEHOLDER",
        "message": "Cannot resolve placeholder: {{RUNTIME:nonexistent-stack:vpcId}}",
        "stack": "data-rds",
        "field": "subnetIds"
      }
    ]
  }
}
```

---

#### GET /deployments/:deploymentId/operations/:operationId

Get operation status (deploy, destroy, etc.).

**Request:**
```http
GET /api/v1/deployments/D1BRV40/operations/op-abc123
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "operationId": "op-abc123",
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "type": "deploy",
    "status": "in_progress",
    "startedAt": "2025-10-09T16:00:00Z",
    "startedBy": "user@example.com",
    "progress": {
      "totalStacks": 16,
      "completedStacks": 8,
      "failedStacks": 0,
      "inProgressStacks": 2,
      "pendingStacks": 6,
      "percentage": 50
    },
    "currentStacks": [
      {
        "name": "compute-ec2",
        "status": "deploying",
        "startedAt": "2025-10-09T16:15:00Z",
        "progress": 65,
        "resourcesCreated": 12,
        "resourcesTotal": 18
      },
      {
        "name": "compute-ecs",
        "status": "deploying",
        "startedAt": "2025-10-09T16:15:00Z",
        "progress": 40,
        "resourcesCreated": 8,
        "resourcesTotal": 20
      }
    ],
    "completedStacks": [
      {
        "name": "network",
        "status": "deployed",
        "startedAt": "2025-10-09T16:00:00Z",
        "completedAt": "2025-10-09T16:05:00Z",
        "duration": 300,
        "resourcesCreated": 15
      }
      // ... more completed stacks
    ],
    "estimatedTimeRemaining": 900,  // seconds
    "logs": [
      {
        "timestamp": "2025-10-09T16:15:30Z",
        "level": "info",
        "stack": "compute-ec2",
        "message": "Creating EC2 instance i-abc123..."
      }
    ]
  }
}
```

---

### Stack Endpoints

#### GET /stacks

List all registered stacks.

**Request:**
```http
GET /api/v1/stacks?category=compute&layer=3
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `category` (string): Filter by category (network, security, compute, data, analytics, ml, devops)
- `layer` (integer): Filter by dependency layer
- `template` (string): Filter by template

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "stacks": [
      {
        "name": "network",
        "displayName": "Network Infrastructure",
        "description": "VPC, subnets, route tables, NAT gateways",
        "category": "network",
        "layer": 1,
        "dependencies": [],
        "outputs": ["vpcId", "privateSubnetIds", "publicSubnetIds"],
        "estimatedResources": 15,
        "estimatedDuration": 300,
        "templates": ["default", "minimal", "microservices", "data-platform"]
      },
      {
        "name": "compute-ec2",
        "displayName": "EC2 Compute",
        "description": "EC2 instances, auto-scaling groups, load balancers",
        "category": "compute",
        "layer": 3,
        "dependencies": ["network", "security"],
        "outputs": ["instanceIds", "loadBalancerDns"],
        "estimatedResources": 18,
        "estimatedDuration": 420,
        "templates": ["default", "microservices"]
      }
      // ... all 16 stacks
    ],
    "total": 16
  }
}
```

---

#### GET /stacks/:stackName

Get stack details.

**Request:**
```http
GET /api/v1/stacks/network
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "name": "network",
    "displayName": "Network Infrastructure",
    "description": "VPC, subnets, route tables, NAT gateways, VPC endpoints",
    "category": "network",
    "layer": 1,
    "dependencies": [],
    "dependents": ["security", "compute-ec2", "compute-ecs", "data-rds", "data-s3"],
    "outputs": {
      "vpcId": {
        "type": "string",
        "description": "VPC ID"
      },
      "privateSubnetIds": {
        "type": "array",
        "description": "Private subnet IDs"
      },
      "publicSubnetIds": {
        "type": "array",
        "description": "Public subnet IDs"
      }
    },
    "configuration": {
      "vpcCidr": {
        "type": "string",
        "description": "VPC CIDR block",
        "default": "10.0.0.0/16"
      },
      "availabilityZones": {
        "type": "integer",
        "description": "Number of availability zones",
        "default": 2,
        "min": 2,
        "max": 3
      }
    },
    "resources": [
      {
        "type": "aws:ec2/vpc:Vpc",
        "description": "Main VPC"
      },
      {
        "type": "aws:ec2/subnet:Subnet",
        "description": "Private subnets (per AZ)"
      },
      {
        "type": "aws:ec2/subnet:Subnet",
        "description": "Public subnets (per AZ)"
      }
      // ... all resource types
    ],
    "estimatedResources": 15,
    "estimatedDuration": 300,
    "estimatedMonthlyCost": 85.00,
    "templates": ["default", "minimal", "microservices", "data-platform"],
    "documentation": "https://docs.example.com/stacks/network"
  }
}
```

---

#### POST /stacks

Register new stack (equivalent to `cloud register-stack`).

**Request:**
```http
POST /api/v1/stacks
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "custom-monitoring",
  "displayName": "Custom Monitoring Stack",
  "description": "CloudWatch dashboards, alarms, and custom metrics",
  "category": "devops",
  "layer": 5,
  "dependencies": ["network", "security", "compute-ec2"],
  "outputs": {
    "dashboardUrl": {
      "type": "string",
      "description": "CloudWatch dashboard URL"
    }
  },
  "configuration": {
    "alarmEmail": {
      "type": "string",
      "description": "Email for alarm notifications",
      "required": true
    }
  },
  "stackDefinition": {
    // Stack template YAML content
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "name": "custom-monitoring",
    "displayName": "Custom Monitoring Stack",
    "registeredAt": "2025-10-09T17:00:00Z",
    "registeredBy": "user@example.com",
    "status": "active"
  }
}
```

---

#### PUT /stacks/:stackName

Update stack definition.

**Request:**
```http
PUT /api/v1/stacks/custom-monitoring
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "description": "Enhanced monitoring with custom metrics and dashboards",
  "layer": 6,
  "configuration": {
    "alarmEmail": {
      "type": "string",
      "description": "Email for alarm notifications",
      "required": true
    },
    "slackWebhook": {
      "type": "string",
      "description": "Slack webhook for notifications",
      "required": false
    }
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "name": "custom-monitoring",
    "updatedAt": "2025-10-09T17:30:00Z",
    "updatedBy": "user@example.com",
    "changes": [
      "description updated",
      "layer: 5 → 6",
      "configuration: added slackWebhook"
    ]
  }
}
```

---

#### DELETE /stacks/:stackName

Unregister stack (equivalent to `cloud unregister-stack`).

**Request:**
```http
DELETE /api/v1/stacks/custom-monitoring?force=false
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Stack unregistered successfully",
  "data": {
    "name": "custom-monitoring",
    "unregisteredAt": "2025-10-09T18:00:00Z",
    "unregisteredBy": "user@example.com"
  }
}
```

---

#### POST /deployments/:deploymentId/stacks/:stackName/deploy

Deploy single stack (equivalent to `cloud deploy-stack`).

**Request:**
```http
POST /api/v1/deployments/D1BRV40/stacks/network/deploy
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev",
  "preview": false,
  "force": false
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Stack deployment started",
  "data": {
    "deploymentId": "D1BRV40",
    "stackName": "network",
    "environment": "dev",
    "operationId": "op-ghi789",
    "status": "in_progress",
    "startedAt": "2025-10-09T18:30:00Z",
    "startedBy": "user@example.com",
    "estimatedDuration": 300,
    "websocketChannel": "deployments/D1BRV40/stacks/network/operations/op-ghi789",
    "statusUrl": "/api/v1/deployments/D1BRV40/stacks/network/operations/op-ghi789"
  }
}
```

---

#### POST /deployments/:deploymentId/stacks/:stackName/destroy

Destroy single stack (equivalent to `cloud destroy-stack`).

**Request:**
```http
POST /api/v1/deployments/D1BRV40/stacks/network/destroy
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev",
  "preview": false,
  "force": false
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Stack destroy operation started",
  "data": {
    "deploymentId": "D1BRV40",
    "stackName": "network",
    "environment": "dev",
    "operationId": "op-jkl012",
    "status": "in_progress",
    "startedAt": "2025-10-09T19:00:00Z",
    "startedBy": "user@example.com",
    "estimatedDuration": 240,
    "websocketChannel": "deployments/D1BRV40/stacks/network/operations/op-jkl012",
    "statusUrl": "/api/v1/deployments/D1BRV40/stacks/network/operations/op-jkl012"
  }
}
```

---

#### GET /deployments/:deploymentId/stacks/:stackName/status

Get stack status in deployment.

**Request:**
```http
GET /api/v1/deployments/D1BRV40/stacks/network/status?environment=dev
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "stackName": "network",
    "environment": "dev",
    "status": "deployed",
    "lastDeployedAt": "2025-10-09T14:10:00Z",
    "lastDeployedBy": "user@example.com",
    "outputs": {
      "vpcId": "vpc-0abc123",
      "privateSubnetIds": ["subnet-111", "subnet-222"],
      "publicSubnetIds": ["subnet-333", "subnet-444"]
    },
    "resources": [
      {
        "type": "aws:ec2/vpc:Vpc",
        "name": "main-vpc",
        "id": "vpc-0abc123",
        "status": "created"
      },
      {
        "type": "aws:ec2/subnet:Subnet",
        "name": "private-subnet-1",
        "id": "subnet-111",
        "status": "created"
      }
      // ... all resources
    ],
    "resourceCount": 15,
    "deploymentDuration": 300,
    "driftDetected": false
  }
}
```

---

### Environment Endpoints

#### GET /deployments/:deploymentId/environments

List environments for deployment.

**Request:**
```http
GET /api/v1/deployments/D1BRV40/environments
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "environments": [
      {
        "name": "dev",
        "enabled": true,
        "region": "us-east-1",
        "account": "111111111111",
        "status": "deployed",
        "stacksDeployed": 16,
        "stacksFailed": 0,
        "lastDeployedAt": "2025-10-09T14:30:00Z",
        "endpoints": {
          "apiGateway": "https://api-dev.ecommerce.companyA.com",
          "cloudfront": "https://cdn-dev.ecommerce.companyA.com"
        },
        "estimatedMonthlyCost": 850.00
      },
      {
        "name": "stage",
        "enabled": true,
        "region": "us-east-1",
        "account": "222222222222",
        "status": "deployed",
        "stacksDeployed": 16,
        "stacksFailed": 0,
        "lastDeployedAt": "2025-10-05T10:00:00Z",
        "estimatedMonthlyCost": 1100.00
      },
      {
        "name": "prod",
        "enabled": false,
        "region": "us-west-2",
        "account": "333333333333",
        "status": "disabled"
      }
    ],
    "total": 3
  }
}
```

---

#### POST /deployments/:deploymentId/environments/:environmentName/enable

Enable environment (equivalent to `cloud enable-environment`).

**Request:**
```http
POST /api/v1/deployments/D1BRV40/environments/stage/enable
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "autoDeploy": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Environment enabled successfully",
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "stage",
    "enabled": true,
    "enabledAt": "2025-10-09T19:30:00Z",
    "enabledBy": "user@example.com",
    "status": "ready"
  }
}
```

---

#### POST /deployments/:deploymentId/environments/:environmentName/disable

Disable environment (equivalent to `cloud disable-environment`).

**Request:**
```http
POST /api/v1/deployments/D1BRV40/environments/stage/disable
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "destroyResources": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Environment disabled successfully",
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "stage",
    "enabled": false,
    "disabledAt": "2025-10-09T20:00:00Z",
    "disabledBy": "user@example.com",
    "status": "disabled"
  }
}
```

---

### Template Endpoints

#### GET /templates

List all templates (equivalent to `cloud list-templates`).

**Request:**
```http
GET /api/v1/templates
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "name": "default",
        "displayName": "Default Template",
        "description": "Balanced infrastructure with all core services",
        "type": "built-in",
        "stacks": ["network", "security", "compute-ec2", "compute-ecs", "data-rds", "data-s3", "api-gateway", "cdn-cloudfront", "cicd-codepipeline", "monitoring", "backup"],
        "estimatedResources": 180,
        "estimatedMonthlyCost": 1250.00,
        "createdAt": "2025-01-01T00:00:00Z"
      },
      {
        "name": "minimal",
        "displayName": "Minimal Template",
        "description": "Essential infrastructure only",
        "type": "built-in",
        "stacks": ["network", "security", "compute-ec2", "data-s3"],
        "estimatedResources": 45,
        "estimatedMonthlyCost": 350.00,
        "createdAt": "2025-01-01T00:00:00Z"
      },
      {
        "name": "microservices",
        "displayName": "Microservices Template",
        "description": "Container-based microservices architecture",
        "type": "built-in",
        "stacks": ["network", "security", "compute-ecs", "data-rds", "data-elasticache", "api-gateway", "cicd-codepipeline", "monitoring"],
        "estimatedResources": 150,
        "estimatedMonthlyCost": 1850.00,
        "createdAt": "2025-01-01T00:00:00Z"
      },
      {
        "name": "data-platform",
        "displayName": "Data Platform Template",
        "description": "Analytics and ML workloads",
        "type": "built-in",
        "stacks": ["network", "security", "data-s3", "data-redshift", "analytics-emr", "analytics-glue", "ml-sagemaker"],
        "estimatedResources": 95,
        "estimatedMonthlyCost": 2400.00,
        "createdAt": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 4
  }
}
```

---

#### GET /templates/:templateName

Get template details (equivalent to `cloud show-template`).

**Request:**
```http
GET /api/v1/templates/default
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "name": "default",
    "displayName": "Default Template",
    "description": "Balanced infrastructure with all core services",
    "type": "built-in",
    "version": "3.0.0",
    "stacks": [
      {
        "name": "network",
        "layer": 1,
        "required": true,
        "description": "VPC, subnets, NAT gateways"
      },
      {
        "name": "security",
        "layer": 2,
        "required": true,
        "description": "Security groups, WAF, IAM roles"
      }
      // ... all stacks
    ],
    "defaultConfig": {
      "network": {
        "vpcCidr": "10.0.0.0/16",
        "availabilityZones": 2
      },
      "compute-ec2": {
        "instanceType": "t3.medium",
        "minInstances": 2,
        "maxInstances": 10
      }
      // ... default config for all stacks
    },
    "environments": {
      "dev": {
        "region": "us-east-1",
        "enabled": true
      },
      "stage": {
        "region": "us-east-1",
        "enabled": false
      },
      "prod": {
        "region": "us-west-2",
        "enabled": false
      }
    },
    "estimatedResources": 180,
    "estimatedMonthlyCost": 1250.00,
    "deploymentTime": 1800,
    "createdAt": "2025-01-01T00:00:00Z",
    "documentation": "https://docs.example.com/templates/default"
  }
}
```

---

#### POST /templates

Create custom template (equivalent to `cloud create-template`).

**Request:**
```http
POST /api/v1/templates
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "custom-ml-platform",
  "displayName": "Custom ML Platform",
  "description": "Custom machine learning platform with data pipelines",
  "stacks": [
    "network",
    "security",
    "data-s3",
    "data-redshift",
    "ml-sagemaker",
    "analytics-glue",
    "cicd-codepipeline"
  ],
  "defaultConfig": {
    "network": {
      "vpcCidr": "10.0.0.0/16",
      "availabilityZones": 3
    },
    "ml-sagemaker": {
      "instanceType": "ml.m5.xlarge",
      "enableSpotInstances": true
    }
  },
  "environments": {
    "dev": {
      "region": "us-east-1",
      "enabled": true
    },
    "prod": {
      "region": "us-west-2",
      "enabled": false
    }
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "name": "custom-ml-platform",
    "displayName": "Custom ML Platform",
    "type": "custom",
    "createdAt": "2025-10-09T20:30:00Z",
    "createdBy": "user@example.com",
    "version": "1.0.0",
    "status": "active"
  }
}
```

---

#### PUT /templates/:templateName

Update template (equivalent to `cloud update-template`).

**Request:**
```http
PUT /api/v1/templates/custom-ml-platform
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "description": "Enhanced ML platform with real-time inference",
  "stacks": [
    "network",
    "security",
    "data-s3",
    "data-redshift",
    "ml-sagemaker",
    "analytics-glue",
    "compute-lambda",
    "cicd-codepipeline"
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "name": "custom-ml-platform",
    "version": "1.1.0",
    "updatedAt": "2025-10-09T21:00:00Z",
    "updatedBy": "user@example.com",
    "changes": [
      "description updated",
      "stacks: added compute-lambda",
      "version: 1.0.0 → 1.1.0"
    ]
  }
}
```

---

#### DELETE /templates/:templateName

Delete template.

**Request:**
```http
DELETE /api/v1/templates/custom-ml-platform
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Template deleted successfully",
  "data": {
    "name": "custom-ml-platform",
    "deletedAt": "2025-10-09T21:30:00Z",
    "deletedBy": "user@example.com"
  }
}
```

---

#### POST /templates/:templateName/validate

Validate template (equivalent to `cloud validate-template`).

**Request:**
```http
POST /api/v1/templates/custom-ml-platform/validate
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "templateName": "custom-ml-platform",
    "valid": true,
    "checks": [
      {
        "name": "stack-definitions",
        "status": "passed",
        "message": "All referenced stacks exist"
      },
      {
        "name": "dependencies",
        "status": "passed",
        "message": "No circular dependencies"
      },
      {
        "name": "configuration",
        "status": "passed",
        "message": "All required config fields present"
      }
    ],
    "warnings": [],
    "errors": []
  }
}
```

---

### State Endpoints

#### GET /deployments/:deploymentId/state/export

Export deployment state (equivalent to `pulumi stack export`).

**Request:**
```http
GET /api/v1/deployments/D1BRV40/state/export?environment=dev&stack=network
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `environment` (string): Environment name
- `stack` (string): Optional - specific stack (exports all if not specified)
- `format` (string): Export format (json, yaml) - default: json

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "stack": "network",
    "exportedAt": "2025-10-09T22:00:00Z",
    "state": {
      "version": 3,
      "deployment": {
        "manifest": {...},
        "resources": [...]
      }
    }
  }
}
```

---

#### POST /deployments/:deploymentId/state/import

Import deployment state (equivalent to `pulumi stack import`).

**Request:**
```http
POST /api/v1/deployments/D1BRV40/state/import
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev",
  "stack": "network",
  "state": {
    // State JSON
  },
  "force": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "State imported successfully",
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "stack": "network",
    "importedAt": "2025-10-09T22:30:00Z",
    "importedBy": "user@example.com"
  }
}
```

---

#### POST /deployments/:deploymentId/state/sync

Sync state with Pulumi Cloud.

**Request:**
```http
POST /api/v1/deployments/D1BRV40/state/sync
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "environment": "dev"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "State synced successfully",
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "syncedAt": "2025-10-09T23:00:00Z",
    "stacksSynced": 16,
    "conflicts": 0
  }
}
```

---

### Monitoring Endpoints

#### GET /deployments/:deploymentId/logs

Get deployment logs (equivalent to `cloud logs`).

**Request:**
```http
GET /api/v1/deployments/D1BRV40/logs?environment=dev&stack=network&level=info&limit=100&since=1h
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `environment` (string): Environment filter
- `stack` (string): Stack filter
- `level` (string): Log level (debug, info, warn, error)
- `limit` (integer): Max logs to return (default: 100, max: 1000)
- `since` (string): Time range (1h, 24h, 7d, etc.)
- `search` (string): Search term in log messages

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "logs": [
      {
        "timestamp": "2025-10-09T14:10:30.123Z",
        "level": "info",
        "stack": "network",
        "operation": "deploy",
        "message": "Creating VPC vpc-0abc123...",
        "metadata": {
          "resourceType": "aws:ec2/vpc:Vpc",
          "resourceName": "main-vpc"
        }
      },
      {
        "timestamp": "2025-10-09T14:10:35.456Z",
        "level": "info",
        "stack": "network",
        "operation": "deploy",
        "message": "VPC created successfully",
        "metadata": {
          "resourceId": "vpc-0abc123",
          "duration": 5.3
        }
      }
      // ... more logs
    ],
    "total": 247,
    "returned": 100
  }
}
```

---

#### GET /deployments/:deploymentId/metrics

Get deployment metrics.

**Request:**
```http
GET /api/v1/deployments/D1BRV40/metrics?environment=dev&period=24h
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `environment` (string): Environment filter
- `period` (string): Time period (1h, 24h, 7d, 30d)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "period": "24h",
    "metrics": {
      "deployments": {
        "total": 12,
        "successful": 11,
        "failed": 1,
        "averageDuration": 1650
      },
      "resources": {
        "total": 245,
        "created": 15,
        "updated": 8,
        "deleted": 2,
        "failed": 1
      },
      "costs": {
        "estimatedMonthly": 1250.50,
        "trend": "+5.2%"
      },
      "stacks": [
        {
          "name": "network",
          "deployments": 2,
          "averageDuration": 305,
          "successRate": 100
        }
        // ... all stacks
      ]
    }
  }
}
```

---

#### GET /health

API health check.

**Request:**
```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2025-10-09T23:30:00Z",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "pulumi": "healthy",
    "aws": "healthy"
  }
}
```

---

## WebSocket Real-Time Updates

**v3.0 Enhancement**: All WebSocket channels now support both secure (wss://) and non-secure (ws://) connections for local development. Production environments enforce wss:// only.

### Connection Establishment

#### Connect to WebSocket

```javascript
// JavaScript WebSocket Client
// Production: wss://api.example.com/ws
// Development: ws://localhost:3000/ws
const ws = new WebSocket('wss://api.example.com/ws');

// Add authentication token
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'
  }));
};

// Handle authentication response
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'authenticated') {
    console.log('Authenticated successfully');

    // Subscribe to deployment updates
    ws.send(JSON.stringify({
      type: 'subscribe',
      channel: 'deployments/D1BRV40/operations/op-abc123'
    }));
  }
};
```

### WebSocket Channels

| Channel Pattern | Description |
|----------------|-------------|
| `deployments/:deploymentId/operations/:operationId` | Real-time updates for specific operation |
| `deployments/:deploymentId` | All events for deployment |
| `deployments/:deploymentId/stacks/:stackName` | Events for specific stack |
| `deployments/:deploymentId/environments/:environment` | Environment-specific events |

### Message Types

#### 1. Operation Started

```json
{
  "type": "operation.started",
  "timestamp": "2025-10-09T16:00:00.000Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "operationType": "deploy",
    "environment": "dev",
    "startedBy": "user@example.com",
    "stacksToProcess": 16
  }
}
```

#### 2. Stack Started

```json
{
  "type": "stack.started",
  "timestamp": "2025-10-09T16:00:05.000Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "stackName": "network",
    "layer": 1,
    "estimatedDuration": 300
  }
}
```

#### 3. Stack Progress

```json
{
  "type": "stack.progress",
  "timestamp": "2025-10-09T16:01:30.000Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "stackName": "network",
    "progress": 35,
    "resourcesProcessed": 8,
    "resourcesTotal": 15,
    "currentResource": {
      "type": "aws:ec2/subnet:Subnet",
      "name": "private-subnet-2",
      "action": "creating"
    }
  }
}
```

#### 4. Stack Completed

```json
{
  "type": "stack.completed",
  "timestamp": "2025-10-09T16:05:00.000Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "stackName": "network",
    "status": "deployed",
    "duration": 295,
    "resourcesCreated": 15,
    "outputs": {
      "vpcId": "vpc-0abc123",
      "privateSubnetIds": ["subnet-111", "subnet-222"]
    }
  }
}
```

#### 5. Stack Failed

```json
{
  "type": "stack.failed",
  "timestamp": "2025-10-09T16:05:00.000Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "stackName": "compute-ec2",
    "error": {
      "code": "RESOURCE_CREATION_FAILED",
      "message": "Failed to create EC2 instance: Insufficient capacity",
      "resource": {
        "type": "aws:ec2/instance:Instance",
        "name": "web-server-1"
      }
    }
  }
}
```

#### 6. Operation Completed

```json
{
  "type": "operation.completed",
  "timestamp": "2025-10-09T16:30:00.000Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "operationType": "deploy",
    "environment": "dev",
    "status": "success",
    "duration": 1800,
    "stacksSucceeded": 16,
    "stacksFailed": 0,
    "resourcesCreated": 245
  }
}
```

#### 7. Log Message

```json
{
  "type": "log",
  "timestamp": "2025-10-09T16:02:15.123Z",
  "data": {
    "deploymentId": "D1BRV40",
    "operationId": "op-abc123",
    "stackName": "network",
    "level": "info",
    "message": "Creating NAT Gateway..."
  }
}
```

### WebSocket Client Example

```javascript
class MultiStackWebSocketClient {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
    this.ws = null;
    this.subscriptions = new Set();
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${this.apiUrl}/ws`);

      this.ws.onopen = () => {
        // Authenticate
        this.ws.send(JSON.stringify({
          type: 'authenticate',
          token: this.token
        }));
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'authenticated') {
          resolve();
        } else if (message.type === 'error') {
          reject(new Error(message.message));
        } else {
          this.handleMessage(message);
        }
      };

      this.ws.onerror = (error) => {
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket connection closed');
        // Implement reconnection logic
        setTimeout(() => this.connect(), 5000);
      };
    });
  }

  subscribe(channel, callback) {
    this.subscriptions.add({ channel, callback });

    this.ws.send(JSON.stringify({
      type: 'subscribe',
      channel: channel
    }));
  }

  unsubscribe(channel) {
    this.ws.send(JSON.stringify({
      type: 'unsubscribe',
      channel: channel
    }));

    this.subscriptions = new Set(
      Array.from(this.subscriptions).filter(s => s.channel !== channel)
    );
  }

  handleMessage(message) {
    // Route message to subscribers
    for (const subscription of this.subscriptions) {
      if (message.channel === subscription.channel) {
        subscription.callback(message);
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const client = new MultiStackWebSocketClient(
  'wss://api.example.com',
  'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'
);

await client.connect();

client.subscribe('deployments/D1BRV40/operations/op-abc123', (message) => {
  console.log(`[${message.type}]`, message.data);

  if (message.type === 'stack.progress') {
    updateProgressBar(message.data.progress);
  } else if (message.type === 'operation.completed') {
    console.log('Deployment completed!');
  }
});
```

---

## Request/Response Schemas

### Common Response Structure

All API responses follow this structure:

```json
{
  "success": true | false,
  "data": { ... },           // Present on success
  "error": { ... },          // Present on failure
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2025-10-09T12:00:00Z",
    "duration": 125,         // milliseconds
    "rateLimit": {
      "limit": 100,
      "remaining": 95,
      "reset": 1728223200
    }
  }
}
```

### Pagination Schema

```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 145,
    "totalPages": 8,
    "hasNext": true,
    "hasPrev": false,
    "nextPage": 2,
    "prevPage": null
  }
}
```

### Deployment Schema

```json
{
  "deploymentId": "string (D<base36>)",
  "organization": "string",
  "project": "string",
  "domain": "string",
  "template": "string",
  "status": "enum (initialized|deploying|deployed|failed|destroying|destroyed)",
  "directory": "string (path)",
  "createdAt": "string (ISO 8601)",
  "updatedAt": "string (ISO 8601)",
  "createdBy": "string (email)",
  "contact": {
    "email": "string",
    "team": "string"
  },
  "tags": {
    "key": "value"
  },
  "environments": [
    {
      "name": "string",
      "enabled": "boolean",
      "region": "string",
      "account": "string",
      "status": "string"
    }
  ],
  "stacks": [
    {
      "name": "string",
      "layer": "integer",
      "status": "string",
      "dependencies": ["string"]
    }
  ]
}
```

### Stack Schema

```json
{
  "name": "string",
  "displayName": "string",
  "description": "string",
  "category": "enum (network|security|compute|data|analytics|ml|devops)",
  "layer": "integer",
  "dependencies": ["string"],
  "outputs": {
    "outputName": {
      "type": "string|array|object",
      "description": "string"
    }
  },
  "configuration": {
    "configKey": {
      "type": "string",
      "description": "string",
      "default": "any",
      "required": "boolean"
    }
  }
}
```

### Operation Schema

```json
{
  "operationId": "string (op-<random>)",
  "deploymentId": "string",
  "environment": "string",
  "type": "enum (deploy|destroy|validate)",
  "status": "enum (pending|in_progress|success|failed|cancelled)",
  "startedAt": "string (ISO 8601)",
  "completedAt": "string (ISO 8601)|null",
  "startedBy": "string (email)",
  "progress": {
    "totalStacks": "integer",
    "completedStacks": "integer",
    "failedStacks": "integer",
    "inProgressStacks": "integer",
    "pendingStacks": "integer",
    "percentage": "integer (0-100)"
  }
}
```

---

## Error Handling

### Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error context
    },
    "suggestion": "Suggested action to resolve error",
    "documentationUrl": "https://docs.example.com/errors/ERROR_CODE"
  },
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2025-10-09T12:00:00Z"
  }
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| **200 OK** | Success | Successful GET, PUT, PATCH, DELETE |
| **201 Created** | Resource created | Successful POST creating new resource |
| **202 Accepted** | Async operation started | Long-running operations (deploy, destroy) |
| **400 Bad Request** | Invalid request | Malformed JSON, missing required fields |
| **401 Unauthorized** | Authentication failed | Invalid or expired token |
| **403 Forbidden** | Authorization failed | User lacks required permissions |
| **404 Not Found** | Resource not found | Deployment, stack, or template doesn't exist |
| **409 Conflict** | Resource conflict | Deployment ID already exists |
| **422 Unprocessable Entity** | Validation failed | Valid JSON but business logic validation failed |
| **429 Too Many Requests** | Rate limit exceeded | Too many requests in time window |
| **500 Internal Server Error** | Server error | Unexpected server-side error |
| **502 Bad Gateway** | Upstream error | Pulumi Cloud or AWS API error |
| **503 Service Unavailable** | Service down | API maintenance or overload |

### Common Error Codes

#### Authentication Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_INVALID_TOKEN` | 401 | JWT token invalid or malformed |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT token expired |
| `AUTH_INVALID_CREDENTIALS` | 401 | Username or password incorrect |
| `AUTH_MFA_REQUIRED` | 401 | MFA code required but not provided |
| `AUTH_MFA_INVALID` | 401 | MFA code invalid |

#### Authorization Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHZ_FORBIDDEN` | 403 | User lacks permission for action |
| `AUTHZ_RESOURCE_ACCESS_DENIED` | 403 | User cannot access specific resource |
| `AUTHZ_ORGANIZATION_MISMATCH` | 403 | Resource belongs to different organization |

#### Validation Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_REQUIRED_FIELD` | 400 | Required field missing |
| `VALIDATION_INVALID_FORMAT` | 400 | Field format invalid |
| `VALIDATION_CIRCULAR_DEPENDENCY` | 422 | Circular dependency detected |
| `VALIDATION_UNRESOLVABLE_PLACEHOLDER` | 422 | Runtime placeholder cannot be resolved |
| `VALIDATION_INVALID_TEMPLATE` | 422 | Template validation failed |

#### Resource Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Deployment, stack, or template not found |
| `RESOURCE_ALREADY_EXISTS` | 409 | Deployment ID or name already exists |
| `RESOURCE_CONFLICT` | 409 | Resource in conflicting state |
| `RESOURCE_LOCKED` | 423 | Resource locked by another operation |

#### Operation Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `OPERATION_FAILED` | 500 | Deployment or destroy operation failed |
| `OPERATION_TIMEOUT` | 504 | Operation exceeded timeout |
| `OPERATION_CANCELLED` | 499 | Operation cancelled by user |
| `OPERATION_IN_PROGRESS` | 409 | Another operation already running |

#### External Service Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AWS_CREDENTIALS_INVALID` | 502 | AWS credentials invalid |
| `AWS_INSUFFICIENT_PERMISSIONS` | 502 | AWS IAM permissions insufficient |
| `AWS_RESOURCE_ERROR` | 502 | AWS resource creation/deletion failed |
| `PULUMI_STATE_ERROR` | 502 | Pulumi Cloud state error |
| `PULUMI_API_ERROR` | 502 | Pulumi Cloud API error |

### Error Examples

#### Authentication Error

```json
{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "JWT token has expired",
    "details": {
      "expiredAt": "2025-10-09T12:00:00Z",
      "currentTime": "2025-10-09T13:00:00Z"
    },
    "suggestion": "Use refresh token to obtain new access token",
    "documentationUrl": "https://docs.example.com/errors/AUTH_TOKEN_EXPIRED"
  },
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2025-10-09T13:00:00Z"
  }
}
```

#### Validation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_CIRCULAR_DEPENDENCY",
    "message": "Circular dependency detected in stack configuration",
    "details": {
      "cycle": ["compute-ec2", "data-rds", "security", "compute-ec2"],
      "affectedStacks": ["compute-ec2", "data-rds", "security"]
    },
    "suggestion": "Review stack dependencies and remove circular reference",
    "documentationUrl": "https://docs.example.com/errors/VALIDATION_CIRCULAR_DEPENDENCY"
  },
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2025-10-09T13:00:00Z"
  }
}
```

#### Resource Error

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_LOCKED",
    "message": "Deployment is locked by another operation",
    "details": {
      "deploymentId": "D1BRV40",
      "lockedBy": "op-def456",
      "lockedAt": "2025-10-09T12:45:00Z",
      "lockType": "deploy"
    },
    "suggestion": "Wait for current operation to complete or cancel it",
    "documentationUrl": "https://docs.example.com/errors/RESOURCE_LOCKED"
  },
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2025-10-09T13:00:00Z"
  }
}
```

---

## Rate Limiting & Quotas

### Rate Limit Configuration

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|--------------|
| **Free** | 60 | 1,000 | 10,000 |
| **Standard** | 300 | 10,000 | 100,000 |
| **Enterprise** | 1,000 | 50,000 | Unlimited |

### Rate Limit Headers

Every API response includes rate limit headers:

```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1728223200
X-RateLimit-Tier: standard
```

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1728223200
Retry-After: 60
```

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 300,
      "window": "1 minute",
      "resetAt": "2025-10-09T13:01:00Z"
    },
    "suggestion": "Reduce request frequency or upgrade to higher tier"
  }
}
```

### Operation Quotas

| Operation | Free Tier | Standard | Enterprise |
|-----------|-----------|----------|------------|
| **Deployments (active)** | 5 | 50 | Unlimited |
| **Stacks per deployment** | 16 | 50 | Unlimited |
| **Custom templates** | 2 | 20 | Unlimited |
| **API keys** | 2 | 10 | Unlimited |
| **WebSocket connections** | 2 | 10 | 100 |
| **Concurrent operations** | 1 | 5 | 20 |

---

## Integration Examples

### Example 1: Deploy from CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy Cloud Infrastructure

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - stage
          - prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Trigger deployment
        run: |
          RESPONSE=$(curl -X POST \
            https://api.example.com/api/v1/deployments/D1BRV40/deploy \
            -H "X-API-Key: ${{ secrets.CLOUD_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "environment": "${{ github.event.inputs.environment || 'dev' }}",
              "preview": false,
              "parallel": true
            }')

          echo "Deployment started"
          echo $RESPONSE | jq .

          # Extract operation ID
          OPERATION_ID=$(echo $RESPONSE | jq -r '.data.operationId')
          echo "OPERATION_ID=$OPERATION_ID" >> $GITHUB_ENV

      - name: Wait for deployment
        run: |
          while true; do
            STATUS=$(curl -s \
              https://api.example.com/api/v1/deployments/D1BRV40/operations/${{ env.OPERATION_ID }} \
              -H "X-API-Key: ${{ secrets.CLOUD_API_KEY }}" \
              | jq -r '.data.status')

            echo "Deployment status: $STATUS"

            if [ "$STATUS" = "success" ]; then
              echo "Deployment completed successfully!"
              exit 0
            elif [ "$STATUS" = "failed" ]; then
              echo "Deployment failed!"
              exit 1
            fi

            sleep 30
          done
        timeout-minutes: 60
```

### Example 2: Create Deployment via API

```bash
#!/bin/bash
# create-deployment.sh

API_URL="https://api.example.com/api/v1"
API_KEY="msk_live_1234567890abcdef"

# Create deployment
RESPONSE=$(curl -X POST "$API_URL/deployments" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "organization": "CompanyA",
    "project": "ecommerce-platform",
    "domain": "ecommerce.companyA.com",
    "template": "default",
    "region": "us-east-1",
    "accounts": {
      "dev": "111111111111",
      "stage": "222222222222",
      "prod": "333333333333"
    },
    "contact": {
      "email": "platform@companyA.com",
      "team": "Platform Engineering"
    },
    "tags": {
      "Department": "Engineering",
      "CostCenter": "CC-1234",
      "Project": "E-Commerce"
    }
  }')

DEPLOYMENT_ID=$(echo $RESPONSE | jq -r '.data.deploymentId')
echo "Created deployment: $DEPLOYMENT_ID"

# Deploy to dev environment
curl -X POST "$API_URL/deployments/$DEPLOYMENT_ID/deploy" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "dev",
    "parallel": true
  }'

echo "Deployment started. Monitor at: $API_URL/deployments/$DEPLOYMENT_ID"
```

### Example 3: Real-Time Deployment Monitoring

```javascript
// monitor-deployment.js
const axios = require('axios');
const WebSocket = require('ws');

const API_URL = 'https://api.example.com/api/v1';
const WS_URL = 'wss://api.example.com/ws';
const API_KEY = 'msk_live_1234567890abcdef';

async function deployAndMonitor(deploymentId, environment) {
  // Start deployment
  const { data } = await axios.post(
    `${API_URL}/deployments/${deploymentId}/deploy`,
    { environment, parallel: true },
    { headers: { 'X-API-Key': API_KEY } }
  );

  const operationId = data.data.operationId;
  console.log(`Deployment started: ${operationId}`);

  // Connect WebSocket
  const ws = new WebSocket(WS_URL);

  ws.on('open', () => {
    // Authenticate
    ws.send(JSON.stringify({
      type: 'authenticate',
      apiKey: API_KEY
    }));
  });

  ws.on('message', (data) => {
    const message = JSON.parse(data);

    if (message.type === 'authenticated') {
      // Subscribe to operation updates
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: `deployments/${deploymentId}/operations/${operationId}`
      }));
    } else if (message.type === 'stack.progress') {
      const { stackName, progress, currentResource } = message.data;
      console.log(`[${stackName}] ${progress}% - ${currentResource.action} ${currentResource.name}`);
    } else if (message.type === 'stack.completed') {
      const { stackName, duration, resourcesCreated } = message.data;
      console.log(`✓ [${stackName}] Completed in ${duration}s (${resourcesCreated} resources)`);
    } else if (message.type === 'stack.failed') {
      const { stackName, error } = message.data;
      console.error(`✗ [${stackName}] Failed: ${error.message}`);
    } else if (message.type === 'operation.completed') {
      const { status, stacksSucceeded, stacksFailed, duration } = message.data;
      console.log(`\nDeployment ${status} in ${duration}s`);
      console.log(`  Succeeded: ${stacksSucceeded}, Failed: ${stacksFailed}`);
      ws.close();
    }
  });
}

// Usage
deployAndMonitor('D1BRV40', 'dev');
```

### Example 4: Validate Before Deploy

```python
# validate_and_deploy.py
import requests
import sys

API_URL = "https://api.example.com/api/v1"
API_KEY = "msk_live_1234567890abcdef"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def validate_deployment(deployment_id, environment):
    """Validate deployment configuration"""
    response = requests.post(
        f"{API_URL}/deployments/{deployment_id}/validate",
        json={
            "environment": environment,
            "checks": [
                "manifest",
                "dependencies",
                "aws-credentials",
                "pulumi-state",
                "runtime-placeholders"
            ]
        },
        headers=headers
    )

    data = response.json()

    if not data['data']['valid']:
        print("❌ Validation failed:")
        for error in data['data']['errors']:
            print(f"  - {error['message']}")
        return False

    if data['data']['warnings']:
        print("⚠️  Warnings:")
        for warning in data['data']['warnings']:
            print(f"  - {warning['message']}")

    print("✅ Validation passed")
    return True

def deploy(deployment_id, environment):
    """Deploy infrastructure"""
    response = requests.post(
        f"{API_URL}/deployments/{deployment_id}/deploy",
        json={
            "environment": environment,
            "preview": False,
            "parallel": True
        },
        headers=headers
    )

    data = response.json()
    operation_id = data['data']['operationId']

    print(f"🚀 Deployment started: {operation_id}")
    return operation_id

def main():
    deployment_id = "D1BRV40"
    environment = "dev"

    # Validate first
    if not validate_deployment(deployment_id, environment):
        sys.exit(1)

    # Deploy
    operation_id = deploy(deployment_id, environment)
    print(f"Monitor at: {API_URL}/deployments/{deployment_id}/operations/{operation_id}")

if __name__ == "__main__":
    main()
```

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

```
https://api.example.com/api/v1/openapi.json
https://api.example.com/api/v1/openapi.yaml
```

### Swagger UI Documentation

Interactive API documentation is available at:

```
https://api.example.com/docs
```

### OpenAPI Specification Structure

```yaml
openapi: 3.0.3
info:
  title: Cloud Architecture API
  version: 3.0.0
  description: Complete REST API for Cloud Architecture v3.0
  contact:
    name: Platform Team
    email: platform@example.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html

servers:
  - url: https://api.example.com/api/v1
    description: Production
  - url: https://stage-api.example.com/api/v1
    description: Stage
  - url: http://localhost:3000/api/v1
    description: Local Development

tags:
  - name: Authentication
    description: User authentication and API key management
  - name: Deployments
    description: Deployment lifecycle management
  - name: Stacks
    description: Stack management and operations
  - name: Environments
    description: Environment configuration
  - name: Templates
    description: Template management
  - name: State
    description: State management operations
  - name: Monitoring
    description: Logs, metrics, and health checks

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    # ... (all schemas defined here)

paths:
  /auth/login:
    post:
      # ... endpoint definition
  # ... (all endpoints)
```

### Generating Client SDKs

Use OpenAPI Generator to create client SDKs:

```bash
# JavaScript/TypeScript
openapi-generator-cli generate \
  -i https://api.example.com/api/v1/openapi.json \
  -g typescript-axios \
  -o ./sdk/typescript

# Python
openapi-generator-cli generate \
  -i https://api.example.com/api/v1/openapi.json \
  -g python \
  -o ./sdk/python

# Go
openapi-generator-cli generate \
  -i https://api.example.com/api/v1/openapi.json \
  -g go \
  -o ./sdk/go

# Java
openapi-generator-cli generate \
  -i https://api.example.com/api/v1/openapi.json \
  -g java \
  -o ./sdk/java
```

---

## Deployment Guide

### AWS Infrastructure Requirements

#### Required AWS Services

- **API Gateway**: REST API + WebSocket API
- **Lambda**: API handler functions
- **Cognito**: User authentication
- **DynamoDB**: Metadata storage
- **S3**: State storage
- **CloudWatch**: Logging and monitoring
- **SQS**: Async operation queue
- **EventBridge**: Event routing
- **IAM**: Roles and policies
- **ACM**: SSL/TLS certificates
- **Route53**: DNS management (optional)

#### IAM Permissions

The API service requires IAM role with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cloud-state-*",
        "arn:aws:s3:::cloud-state-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/cloud-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": [
        "arn:aws:sqs:*:*:cloud-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### Infrastructure Deployment

#### Using Pulumi (Recommended)

```bash
# Deploy API service stack
cd ./cloud/stacks/api-service
pulumi up
```

#### Manual CloudFormation

```bash
# Deploy CloudFormation template
aws cloudformation create-stack \
  --stack-name cloud-api \
  --template-body file://cloudformation/api-service.yaml \
  --parameters \
    ParameterKey=DomainName,ParameterValue=api.example.com \
    ParameterKey=CertificateArn,ParameterValue=arn:aws:acm:... \
  --capabilities CAPABILITY_IAM
```

### Configuration Management

#### Environment-Specific Configuration

```yaml
# config/production.yaml
api:
  domain: api.example.com
  version: v1
  corsOrigins:
    - https://console.example.com
    - https://app.example.com
  rateLimit:
    requests: 300
    window: 60000

auth:
  cognito:
    userPoolId: us-east-1_ABC123
    clientId: abcdef123456
  jwt:
    expiresIn: 3600
    refreshExpiresIn: 604800

aws:
  region: us-east-1
  accountId: "123456789012"

pulumi:
  accessToken: ${PULUMI_ACCESS_TOKEN}
  organization: my-organization

database:
  deploymentsTable: cloud-deployments-prod
  auditTable: cloud-audit-logs-prod

storage:
  stateBucket: cloud-state-prod
  configBucket: cloud-config-prod

logging:
  level: info
  format: json
  retentionDays: 30
```

### Monitoring Setup

#### CloudWatch Alarms

```bash
# API Error Rate Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name cloud-api-error-rate \
  --alarm-description "Alert when API error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/ApiGateway \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Lambda Duration Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name cloud-api-lambda-duration \
  --alarm-description "Alert when Lambda execution time exceeds 10s" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10000 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

#### CloudWatch Dashboard

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "API Request Count",
        "metrics": [
          ["AWS/ApiGateway", "Count", {"stat": "Sum"}]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "API Latency",
        "metrics": [
          ["AWS/ApiGateway", "Latency", {"stat": "Average"}],
          ["...", {"stat": "p99"}]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    }
  ]
}
```

---

## Monitoring & Observability

### Metrics

#### API Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `api.requests.total` | Total API requests | Count |
| `api.requests.success` | Successful requests (2xx) | Count |
| `api.requests.errors` | Failed requests (4xx, 5xx) | Count |
| `api.latency.avg` | Average response time | Milliseconds |
| `api.latency.p95` | 95th percentile latency | Milliseconds |
| `api.latency.p99` | 99th percentile latency | Milliseconds |

#### Operation Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `operations.deploy.count` | Total deploy operations | Count |
| `operations.deploy.success` | Successful deploys | Count |
| `operations.deploy.failed` | Failed deploys | Count |
| `operations.deploy.duration` | Average deploy duration | Seconds |
| `operations.destroy.count` | Total destroy operations | Count |
| `operations.destroy.duration` | Average destroy duration | Seconds |

#### Resource Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `resources.created` | Resources created | Count |
| `resources.updated` | Resources updated | Count |
| `resources.deleted` | Resources deleted | Count |
| `resources.failed` | Resource operations failed | Count |

### Logging

#### Log Structure

```json
{
  "timestamp": "2025-10-09T12:00:00.123Z",
  "level": "info",
  "requestId": "req-abc123",
  "userId": "user-123",
  "method": "POST",
  "path": "/api/v1/deployments/D1BRV40/deploy",
  "statusCode": 202,
  "duration": 125,
  "message": "Deployment operation started",
  "context": {
    "deploymentId": "D1BRV40",
    "environment": "dev",
    "operationId": "op-abc123"
  }
}
```

#### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARN**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for failures
- **FATAL**: Critical failures requiring immediate attention

### Tracing

Distributed tracing with AWS X-Ray:

```javascript
const AWSXRay = require('aws-xray-sdk-core');
const AWS = AWSXRay.captureAWS(require('aws-sdk'));

// Trace API requests
app.use(AWSXRay.express.openSegment('cloud-api'));

app.post('/deployments/:id/deploy', async (req, res) => {
  const segment = AWSXRay.getSegment();
  const subsegment = segment.addNewSubsegment('deploy-operation');

  try {
    // Operation logic
    subsegment.addAnnotation('deploymentId', req.params.id);
    subsegment.addMetadata('environment', req.body.environment);

    // ... deploy logic

    subsegment.close();
  } catch (error) {
    subsegment.addError(error);
    subsegment.close();
  }
});

app.use(AWSXRay.express.closeSegment());
```

---

## Security Considerations

### Best Practices

1. **Authentication**: Always use JWT tokens or API keys, never bypass authentication
2. **HTTPS Only**: All API communication must use HTTPS
3. **Token Expiration**: Access tokens expire in 1 hour, refresh tokens in 7 days
4. **API Key Rotation**: Rotate API keys every 90 days
5. **Least Privilege**: Grant minimum required permissions
6. **Input Validation**: Validate all input data before processing
7. **Rate Limiting**: Enforce rate limits to prevent abuse
8. **Audit Logging**: Log all operations for compliance
9. **Encryption**: Encrypt sensitive data at rest and in transit
10. **MFA**: Enable multi-factor authentication for production access

### Security Headers

All API responses include security headers:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

### Data Encryption

- **At Rest**: All data encrypted with AES-256
- **In Transit**: TLS 1.3 for all API communication
- **Secrets**: Stored in AWS Secrets Manager
- **State Files**: Encrypted in S3 with KMS

---

## Versioning Strategy

### API Versioning

- **Current Version**: v1
- **Versioning Scheme**: URL path versioning (`/api/v1/`)
- **Deprecation Policy**: 12 months notice before removal
- **Version Support**: Support current and previous version

### Version Migration

When new version released:

1. Announce deprecation 12 months in advance
2. Provide migration guide
3. Support both versions during transition
4. Gradual sunset of old version

---

## Troubleshooting

### Common Issues

#### Issue: 401 Unauthorized

**Cause**: Invalid or expired JWT token

**Solution**:
```bash
# Refresh token
curl -X POST https://api.example.com/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{ "refreshToken": "..." }'
```

#### Issue: 429 Too Many Requests

**Cause**: Rate limit exceeded

**Solution**: Wait for rate limit reset or upgrade tier

#### Issue: 500 Internal Server Error

**Cause**: Server-side error

**Solution**: Check CloudWatch logs for error details:
```bash
aws logs tail /aws/lambda/cloud-api --follow
```

#### Issue: WebSocket Connection Failed

**Cause**: Invalid authentication or network issue

**Solution**: Verify token and network connectivity

---

## Appendix

### Response Time SLA

| Endpoint Type | Target | Maximum |
|--------------|---------|---------|
| **Authentication** | < 200ms | 500ms |
| **GET Requests** | < 300ms | 1000ms |
| **POST/PUT/PATCH** | < 500ms | 2000ms |
| **Deploy Operations** | N/A (Async) | N/A |

### Support

- **Documentation**: https://docs.example.com
- **Support Email**: support@example.com
- **Status Page**: https://status.example.com
- **Community Forum**: https://community.example.com

---

**Document Version**: 3.0.0
**Last Updated**: 2025-10-09
**Next Review**: 2025-11-06
