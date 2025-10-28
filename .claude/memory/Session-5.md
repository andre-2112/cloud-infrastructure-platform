# Session 5: Database Integration

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 5
**Focus:** DynamoDB + GraphQL API (AWS AppSync) + Cognito Auth
**Date:** 2025-10-23

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Session Context](#session-context)
3. [Database Architecture](#database-architecture)
4. [DynamoDB Schema Design](#dynamodb-schema-design)
5. [GraphQL API with AWS AppSync](#graphql-api-with-aws-appapp)
6. [Cognito Authentication Integration](#cognito-authentication-integration)
7. [Data Access Patterns](#data-access-patterns)
8. [Code Implementation](#code-implementation)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Plan](#implementation-plan)
11. [Success Criteria](#success-criteria)

---

## Executive Summary

### Purpose of Session 5

Session 5 implements **persistent storage** for the Cloud Infrastructure Orchestration Platform using **DynamoDB** as the primary database, with a **GraphQL API** powered by **AWS AppSync** for flexible data queries, secured with **AWS Cognito** authentication.

### Key Objectives

1. **DynamoDB Tables** - Design and implement tables for deployments, stacks, logs
2. **GraphQL API** - Build AppSync GraphQL API for flexible queries
3. **Cognito Integration** - Secure GraphQL API with Cognito user pools
4. **Data Access Layer** - Python client library for database operations
5. **State Management** - Persistent storage for deployment state and history
6. **Real-time Updates** - AppSync subscriptions for real-time monitoring

### Why DynamoDB + AppSync + GraphQL?

**DynamoDB:**
- Fully managed NoSQL database
- Automatic scaling
- Single-digit millisecond latency
- Pay-per-request pricing
- Perfect for deployment metadata and state

**AppSync:**
- Managed GraphQL service
- Automatic Cognito integration
- Real-time subscriptions (WebSocket)
- Automatic schema generation
- Offline support

**GraphQL:**
- Flexible queries (fetch exactly what you need)
- Strong typing
- Single endpoint
- Real-time subscriptions
- Auto-generated documentation

### What Gets Built

```
cloud/tools/database/
├── src/
│   └── cloud_db/
│       ├── __init__.py
│       ├── client.py                  # DynamoDB client wrapper
│       ├── models/                    # Data models
│       │   ├── __init__.py
│       │   ├── deployment.py          # Deployment model
│       │   ├── stack.py               # Stack model
│       │   ├── log_entry.py           # Log entry model
│       │   └── metric.py              # Metric model
│       ├── repositories/              # Data access layer
│       │   ├── __init__.py
│       │   ├── deployment_repository.py
│       │   ├── stack_repository.py
│       │   ├── log_repository.py
│       │   └── metric_repository.py
│       └── utils/                     # Utilities
│           ├── __init__.py
│           ├── serializer.py          # DynamoDB serialization
│           └── query_builder.py       # Query helpers
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models/
│   ├── test_repositories/
│   └── test_integration/
├── graphql/                           # GraphQL schema
│   ├── schema.graphql                 # Main schema
│   ├── resolvers/                     # AppSync resolvers
│   │   ├── deployment.vtl             # Deployment resolvers
│   │   ├── stack.vtl                  # Stack resolvers
│   │   ├── log.vtl                    # Log resolvers
│   │   └── metric.vtl                 # Metric resolvers
│   └── pipeline/                      # Pipeline resolvers
├── infrastructure/                    # IaC for database
│   ├── dynamodb.ts                    # DynamoDB tables (Pulumi)
│   ├── appsync.ts                     # AppSync API (Pulumi)
│   └── cognito.ts                     # Cognito integration
├── requirements.txt
├── pyproject.toml
└── README.md

INTEGRATION WITH CLI/API:
cloud/tools/cli/ and cloud/tools/api/ will use cloud/tools/database/ for:
- Storing deployment state
- Querying deployment history
- Logging operations
- Storing metrics
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                      │
│  (CLI, REST API, Web Dashboard, Mobile Apps)                │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ GraphQL queries/mutations/subscriptions
                           │ Authorization: Cognito JWT token
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     AWS AppSync                             │
│  - GraphQL endpoint                                         │
│  - Cognito authentication                                   │
│  - Real-time subscriptions                                  │
│  - Request/response mapping                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ VTL resolvers
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      DynamoDB Tables                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Deployments Table                                  │   │
│  │  PK: DEPLOYMENT#{id}                                │   │
│  │  SK: METADATA                                       │   │
│  │  GSI1: organization + created_at                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Stacks Table                                       │   │
│  │  PK: DEPLOYMENT#{id}                                │   │
│  │  SK: STACK#{name}#{env}                             │   │
│  │  GSI1: stack_name + updated_at                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Logs Table                                         │   │
│  │  PK: DEPLOYMENT#{id}                                │   │
│  │  SK: TIMESTAMP#{iso}#{uuid}                         │   │
│  │  GSI1: log_level + timestamp                        │   │
│  │  TTL: 90 days                                       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Metrics Table                                      │   │
│  │  PK: METRIC#{name}                                  │   │
│  │  SK: TIMESTAMP#{iso}                                │   │
│  │  TTL: 365 days                                      │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Python client library
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              CLI/API Business Logic                         │
│  (orchestrator, template manager, deployment manager)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Session Context

### What Was Built Before

**Session 1:** Complete documentation (16 documents)
**Session 2.1:** CLI framework (directory structure, basic commands)
**Session 3:** Complete CLI implementation (orchestrator, business logic, 25+ commands)
**Session 4:** REST API with FastAPI (24 endpoints, Cognito auth)

### What Session 5 Adds

1. **DynamoDB Tables** - Persistent storage for deployments, stacks, logs, metrics
2. **GraphQL Schema** - Type-safe API for data access
3. **AWS AppSync API** - Managed GraphQL service with Cognito auth
4. **Python Client Library** - Easy-to-use database access layer
5. **Data Access Patterns** - Optimized queries for common use cases
6. **Real-time Subscriptions** - Live updates for monitoring

### Dependencies

- **AWS DynamoDB** - NoSQL database
- **AWS AppSync** - GraphQL API service
- **AWS Cognito** - Authentication (from Session 4)
- **boto3** - AWS SDK for Python
- **pydantic** - Data validation
- **python-graphql-client** - GraphQL client library

---

## Database Architecture

### Design Principles

1. **Single Table Design** - Use DynamoDB best practices with composite keys
2. **Access Pattern Driven** - Design based on query patterns, not entities
3. **Denormalization** - Duplicate data for fast queries
4. **GSIs for Queries** - Use Global Secondary Indexes for alternate access patterns
5. **TTL for Logs** - Automatic expiration of old logs
6. **Optimistic Locking** - Version fields for concurrent updates

### Why Single Table Design?

DynamoDB performs best with a single table that uses:
- **Composite Primary Key** (PK + SK) for item organization
- **Global Secondary Indexes** (GSI) for alternate queries
- **Item collections** for related data

Benefits:
- Fewer tables to manage
- Atomic transactions within item collections
- Lower costs (fewer tables = fewer reads/writes)
- Better performance (minimize cross-table queries)

### Table Structure

We'll use **4 tables** (compromise between single-table and multi-table):

1. **Deployments** - Deployment metadata and configuration
2. **Stacks** - Individual stack states and outputs
3. **Logs** - Operation logs with TTL
4. **Metrics** - System metrics with TTL

This provides:
- Clear separation of concerns
- Independent scaling
- Easier TTL management
- Simpler queries

---

## DynamoDB Schema Design

### Table 1: Deployments

**Purpose:** Store deployment metadata, configuration, and state

**Schema:**
```
PK: DEPLOYMENT#{deployment_id}
SK: METADATA
```

**Attributes:**
```
- deployment_id (String) - Unique ID (D1BRV40)
- organization (String) - Organization name
- project (String) - Project name
- domain (String) - Base domain
- template (String) - Template used
- status (String) - initialized/deploying/deployed/failed
- environments (Map) - Environment configurations
- stacks (Map) - Stack configurations
- manifest (String) - Full manifest JSON
- created_at (String) - ISO 8601 timestamp
- updated_at (String) - ISO 8601 timestamp
- created_by (String) - User ID (Cognito sub)
- version (Number) - Version for optimistic locking
```

**GSI1 (OrganizationIndex):**
```
PK: organization
SK: created_at
```
Use case: List deployments by organization, sorted by creation date

**GSI2 (StatusIndex):**
```
PK: status
SK: updated_at
```
Use case: Query deployments by status (e.g., all active deployments)

**Example Item:**
```json
{
  "PK": "DEPLOYMENT#D1BRV40",
  "SK": "METADATA",
  "deployment_id": "D1BRV40",
  "organization": "MyOrg",
  "project": "my-project",
  "domain": "myproject.example.com",
  "template": "default",
  "status": "deployed",
  "environments": {
    "dev": {
      "enabled": true,
      "region": "us-east-1",
      "account_id": "111111111111"
    }
  },
  "stacks": {
    "network": {
      "enabled": true,
      "dependencies": []
    },
    "security": {
      "enabled": true,
      "dependencies": ["network"]
    }
  },
  "manifest": "{...full manifest JSON...}",
  "created_at": "2025-10-23T10:00:00Z",
  "updated_at": "2025-10-23T10:15:00Z",
  "created_by": "123e4567-e89b-12d3-a456-426614174000",
  "version": 3
}
```

---

### Table 2: Stacks

**Purpose:** Store individual stack states, outputs, and resources

**Schema:**
```
PK: DEPLOYMENT#{deployment_id}
SK: STACK#{stack_name}#{environment}
```

**Attributes:**
```
- deployment_id (String) - Deployment ID
- stack_name (String) - Stack name (network, security, etc.)
- environment (String) - Environment (dev/stage/prod)
- status (String) - pending/deploying/deployed/failed/destroying
- pulumi_stack_name (String) - Full Pulumi stack name
- layer (Number) - Execution layer
- dependencies (List<String>) - Stack dependencies
- outputs (Map) - Stack outputs from Pulumi
- resources (List<Map>) - List of resources in stack
- resource_count (Number) - Total resources
- last_deployment (Map) - Last deployment info
  - started_at (String)
  - completed_at (String)
  - duration_seconds (Number)
  - result (String) - success/failed
  - error_message (String, optional)
- created_at (String) - ISO 8601 timestamp
- updated_at (String) - ISO 8601 timestamp
- version (Number) - Version for optimistic locking
```

**GSI1 (StackNameIndex):**
```
PK: stack_name
SK: updated_at
```
Use case: Query all instances of a stack across deployments

**GSI2 (StatusIndex):**
```
PK: status
SK: updated_at
```
Use case: Find all stacks in a particular state

**Example Item:**
```json
{
  "PK": "DEPLOYMENT#D1BRV40",
  "SK": "STACK#network#dev",
  "deployment_id": "D1BRV40",
  "stack_name": "network",
  "environment": "dev",
  "status": "deployed",
  "pulumi_stack_name": "MyOrg/my-project/D1BRV40-network-dev",
  "layer": 1,
  "dependencies": [],
  "outputs": {
    "vpc_id": "vpc-12345",
    "public_subnet_ids": ["subnet-11111", "subnet-22222"],
    "private_subnet_ids": ["subnet-33333", "subnet-44444"]
  },
  "resources": [
    {
      "type": "aws:ec2/vpc:Vpc",
      "name": "main-vpc",
      "urn": "urn:pulumi:...",
      "status": "up-to-date"
    }
  ],
  "resource_count": 15,
  "last_deployment": {
    "started_at": "2025-10-23T10:05:00Z",
    "completed_at": "2025-10-23T10:10:00Z",
    "duration_seconds": 300,
    "result": "success"
  },
  "created_at": "2025-10-23T10:05:00Z",
  "updated_at": "2025-10-23T10:10:00Z",
  "version": 2
}
```

---

### Table 3: Logs

**Purpose:** Store operation logs with automatic expiration

**Schema:**
```
PK: DEPLOYMENT#{deployment_id}
SK: TIMESTAMP#{iso_timestamp}#{uuid}
```

**Attributes:**
```
- log_id (String) - UUID
- deployment_id (String) - Deployment ID
- stack_name (String, optional) - Related stack
- environment (String, optional) - Related environment
- timestamp (String) - ISO 8601 timestamp
- level (String) - debug/info/warn/error
- message (String) - Log message
- details (Map, optional) - Additional context
- user_id (String, optional) - User who triggered action
- ttl (Number) - Unix timestamp for TTL (90 days from creation)
```

**GSI1 (LogLevelIndex):**
```
PK: level
SK: timestamp
```
Use case: Query logs by level (e.g., all errors)

**TTL Attribute:** `ttl`
- Automatically delete logs after 90 days
- Reduces storage costs
- Complies with data retention policies

**Example Item:**
```json
{
  "PK": "DEPLOYMENT#D1BRV40",
  "SK": "TIMESTAMP#2025-10-23T10:05:30.123Z#a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "log_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "deployment_id": "D1BRV40",
  "stack_name": "network",
  "environment": "dev",
  "timestamp": "2025-10-23T10:05:30.123Z",
  "level": "info",
  "message": "Starting deployment of network-dev",
  "details": {
    "layer": 1,
    "total_resources": 15
  },
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "ttl": 1737364800
}
```

---

### Table 4: Metrics

**Purpose:** Store system metrics with automatic expiration

**Schema:**
```
PK: METRIC#{metric_name}
SK: TIMESTAMP#{iso_timestamp}
```

**Attributes:**
```
- metric_name (String) - Metric identifier
- timestamp (String) - ISO 8601 timestamp
- value (Number) - Metric value
- unit (String) - Metric unit (count, seconds, bytes, etc.)
- dimensions (Map) - Additional dimensions
  - deployment_id (String, optional)
  - stack_name (String, optional)
  - environment (String, optional)
- ttl (Number) - Unix timestamp for TTL (365 days from creation)
```

**Example Metrics:**
- `deployments_started`
- `deployments_completed`
- `deployments_failed`
- `stack_deployment_duration`
- `api_requests`
- `api_errors`

**Example Item:**
```json
{
  "PK": "METRIC#stack_deployment_duration",
  "SK": "TIMESTAMP#2025-10-23T10:10:00Z",
  "metric_name": "stack_deployment_duration",
  "timestamp": "2025-10-23T10:10:00Z",
  "value": 300,
  "unit": "seconds",
  "dimensions": {
    "deployment_id": "D1BRV40",
    "stack_name": "network",
    "environment": "dev"
  },
  "ttl": 1761350400
}
```

---

## GraphQL API with AWS AppSync

### GraphQL Schema

**File:** `graphql/schema.graphql`

```graphql
# Cloud Infrastructure Orchestration Platform
# GraphQL Schema - Architecture 3.1

# ============================================================================
# Types
# ============================================================================

type Deployment {
  deployment_id: ID!
  organization: String!
  project: String!
  domain: String!
  template: String!
  status: DeploymentStatus!
  environments: AWSJSON!
  stacks: AWSJSON!
  manifest: AWSJSON!
  created_at: AWSDateTime!
  updated_at: AWSDateTime!
  created_by: String!
  version: Int!
}

type Stack {
  deployment_id: ID!
  stack_name: String!
  environment: String!
  status: StackStatus!
  pulumi_stack_name: String!
  layer: Int!
  dependencies: [String!]!
  outputs: AWSJSON
  resources: [Resource!]
  resource_count: Int!
  last_deployment: LastDeployment
  created_at: AWSDateTime!
  updated_at: AWSDateTime!
  version: Int!
}

type Resource {
  type: String!
  name: String!
  urn: String!
  status: String!
}

type LastDeployment {
  started_at: AWSDateTime!
  completed_at: AWSDateTime
  duration_seconds: Int
  result: String!
  error_message: String
}

type LogEntry {
  log_id: ID!
  deployment_id: ID!
  stack_name: String
  environment: String
  timestamp: AWSDateTime!
  level: LogLevel!
  message: String!
  details: AWSJSON
  user_id: String
}

type Metric {
  metric_name: String!
  timestamp: AWSDateTime!
  value: Float!
  unit: String!
  dimensions: AWSJSON
}

# ============================================================================
# Enums
# ============================================================================

enum DeploymentStatus {
  INITIALIZED
  DEPLOYING
  DEPLOYED
  FAILED
  DESTROYING
}

enum StackStatus {
  PENDING
  DEPLOYING
  DEPLOYED
  FAILED
  DESTROYING
  DESTROYED
}

enum LogLevel {
  DEBUG
  INFO
  WARN
  ERROR
}

# ============================================================================
# Input Types
# ============================================================================

input CreateDeploymentInput {
  organization: String!
  project: String!
  domain: String!
  template: String!
  environments: AWSJSON!
  stacks: AWSJSON!
  manifest: AWSJSON!
  created_by: String!
}

input UpdateDeploymentInput {
  deployment_id: ID!
  status: DeploymentStatus
  environments: AWSJSON
  stacks: AWSJSON
  manifest: AWSJSON
  version: Int!
}

input CreateStackInput {
  deployment_id: ID!
  stack_name: String!
  environment: String!
  pulumi_stack_name: String!
  layer: Int!
  dependencies: [String!]!
}

input UpdateStackInput {
  deployment_id: ID!
  stack_name: String!
  environment: String!
  status: StackStatus
  outputs: AWSJSON
  resources: AWSJSON
  resource_count: Int
  last_deployment: AWSJSON
  version: Int!
}

input CreateLogInput {
  deployment_id: ID!
  stack_name: String
  environment: String
  level: LogLevel!
  message: String!
  details: AWSJSON
  user_id: String
}

input CreateMetricInput {
  metric_name: String!
  value: Float!
  unit: String!
  dimensions: AWSJSON
}

# ============================================================================
# Queries
# ============================================================================

type Query {
  # Get single deployment
  getDeployment(deployment_id: ID!): Deployment

  # List deployments with filters
  listDeployments(
    organization: String
    status: DeploymentStatus
    limit: Int
    nextToken: String
  ): DeploymentConnection!

  # Get single stack
  getStack(
    deployment_id: ID!
    stack_name: String!
    environment: String!
  ): Stack

  # List stacks for a deployment
  listStacks(
    deployment_id: ID!
    environment: String
    limit: Int
    nextToken: String
  ): StackConnection!

  # List stacks by name across deployments
  listStacksByName(
    stack_name: String!
    limit: Int
    nextToken: String
  ): StackConnection!

  # List logs for a deployment
  listLogs(
    deployment_id: ID!
    level: LogLevel
    stack_name: String
    start_time: AWSDateTime
    end_time: AWSDateTime
    limit: Int
    nextToken: String
  ): LogConnection!

  # Get metrics
  getMetrics(
    metric_name: String!
    start_time: AWSDateTime!
    end_time: AWSDateTime!
    dimensions: AWSJSON
  ): [Metric!]!
}

# ============================================================================
# Mutations
# ============================================================================

type Mutation {
  # Create deployment
  createDeployment(input: CreateDeploymentInput!): Deployment!

  # Update deployment
  updateDeployment(input: UpdateDeploymentInput!): Deployment!

  # Delete deployment
  deleteDeployment(deployment_id: ID!): Boolean!

  # Create stack
  createStack(input: CreateStackInput!): Stack!

  # Update stack
  updateStack(input: UpdateStackInput!): Stack!

  # Delete stack
  deleteStack(
    deployment_id: ID!
    stack_name: String!
    environment: String!
  ): Boolean!

  # Create log entry
  createLog(input: CreateLogInput!): LogEntry!

  # Create metric
  createMetric(input: CreateMetricInput!): Metric!
}

# ============================================================================
# Subscriptions
# ============================================================================

type Subscription {
  # Subscribe to deployment updates
  onDeploymentUpdated(deployment_id: ID!): Deployment
    @aws_subscribe(mutations: ["updateDeployment"])

  # Subscribe to stack updates
  onStackUpdated(
    deployment_id: ID!
    stack_name: String
  ): Stack
    @aws_subscribe(mutations: ["updateStack"])

  # Subscribe to new logs
  onLogCreated(deployment_id: ID!): LogEntry
    @aws_subscribe(mutations: ["createLog"])
}

# ============================================================================
# Connection Types (for pagination)
# ============================================================================

type DeploymentConnection {
  items: [Deployment!]!
  nextToken: String
}

type StackConnection {
  items: [Stack!]!
  nextToken: String
}

type LogConnection {
  items: [LogEntry!]!
  nextToken: String
}

# ============================================================================
# Directives
# ============================================================================

# All operations require Cognito authentication
directive @aws_cognito_user_pools on OBJECT | FIELD_DEFINITION
```

---

### AppSync Resolvers (VTL Templates)

**File:** `graphql/resolvers/deployment.vtl`

```vtl
## Get Deployment Resolver

#if($context.arguments.deployment_id)
  {
    "version": "2018-05-29",
    "operation": "GetItem",
    "key": {
      "PK": $util.dynamodb.toDynamoDBJson("DEPLOYMENT#${context.arguments.deployment_id}"),
      "SK": $util.dynamodb.toDynamoDBJson("METADATA")
    }
  }
#end

## Response template
#if($context.result)
  $util.toJson($context.result)
#else
  null
#end
```

```vtl
## List Deployments Resolver

#set($limit = $context.arguments.limit)
#if(!$limit)
  #set($limit = 50)
#end

{
  "version": "2018-05-29",
  "operation": "Query",
  "index": "OrganizationIndex",
  "query": {
    "expression": "organization = :organization",
    "expressionValues": {
      ":organization": $util.dynamodb.toDynamoDBJson($context.arguments.organization)
    }
  },
  "limit": $limit,
  "scanIndexForward": false
}

#if($context.arguments.nextToken)
  ,"nextToken": "$context.arguments.nextToken"
#end

## Response template
{
  "items": $util.toJson($context.result.items),
  "nextToken": #if($context.result.nextToken) "$context.result.nextToken" #else null #end
}
```

---

### AppSync Configuration

**Authentication:**
- **Primary:** AWS Cognito User Pools (from Session 4)
- **Secondary:** IAM (for internal services)

**Authorization:**
- All GraphQL operations require authentication
- User groups control access:
  - `Administrators` - Full access (read/write/delete)
  - `Developers` - Read/write deployments and stacks
  - `ReadOnly` - Read-only access

**Real-time Subscriptions:**
- Clients subscribe to deployment/stack updates
- AppSync pushes updates via WebSocket
- Automatic reconnection on connection loss

---

## Cognito Authentication Integration

### AppSync Cognito Setup

```typescript
// infrastructure/appsync.ts (Pulumi)

import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

// Reference Cognito User Pool from Session 4
const userPool = new aws.cognito.UserPool("cloud-platform-users", {
  name: "cloud-platform-users",
  // ... configuration from Session 4
});

// Create AppSync GraphQL API
const api = new aws.appsync.GraphQLApi("cloud-platform-api", {
  name: "cloud-platform-graphql-api",
  authenticationType: "AMAZON_COGNITO_USER_POOLS",
  userPoolConfig: {
    userPoolId: userPool.id,
    awsRegion: aws.config.region,
    defaultAction: "ALLOW",
  },
  schema: fs.readFileSync("../graphql/schema.graphql", "utf8"),
  logConfig: {
    cloudwatchLogsRoleArn: logRole.arn,
    fieldLogLevel: "ALL",
  },
});

// Additional authentication: IAM for internal services
const iamAuth = new aws.appsync.ApiKey("cloud-api-iam", {
  apiId: api.id,
  // ... configuration
});
```

### Client Authentication Flow

```python
# Example: Python client with Cognito authentication

import boto3
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# 1. Authenticate with Cognito
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

auth_response = cognito_client.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'user@example.com',
        'PASSWORD': 'SecurePass123!'
    },
    ClientId='<APP_CLIENT_ID>'
)

id_token = auth_response['AuthenticationResult']['IdToken']

# 2. Create GraphQL client with token
transport = RequestsHTTPTransport(
    url='https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql',
    headers={'Authorization': id_token},
    use_json=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# 3. Execute GraphQL query
query = gql('''
    query GetDeployment($id: ID!) {
        getDeployment(deployment_id: $id) {
            deployment_id
            organization
            project
            status
            created_at
        }
    }
''')

result = client.execute(query, variable_values={'id': 'D1BRV40'})
print(result)
```

---

## Data Access Patterns

### Pattern 1: Get Deployment by ID

**Use Case:** Load deployment details
**Query:**
```python
deployment = deployment_repo.get_by_id("D1BRV40")
```
**DynamoDB:**
```
GetItem:
  Table: Deployments
  Key:
    PK: DEPLOYMENT#D1BRV40
    SK: METADATA
```

---

### Pattern 2: List Deployments by Organization

**Use Case:** Show all deployments for an organization
**Query:**
```python
deployments = deployment_repo.list_by_organization("MyOrg", limit=50)
```
**DynamoDB:**
```
Query:
  Table: Deployments
  IndexName: OrganizationIndex
  KeyConditionExpression: organization = :org
  ScanIndexForward: false (newest first)
  Limit: 50
```

---

### Pattern 3: Get Stack Status

**Use Case:** Check if a stack is deployed
**Query:**
```python
stack = stack_repo.get_stack("D1BRV40", "network", "dev")
```
**DynamoDB:**
```
GetItem:
  Table: Stacks
  Key:
    PK: DEPLOYMENT#D1BRV40
    SK: STACK#network#dev
```

---

### Pattern 4: List All Stacks for Deployment

**Use Case:** Show all stacks in a deployment
**Query:**
```python
stacks = stack_repo.list_by_deployment("D1BRV40")
```
**DynamoDB:**
```
Query:
  Table: Stacks
  KeyConditionExpression: PK = :pk AND begins_with(SK, :sk_prefix)
  ExpressionAttributeValues:
    :pk = DEPLOYMENT#D1BRV40
    :sk_prefix = STACK#
```

---

### Pattern 5: Get Recent Logs for Deployment

**Use Case:** View deployment logs
**Query:**
```python
logs = log_repo.get_logs("D1BRV40", limit=100)
```
**DynamoDB:**
```
Query:
  Table: Logs
  KeyConditionExpression: PK = :pk AND begins_with(SK, :sk_prefix)
  ExpressionAttributeValues:
    :pk = DEPLOYMENT#D1BRV40
    :sk_prefix = TIMESTAMP#
  ScanIndexForward: false (newest first)
  Limit: 100
```

---

### Pattern 6: Query Error Logs

**Use Case:** Find all error logs
**Query:**
```python
errors = log_repo.get_logs_by_level("ERROR", limit=50)
```
**DynamoDB:**
```
Query:
  Table: Logs
  IndexName: LogLevelIndex
  KeyConditionExpression: level = :level
  ExpressionAttributeValues:
    :level = ERROR
  ScanIndexForward: false (newest first)
  Limit: 50
```

---

### Pattern 7: Record Metric

**Use Case:** Store deployment duration metric
**Query:**
```python
metric_repo.record_metric(
    "stack_deployment_duration",
    value=300,
    unit="seconds",
    dimensions={"deployment_id": "D1BRV40", "stack_name": "network"}
)
```
**DynamoDB:**
```
PutItem:
  Table: Metrics
  Item:
    PK: METRIC#stack_deployment_duration
    SK: TIMESTAMP#2025-10-23T10:10:00Z
    value: 300
    unit: seconds
    dimensions: {deployment_id: D1BRV40, stack_name: network}
    ttl: 1761350400
```

---

## Code Implementation

### Python Client Library

#### File: `client.py`

```python
"""
DynamoDB Client Wrapper
Architecture 3.1
"""

import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError

from cloud_db.utils.logger import get_logger

logger = get_logger(__name__)


class DynamoDBClient:
    """
    DynamoDB client wrapper with connection pooling and error handling.
    """

    def __init__(
        self,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize DynamoDB client.

        Args:
            region: AWS region (default from env or us-east-1)
            endpoint_url: Custom endpoint URL (for local testing)
        """
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.endpoint_url = endpoint_url

        self._client = None
        self._resource = None

    @property
    def client(self):
        """Get boto3 DynamoDB client (lazy initialization)"""
        if self._client is None:
            self._client = boto3.client(
                'dynamodb',
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
            logger.info(f"DynamoDB client initialized (region: {self.region})")
        return self._client

    @property
    def resource(self):
        """Get boto3 DynamoDB resource (lazy initialization)"""
        if self._resource is None:
            self._resource = boto3.resource(
                'dynamodb',
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
            logger.info(f"DynamoDB resource initialized (region: {self.region})")
        return self._resource

    def get_table(self, table_name: str):
        """
        Get DynamoDB table resource.

        Args:
            table_name: Name of the table

        Returns:
            boto3 Table resource
        """
        return self.resource.Table(table_name)

    def handle_error(self, error: ClientError, operation: str):
        """
        Handle DynamoDB client errors.

        Args:
            error: ClientError from boto3
            operation: Operation name for logging

        Raises:
            Appropriate exception based on error code
        """
        error_code = error.response['Error']['Code']
        error_message = error.response['Error']['Message']

        logger.error(f"DynamoDB error during {operation}: {error_code} - {error_message}")

        if error_code == 'ResourceNotFoundException':
            raise ValueError(f"Table or item not found: {error_message}")
        elif error_code == 'ConditionalCheckFailedException':
            raise ValueError(f"Conditional check failed: {error_message}")
        elif error_code == 'ValidationException':
            raise ValueError(f"Validation error: {error_message}")
        else:
            raise RuntimeError(f"DynamoDB error: {error_message}")


# Global client instance (singleton pattern)
_db_client: Optional[DynamoDBClient] = None


def get_db_client() -> DynamoDBClient:
    """
    Get global DynamoDB client instance.

    Returns:
        DynamoDBClient instance
    """
    global _db_client
    if _db_client is None:
        _db_client = DynamoDBClient()
    return _db_client
```

---

#### File: `models/deployment.py`

```python
"""
Deployment Data Model
Architecture 3.1
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class Deployment(BaseModel):
    """Deployment data model"""

    deployment_id: str = Field(..., pattern=r'^D[A-Z0-9]{6}$')
    organization: str
    project: str
    domain: str
    template: str
    status: str  # initialized/deploying/deployed/failed/destroying
    environments: Dict
    stacks: Dict
    manifest: str  # JSON string
    created_at: datetime
    updated_at: datetime
    created_by: str  # Cognito user ID
    version: int = Field(default=1, ge=1)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dynamodb(self) -> Dict:
        """Convert to DynamoDB item format"""
        return {
            "PK": f"DEPLOYMENT#{self.deployment_id}",
            "SK": "METADATA",
            "deployment_id": self.deployment_id,
            "organization": self.organization,
            "project": self.project,
            "domain": self.domain,
            "template": self.template,
            "status": self.status,
            "environments": self.environments,
            "stacks": self.stacks,
            "manifest": self.manifest,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "version": self.version,
        }

    @classmethod
    def from_dynamodb(cls, item: Dict) -> "Deployment":
        """Create from DynamoDB item"""
        return cls(
            deployment_id=item["deployment_id"],
            organization=item["organization"],
            project=item["project"],
            domain=item["domain"],
            template=item["template"],
            status=item["status"],
            environments=item["environments"],
            stacks=item["stacks"],
            manifest=item["manifest"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            created_by=item["created_by"],
            version=item["version"],
        )
```

---

#### File: `repositories/deployment_repository.py`

```python
"""
Deployment Repository
Architecture 3.1
"""

from datetime import datetime
from typing import List, Optional
from botocore.exceptions import ClientError

from cloud_db.client import get_db_client
from cloud_db.models.deployment import Deployment
from cloud_db.utils.logger import get_logger

logger = get_logger(__name__)

# Table name (from environment variable)
import os
TABLE_NAME = os.environ.get("DEPLOYMENTS_TABLE", "cloud-deployments")


class DeploymentRepository:
    """Repository for Deployment data access"""

    def __init__(self):
        self.db = get_db_client()
        self.table = self.db.get_table(TABLE_NAME)

    def create(self, deployment: Deployment) -> Deployment:
        """
        Create a new deployment.

        Args:
            deployment: Deployment object

        Returns:
            Created deployment

        Raises:
            ValueError: If deployment already exists
        """
        try:
            item = deployment.to_dynamodb()

            # Conditional: only create if doesn't exist
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(PK)'
            )

            logger.info(f"Created deployment: {deployment.deployment_id}")
            return deployment

        except ClientError as e:
            self.db.handle_error(e, "create_deployment")

    def get_by_id(self, deployment_id: str) -> Optional[Deployment]:
        """
        Get deployment by ID.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment object or None if not found
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'DEPLOYMENT#{deployment_id}',
                    'SK': 'METADATA'
                }
            )

            if 'Item' in response:
                return Deployment.from_dynamodb(response['Item'])
            return None

        except ClientError as e:
            self.db.handle_error(e, "get_deployment")

    def update(self, deployment: Deployment) -> Deployment:
        """
        Update deployment with optimistic locking.

        Args:
            deployment: Deployment object with updated fields

        Returns:
            Updated deployment

        Raises:
            ValueError: If version mismatch (concurrent update)
        """
        try:
            deployment.updated_at = datetime.utcnow()
            deployment.version += 1

            item = deployment.to_dynamodb()
            old_version = deployment.version - 1

            # Optimistic locking: only update if version matches
            self.table.put_item(
                Item=item,
                ConditionExpression='version = :old_version',
                ExpressionAttributeValues={
                    ':old_version': old_version
                }
            )

            logger.info(f"Updated deployment: {deployment.deployment_id} (version {deployment.version})")
            return deployment

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(
                    f"Version mismatch for deployment {deployment.deployment_id}. "
                    "Another update occurred. Please refresh and try again."
                )
            self.db.handle_error(e, "update_deployment")

    def delete(self, deployment_id: str) -> bool:
        """
        Delete deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            True if deleted, False if not found
        """
        try:
            self.table.delete_item(
                Key={
                    'PK': f'DEPLOYMENT#{deployment_id}',
                    'SK': 'METADATA'
                }
            )

            logger.info(f"Deleted deployment: {deployment_id}")
            return True

        except ClientError as e:
            self.db.handle_error(e, "delete_deployment")

    def list_by_organization(
        self,
        organization: str,
        limit: int = 50,
        next_token: Optional[str] = None
    ) -> tuple[List[Deployment], Optional[str]]:
        """
        List deployments by organization.

        Args:
            organization: Organization name
            limit: Maximum results
            next_token: Pagination token

        Returns:
            Tuple of (deployments list, next_token)
        """
        try:
            query_params = {
                'IndexName': 'OrganizationIndex',
                'KeyConditionExpression': 'organization = :org',
                'ExpressionAttributeValues': {
                    ':org': organization
                },
                'ScanIndexForward': False,  # Newest first
                'Limit': limit
            }

            if next_token:
                query_params['ExclusiveStartKey'] = next_token

            response = self.table.query(**query_params)

            deployments = [
                Deployment.from_dynamodb(item)
                for item in response.get('Items', [])
            ]

            next_token = response.get('LastEvaluatedKey')

            logger.info(f"Listed {len(deployments)} deployments for organization: {organization}")
            return deployments, next_token

        except ClientError as e:
            self.db.handle_error(e, "list_deployments")

    def list_by_status(
        self,
        status: str,
        limit: int = 50,
        next_token: Optional[str] = None
    ) -> tuple[List[Deployment], Optional[str]]:
        """
        List deployments by status.

        Args:
            status: Deployment status
            limit: Maximum results
            next_token: Pagination token

        Returns:
            Tuple of (deployments list, next_token)
        """
        try:
            query_params = {
                'IndexName': 'StatusIndex',
                'KeyConditionExpression': 'status = :status',
                'ExpressionAttributeValues': {
                    ':status': status
                },
                'ScanIndexForward': False,  # Newest first
                'Limit': limit
            }

            if next_token:
                query_params['ExclusiveStartKey'] = next_token

            response = self.table.query(**query_params)

            deployments = [
                Deployment.from_dynamodb(item)
                for item in response.get('Items', [])
            ]

            next_token = response.get('LastEvaluatedKey')

            logger.info(f"Listed {len(deployments)} deployments with status: {status}")
            return deployments, next_token

        except ClientError as e:
            self.db.handle_error(e, "list_deployments_by_status")
```

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py                       # Shared fixtures
│
├── test_models/                      # Model tests (8 tests)
│   ├── test_deployment.py            # 2 tests
│   ├── test_stack.py                 # 2 tests
│   ├── test_log_entry.py             # 2 tests
│   └── test_metric.py                # 2 tests
│
├── test_repositories/                # Repository tests (16 tests)
│   ├── test_deployment_repository.py # 6 tests
│   ├── test_stack_repository.py      # 4 tests
│   ├── test_log_repository.py        # 3 tests
│   └── test_metric_repository.py     # 3 tests
│
├── test_graphql/                     # GraphQL tests (12 tests)
│   ├── test_queries.py               # 6 tests
│   ├── test_mutations.py             # 4 tests
│   └── test_subscriptions.py         # 2 tests
│
└── test_integration/                 # Integration tests (4 tests)
    ├── test_full_flow.py             # 2 tests
    └── test_cognito_integration.py   # 2 tests

Total: ~40 tests
```

### Test Fixtures (`conftest.py`)

```python
"""
Pytest Fixtures for Database Testing
Architecture 3.1
"""

import pytest
import boto3
from moto import mock_dynamodb
from datetime import datetime

from cloud_db.client import DynamoDBClient
from cloud_db.models.deployment import Deployment


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing"""
    with mock_dynamodb():
        # Create mock DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Create Deployments table
        table = dynamodb.create_table(
            TableName='test-deployments',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'organization', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'OrganizationIndex',
                    'KeySchema': [
                        {'AttributeName': 'organization', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        yield table


@pytest.fixture
def sample_deployment():
    """Sample deployment for testing"""
    return Deployment(
        deployment_id="D1TEST1",
        organization="TestOrg",
        project="test-project",
        domain="test.example.com",
        template="default",
        status="initialized",
        environments={"dev": {"enabled": True, "region": "us-east-1"}},
        stacks={"network": {"enabled": True}},
        manifest="{}",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="test-user-123",
        version=1
    )
```

---

### Example Repository Tests

```python
"""
Tests for Deployment Repository
Architecture 3.1
"""

import pytest
from datetime import datetime

from cloud_db.repositories.deployment_repository import DeploymentRepository
from cloud_db.models.deployment import Deployment


def test_create_deployment(mock_dynamodb_table, sample_deployment):
    """Test creating a deployment"""
    repo = DeploymentRepository()

    # Create deployment
    result = repo.create(sample_deployment)

    assert result.deployment_id == sample_deployment.deployment_id
    assert result.organization == sample_deployment.organization


def test_get_deployment_by_id(mock_dynamodb_table, sample_deployment):
    """Test retrieving a deployment by ID"""
    repo = DeploymentRepository()

    # Create deployment
    repo.create(sample_deployment)

    # Get deployment
    result = repo.get_by_id(sample_deployment.deployment_id)

    assert result is not None
    assert result.deployment_id == sample_deployment.deployment_id


def test_update_deployment(mock_dynamodb_table, sample_deployment):
    """Test updating a deployment with optimistic locking"""
    repo = DeploymentRepository()

    # Create deployment
    created = repo.create(sample_deployment)

    # Update deployment
    created.status = "deployed"
    updated = repo.update(created)

    assert updated.status == "deployed"
    assert updated.version == 2


def test_optimistic_locking_conflict(mock_dynamodb_table, sample_deployment):
    """Test optimistic locking prevents concurrent updates"""
    repo = DeploymentRepository()

    # Create deployment
    created = repo.create(sample_deployment)

    # Simulate concurrent update
    created.status = "deployed"
    repo.update(created)

    # Try to update with old version
    with pytest.raises(ValueError, match="Version mismatch"):
        created.version = 1  # Old version
        repo.update(created)


# ... 2 more repository tests
```

---

## Implementation Plan

### Phase 1: Database Schema (Est: 4 hours)

**1.1 DynamoDB Tables**
- Design table schemas (Deployments, Stacks, Logs, Metrics)
- Create Pulumi infrastructure code (`infrastructure/dynamodb.ts`)
- Deploy tables to AWS
- Verify table creation and indexes

**1.2 Data Models**
- Create Pydantic models (`models/`)
- Implement to_dynamodb() and from_dynamodb() methods
- Add validation rules
- Test serialization/deserialization

---

### Phase 2: Data Access Layer (Est: 6 hours)

**2.1 DynamoDB Client**
- Implement client wrapper (`client.py`)
- Add connection pooling
- Implement error handling
- Test client connectivity

**2.2 Repositories**
- Implement deployment repository (6 methods)
- Implement stack repository (5 methods)
- Implement log repository (4 methods)
- Implement metric repository (3 methods)
- Add optimistic locking
- Test all CRUD operations

---

### Phase 3: GraphQL API (Est: 8 hours)

**3.1 GraphQL Schema**
- Define schema (`graphql/schema.graphql`)
- Define queries, mutations, subscriptions
- Add input/output types
- Document schema

**3.2 AppSync Setup**
- Create Pulumi infrastructure (`infrastructure/appsync.ts`)
- Configure Cognito authentication
- Deploy AppSync API
- Verify API creation

**3.3 Resolvers**
- Implement VTL resolvers for queries
- Implement VTL resolvers for mutations
- Implement subscription resolvers
- Test all resolvers

---

### Phase 4: Integration (Est: 4 hours)

**4.1 CLI Integration**
- Update deployment manager to use database
- Update orchestrator to log to database
- Update state manager to use database
- Test CLI with database

**4.2 API Integration**
- Update REST API to use database
- Add database queries to endpoints
- Test API with database

---

### Phase 5: Testing (Est: 6 hours)

**5.1 Unit Tests** (3 hours)
- Model tests (8 tests)
- Repository tests (16 tests)

**5.2 GraphQL Tests** (2 hours)
- Query tests (6 tests)
- Mutation tests (4 tests)
- Subscription tests (2 tests)

**5.3 Integration Tests** (1 hour)
- Full flow tests (2 tests)
- Cognito integration tests (2 tests)

---

### Phase 6: Documentation (Est: 2 hours)

**6.1 Database Documentation**
- Schema documentation
- Query examples
- Best practices

**6.2 GraphQL Documentation**
- API reference
- Query examples
- Subscription examples

**Total Estimated Time: 30 hours**

---

## Success Criteria

### Functional Requirements

- [ ] **4 DynamoDB tables** created and configured
- [ ] **GraphQL schema** with 15+ queries/mutations
- [ ] **AWS AppSync API** deployed and accessible
- [ ] **Cognito authentication** working on GraphQL API
- [ ] **Python client library** with repositories
- [ ] **40+ tests passing** (models + repositories + GraphQL)
- [ ] **CLI/API integration** storing data in database
- [ ] **Real-time subscriptions** working for monitoring

### Non-Functional Requirements

- [ ] **Query latency** < 50ms for GetItem operations
- [ ] **Query latency** < 100ms for Query operations
- [ ] **Throughput** Support 1000+ req/sec
- [ ] **Data consistency** Optimistic locking prevents conflicts
- [ ] **TTL** Automatic expiration of logs and metrics
- [ ] **Security** All GraphQL operations require Cognito auth

### Code Quality

- [ ] **Type hints** on all functions
- [ ] **Docstrings** on all public functions
- [ ] **Tests** 90%+ code coverage
- [ ] **DynamoDB best practices** Single table design, GSIs, TTL
- [ ] **GraphQL best practices** Type-safe schema, pagination

---

## Appendix: Code Examples

### Example: Using Deployment Repository

```python
from cloud_db.repositories.deployment_repository import DeploymentRepository
from cloud_db.models.deployment import Deployment
from datetime import datetime

# Create repository
repo = DeploymentRepository()

# Create new deployment
deployment = Deployment(
    deployment_id="D1BRV40",
    organization="MyOrg",
    project="my-project",
    domain="myproject.example.com",
    template="default",
    status="initialized",
    environments={"dev": {"enabled": True, "region": "us-east-1"}},
    stacks={"network": {"enabled": True}},
    manifest="{}",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    created_by="user-123",
)

# Save to database
repo.create(deployment)

# Get by ID
deployment = repo.get_by_id("D1BRV40")
print(f"Status: {deployment.status}")

# Update status
deployment.status = "deployed"
repo.update(deployment)

# List by organization
deployments, next_token = repo.list_by_organization("MyOrg", limit=10)
for d in deployments:
    print(f"{d.deployment_id}: {d.status}")
```

---

### Example: GraphQL Query

```graphql
query GetDeploymentWithStacks($deploymentId: ID!) {
  getDeployment(deployment_id: $deploymentId) {
    deployment_id
    organization
    project
    status
    created_at
    updated_at
  }

  listStacks(deployment_id: $deploymentId) {
    items {
      stack_name
      environment
      status
      resource_count
      outputs
    }
  }
}
```

---

### Example: GraphQL Subscription

```graphql
subscription OnDeploymentUpdated($deploymentId: ID!) {
  onDeploymentUpdated(deployment_id: $deploymentId) {
    deployment_id
    status
    updated_at
  }
}
```

---

**End of Session 5 Document**

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 5
**Document Version:** 1.0
**Last Updated:** 2025-10-23
