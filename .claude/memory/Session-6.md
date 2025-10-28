# Session 6: WebSocket Monitoring

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 6
**Focus:** Real-time Monitoring via WebSocket (API Gateway WebSocket + AppSync Subscriptions)
**Date:** 2025-10-23

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Session Context](#session-context)
3. [WebSocket Architecture](#websocket-architecture)
4. [API Gateway WebSocket API](#api-gateway-websocket-api)
5. [AppSync Subscriptions](#appsync-subscriptions)
6. [Cognito Authentication](#cognito-authentication)
7. [Message Protocol](#message-protocol)
8. [Client Implementation](#client-implementation)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Plan](#implementation-plan)
11. [Success Criteria](#success-criteria)

---

## Executive Summary

### Purpose of Session 6

Session 6 implements **real-time monitoring** for the Cloud Infrastructure Orchestration Platform using **WebSocket connections** to push live updates to clients. This enables dashboards, CLIs, and mobile apps to receive instant notifications about deployment progress, stack status changes, and system events.

### Key Objectives

1. **WebSocket API** - Build API Gateway WebSocket API for bidirectional communication
2. **AppSync Subscriptions** - Leverage GraphQL subscriptions for real-time data
3. **Cognito Auth** - Secure WebSocket connections with Cognito JWT tokens
4. **Message Protocol** - Define JSON message format for all event types
5. **Client Libraries** - Python and JavaScript WebSocket clients
6. **Connection Management** - Handle connect/disconnect/ping/pong
7. **Event Broadcasting** - Push updates to subscribed clients

### Why WebSocket?

**Advantages over HTTP Polling:**
- **Real-time** - Instant updates, no polling delay
- **Efficient** - Single persistent connection vs. repeated requests
- **Bidirectional** - Server can push data to client
- **Lower latency** - No HTTP overhead for each message
- **Lower cost** - Fewer API requests

**Use Cases:**
- Live deployment progress updates
- Stack status changes
- Real-time log streaming
- System health monitoring
- Multi-user collaborative dashboards

### What Gets Built

```
cloud/tools/websocket/
├── src/
│   └── cloud_ws/
│       ├── __init__.py
│       ├── server.py                  # WebSocket server (Lambda)
│       ├── handlers/                  # Lambda handlers
│       │   ├── __init__.py
│       │   ├── connect.py             # $connect handler
│       │   ├── disconnect.py          # $disconnect handler
│       │   ├── authorize.py           # Cognito authorization
│       │   └── default.py             # $default handler
│       ├── broadcast/                 # Broadcasting
│       │   ├── __init__.py
│       │   ├── broadcaster.py         # Broadcast messages
│       │   └── connection_manager.py  # Track connections
│       ├── protocol/                  # Message protocol
│       │   ├── __init__.py
│       │   ├── messages.py            # Message types
│       │   └── serializer.py          # JSON serialization
│       └── utils/                     # Utilities
│           ├── __init__.py
│           └── logger.py              # Logger
│
├── client/                            # Client libraries
│   ├── python/                        # Python client
│   │   ├── cloud_ws_client/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # WebSocket client
│   │   │   ├── reconnect.py           # Auto-reconnect
│   │   │   └── handlers.py            # Event handlers
│   │   └── examples/
│   │       └── monitor.py             # Example usage
│   │
│   └── javascript/                    # JavaScript client
│       ├── src/
│       │   ├── client.ts              # WebSocket client
│       │   ├── reconnect.ts           # Auto-reconnect
│       │   └── types.ts               # TypeScript types
│       └── examples/
│           └── monitor.html           # Web dashboard example
│
├── infrastructure/                    # IaC for WebSocket
│   ├── api_gateway.ts                 # API Gateway WebSocket API
│   ├── lambda.ts                      # Lambda functions
│   ├── dynamodb.ts                    # Connection tracking table
│   └── iam.ts                         # IAM roles/policies
│
├── tests/                             # Test suite
│   ├── test_handlers/
│   ├── test_broadcast/
│   ├── test_protocol/
│   └── test_integration/
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                             │
│  (CLI, Web Dashboard, Mobile Apps, Monitoring Tools)        │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ WebSocket connections
                           │ wss://xxx.execute-api.us-east-1.amazonaws.com
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS API Gateway WebSocket API                  │
│  Routes:                                                    │
│  - $connect    → Connect handler (auth)                    │
│  - $disconnect → Disconnect handler                        │
│  - $default    → Default message handler                   │
│  - subscribe   → Subscribe to events                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Invoke Lambda
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Lambda Functions                         │
│  - ConnectHandler: Authenticate and register connection     │
│  - DisconnectHandler: Clean up connection                   │
│  - SubscribeHandler: Subscribe to deployment events         │
│  - BroadcastHandler: Push events to subscribed clients      │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Store connections
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               DynamoDB Connections Table                    │
│  PK: connectionId                                           │
│  Attributes: user_id, subscriptions, connected_at, ttl      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Event Sources                             │
│  - Orchestrator (deployment events)                         │
│  - Stack operations (status changes)                        │
│  - Log writer (new logs)                                    │
│  - Metric collector (new metrics)                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Publish events
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    EventBridge / SNS                        │
│  Event bus for system events                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Trigger Lambda
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Broadcast Lambda                            │
│  - Query subscribed connections from DynamoDB               │
│  - Send message to each connection via API Gateway          │
└─────────────────────────────────────────────────────────────┘
```

---

## Session Context

### What Was Built Before

**Session 1:** Complete documentation
**Session 2.1:** CLI framework
**Session 3:** Complete CLI implementation
**Session 4:** REST API with FastAPI + Cognito auth
**Session 5:** DynamoDB + GraphQL (AppSync) with real-time subscriptions

### What Session 6 Adds

1. **API Gateway WebSocket API** - Managed WebSocket endpoint
2. **Lambda Handlers** - Connect/disconnect/message handlers
3. **Connection Management** - Track active connections in DynamoDB
4. **Event Broadcasting** - Push events to subscribed clients
5. **Python Client** - WebSocket client library with auto-reconnect
6. **JavaScript Client** - Browser-compatible WebSocket client
7. **Message Protocol** - Standardized JSON message format

### Two WebSocket Approaches

Session 6 implements **two complementary approaches**:

**Approach 1: API Gateway WebSocket API**
- Custom WebSocket endpoint
- Full control over connection lifecycle
- Custom message routing
- Direct Lambda integration
- Best for: Custom monitoring dashboards, CLI tools

**Approach 2: AppSync GraphQL Subscriptions** (from Session 5)
- GraphQL subscriptions over WebSocket
- Automatic DynamoDB integration
- Type-safe schema
- Built-in Cognito auth
- Best for: GraphQL clients, web dashboards

Clients can choose either approach based on their needs.

---

## WebSocket Architecture

### Design Principles

1. **Scalability** - Support thousands of concurrent connections
2. **Reliability** - Auto-reconnect on connection loss
3. **Security** - Cognito JWT authentication on connect
4. **Efficiency** - Only send updates to subscribed clients
5. **Simplicity** - JSON message protocol, easy to integrate

### Connection Lifecycle

```
1. Client connects with JWT token
   └─> wss://xxx.execute-api.us-east-1.amazonaws.com?token=<jwt>

2. $connect route invoked
   └─> ConnectHandler Lambda
       └─> Verify JWT with Cognito
       └─> Store connection in DynamoDB
       └─> Return 200 OK

3. Client subscribes to events
   └─> Send JSON: {"action": "subscribe", "deployment_id": "D1BRV40"}
   └─> SubscribeHandler Lambda
       └─> Update connection subscriptions in DynamoDB

4. Events occur (deployment progress, status changes)
   └─> Event published to EventBridge/SNS
   └─> BroadcastHandler Lambda triggered
       └─> Query subscribed connections from DynamoDB
       └─> Send message to each connection via API Gateway

5. Client receives message
   └─> JSON: {"type": "deployment.status", "data": {...}}

6. Client disconnects
   └─> $disconnect route invoked
   └─> DisconnectHandler Lambda
       └─> Remove connection from DynamoDB
```

### Connection Table Schema

**DynamoDB Table:** `cloud-websocket-connections`

```
PK: connectionId (String)
```

**Attributes:**
```
- connectionId (String) - API Gateway connection ID
- user_id (String) - Cognito user ID
- email (String) - User email
- subscriptions (List<String>) - Subscribed deployment IDs
- connected_at (String) - ISO 8601 timestamp
- last_ping (String) - ISO 8601 timestamp
- ttl (Number) - TTL for automatic cleanup (24 hours)
```

**Example Item:**
```json
{
  "connectionId": "dGVzdC1jb25uZWN0aW9uLWlk",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "subscriptions": ["D1BRV40", "D2XYZ90"],
  "connected_at": "2025-10-23T10:00:00Z",
  "last_ping": "2025-10-23T10:05:00Z",
  "ttl": 1729767600
}
```

---

## API Gateway WebSocket API

### API Configuration

```typescript
// infrastructure/api_gateway.ts (Pulumi)

import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

// Create WebSocket API
const websocketApi = new aws.apigatewayv2.Api("cloud-websocket-api", {
  name: "cloud-websocket-api",
  protocolType: "WEBSOCKET",
  routeSelectionExpression: "$request.body.action",
  description: "WebSocket API for real-time monitoring",
});

// $connect route
const connectIntegration = new aws.apigatewayv2.Integration("connect-integration", {
  apiId: websocketApi.id,
  integrationType: "AWS_PROXY",
  integrationUri: connectLambda.invokeArn,
});

const connectRoute = new aws.apigatewayv2.Route("connect-route", {
  apiId: websocketApi.id,
  routeKey: "$connect",
  authorizationType: "NONE",  // Auth handled in Lambda
  target: pulumi.interpolate`integrations/${connectIntegration.id}`,
});

// $disconnect route
const disconnectIntegration = new aws.apigatewayv2.Integration("disconnect-integration", {
  apiId: websocketApi.id,
  integrationType: "AWS_PROXY",
  integrationUri: disconnectLambda.invokeArn,
});

const disconnectRoute = new aws.apigatewayv2.Route("disconnect-route", {
  apiId: websocketApi.id,
  routeKey: "$disconnect",
  target: pulumi.interpolate`integrations/${disconnectIntegration.id}`,
});

// $default route
const defaultIntegration = new aws.apigatewayv2.Integration("default-integration", {
  apiId: websocketApi.id,
  integrationType: "AWS_PROXY",
  integrationUri: defaultLambda.invokeArn,
});

const defaultRoute = new aws.apigatewayv2.Route("default-route", {
  apiId: websocketApi.id,
  routeKey: "$default",
  target: pulumi.interpolate`integrations/${defaultIntegration.id}`,
});

// Deploy API
const deployment = new aws.apigatewayv2.Deployment("websocket-deployment", {
  apiId: websocketApi.id,
  description: "WebSocket API deployment",
}, { dependsOn: [connectRoute, disconnectRoute, defaultRoute] });

const stage = new aws.apigatewayv2.Stage("production", {
  apiId: websocketApi.id,
  deploymentId: deployment.id,
  name: "production",
  description: "Production stage",
  defaultRouteSettings: {
    throttlingBurstLimit: 5000,
    throttlingRateLimit: 10000,
  },
});

// Export WebSocket URL
export const websocketUrl = pulumi.interpolate`${websocketApi.apiEndpoint}/${stage.name}`;
// Output: wss://xxxxx.execute-api.us-east-1.amazonaws.com/production
```

---

### Lambda Handlers

#### File: `handlers/connect.py`

```python
"""
WebSocket $connect Handler
Architecture 3.1

Authenticates connection and registers in DynamoDB.
"""

import json
import os
from datetime import datetime, timedelta
import boto3
from jose import JWTError

from cloud_ws.handlers.authorize import verify_cognito_token
from cloud_ws.utils.logger import get_logger

logger = get_logger(__name__)

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE_NAME'])


def lambda_handler(event, context):
    """
    Handle WebSocket $connect event.

    Query parameters:
        token: Cognito JWT token (required)

    Returns:
        statusCode: 200 if authorized, 401 if unauthorized
    """
    connection_id = event['requestContext']['connectionId']

    logger.info(f"Connection attempt: {connection_id}")

    try:
        # Extract token from query string
        query_params = event.get('queryStringParameters', {}) or {}
        token = query_params.get('token')

        if not token:
            logger.warning(f"Connection {connection_id}: Missing token")
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Unauthorized: Missing token'})
            }

        # Verify token with Cognito
        user_info = verify_cognito_token(token)

        # Store connection in DynamoDB
        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())

        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'user_id': user_info['user_id'],
                'email': user_info['email'],
                'subscriptions': [],
                'connected_at': datetime.utcnow().isoformat(),
                'last_ping': datetime.utcnow().isoformat(),
                'ttl': ttl,
            }
        )

        logger.info(f"Connection {connection_id} registered for user {user_info['email']}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected'})
        }

    except JWTError as e:
        logger.warning(f"Connection {connection_id}: Invalid token - {e}")
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Unauthorized: Invalid token'})
        }

    except Exception as e:
        logger.error(f"Connection {connection_id}: Error - {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }
```

---

#### File: `handlers/disconnect.py`

```python
"""
WebSocket $disconnect Handler
Architecture 3.1

Removes connection from DynamoDB.
"""

import json
import os
import boto3

from cloud_ws.utils.logger import get_logger

logger = get_logger(__name__)

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE_NAME'])


def lambda_handler(event, context):
    """
    Handle WebSocket $disconnect event.

    Removes connection from tracking table.

    Returns:
        statusCode: 200 always
    """
    connection_id = event['requestContext']['connectionId']

    logger.info(f"Disconnecting: {connection_id}")

    try:
        # Remove connection from DynamoDB
        connections_table.delete_item(
            Key={'connectionId': connection_id}
        )

        logger.info(f"Connection {connection_id} removed")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected'})
        }

    except Exception as e:
        logger.error(f"Connection {connection_id}: Error during disconnect - {e}", exc_info=True)
        # Return 200 anyway (connection will be cleaned up by TTL)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected'})
        }
```

---

#### File: `handlers/default.py`

```python
"""
WebSocket $default Handler
Architecture 3.1

Handles messages from clients (subscribe, unsubscribe, ping).
"""

import json
import os
from datetime import datetime
import boto3

from cloud_ws.utils.logger import get_logger

logger = get_logger(__name__)

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE_NAME'])

# API Gateway Management API client
apigateway_management = None  # Initialized per-request


def get_apigateway_client(event):
    """Get API Gateway Management API client for this connection"""
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    endpoint_url = f"https://{domain_name}/{stage}"

    return boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)


def lambda_handler(event, context):
    """
    Handle WebSocket messages.

    Message format:
        {
            "action": "subscribe" | "unsubscribe" | "ping",
            "deployment_id": "D1BRV40"  (for subscribe/unsubscribe)
        }

    Returns:
        statusCode: 200 if successful
    """
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event.get('body', '{}'))

    logger.info(f"Message from {connection_id}: {body}")

    try:
        action = body.get('action')

        if action == 'subscribe':
            return handle_subscribe(connection_id, body)

        elif action == 'unsubscribe':
            return handle_unsubscribe(connection_id, body)

        elif action == 'ping':
            return handle_ping(connection_id, event)

        else:
            logger.warning(f"Unknown action: {action}")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': f'Unknown action: {action}'})
            }

    except Exception as e:
        logger.error(f"Error handling message from {connection_id}: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }


def handle_subscribe(connection_id: str, body: dict):
    """Handle subscribe action"""
    deployment_id = body.get('deployment_id')

    if not deployment_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing deployment_id'})
        }

    # Get current connection
    response = connections_table.get_item(Key={'connectionId': connection_id})

    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Connection not found'})
        }

    connection = response['Item']

    # Add to subscriptions (if not already subscribed)
    subscriptions = set(connection.get('subscriptions', []))
    subscriptions.add(deployment_id)

    # Update connection
    connections_table.update_item(
        Key={'connectionId': connection_id},
        UpdateExpression='SET subscriptions = :subs',
        ExpressionAttributeValues={
            ':subs': list(subscriptions)
        }
    )

    logger.info(f"Connection {connection_id} subscribed to {deployment_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Subscribed',
            'deployment_id': deployment_id
        })
    }


def handle_unsubscribe(connection_id: str, body: dict):
    """Handle unsubscribe action"""
    deployment_id = body.get('deployment_id')

    if not deployment_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing deployment_id'})
        }

    # Get current connection
    response = connections_table.get_item(Key={'connectionId': connection_id})

    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Connection not found'})
        }

    connection = response['Item']

    # Remove from subscriptions
    subscriptions = set(connection.get('subscriptions', []))
    subscriptions.discard(deployment_id)

    # Update connection
    connections_table.update_item(
        Key={'connectionId': connection_id},
        UpdateExpression='SET subscriptions = :subs',
        ExpressionAttributeValues={
            ':subs': list(subscriptions)
        }
    )

    logger.info(f"Connection {connection_id} unsubscribed from {deployment_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Unsubscribed',
            'deployment_id': deployment_id
        })
    }


def handle_ping(connection_id: str, event: dict):
    """Handle ping action (keep-alive)"""
    # Update last_ping timestamp
    connections_table.update_item(
        Key={'connectionId': connection_id},
        UpdateExpression='SET last_ping = :ts',
        ExpressionAttributeValues={
            ':ts': datetime.utcnow().isoformat()
        }
    )

    # Send pong response
    apigateway = get_apigateway_client(event)
    apigateway.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps({'type': 'pong', 'timestamp': datetime.utcnow().isoformat()})
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Pong'})
    }
```

---

#### File: `handlers/authorize.py`

```python
"""
Cognito Authorization for WebSocket
Architecture 3.1
"""

import os
import requests
from jose import JWTError, jwt
from functools import lru_cache

from cloud_ws.utils.logger import get_logger

logger = get_logger(__name__)

# Cognito configuration
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
COGNITO_APP_CLIENT_ID = os.environ["COGNITO_APP_CLIENT_ID"]

COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def get_cognito_public_keys():
    """Fetch Cognito public keys for JWT verification (cached)"""
    try:
        response = requests.get(COGNITO_JWKS_URL, timeout=10)
        response.raise_for_status()
        jwks = response.json()

        keys = {}
        for key_data in jwks["keys"]:
            kid = key_data["kid"]
            keys[kid] = key_data

        logger.info(f"Loaded {len(keys)} Cognito public keys")
        return keys

    except Exception as e:
        logger.error(f"Failed to load Cognito public keys: {e}")
        raise


def verify_cognito_token(token: str) -> dict:
    """
    Verify Cognito JWT token.

    Args:
        token: JWT token string

    Returns:
        User info dict with user_id, email, groups

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        # Decode header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]

        # Get public key
        public_keys = get_cognito_public_keys()
        if kid not in public_keys:
            raise JWTError(f"Public key not found for kid: {kid}")

        public_key = public_keys[kid]

        # Decode and verify
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=COGNITO_ISSUER,
            audience=COGNITO_APP_CLIENT_ID,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            }
        )

        # Extract user info
        user_info = {
            "user_id": payload.get("sub"),
            "username": payload.get("cognito:username"),
            "email": payload.get("email"),
            "groups": payload.get("cognito:groups", []),
        }

        logger.debug(f"Token verified for user: {user_info['email']}")
        return user_info

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise
```

---

### Broadcasting Events

#### File: `broadcast/broadcaster.py`

```python
"""
Event Broadcaster
Architecture 3.1

Broadcasts events to subscribed WebSocket connections.
"""

import json
import os
from typing import List, Dict
import boto3

from cloud_ws.utils.logger import get_logger

logger = get_logger(__name__)

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE_NAME'])


class EventBroadcaster:
    """
    Broadcasts events to subscribed WebSocket connections.
    """

    def __init__(self, apigateway_endpoint: str):
        """
        Initialize broadcaster.

        Args:
            apigateway_endpoint: API Gateway endpoint URL
                Format: https://xxx.execute-api.us-east-1.amazonaws.com/production
        """
        self.apigateway = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=apigateway_endpoint
        )

    def broadcast_deployment_event(
        self,
        deployment_id: str,
        event_type: str,
        data: dict
    ):
        """
        Broadcast deployment event to subscribed connections.

        Args:
            deployment_id: Deployment ID
            event_type: Event type (e.g., "deployment.status", "stack.deployed")
            data: Event data
        """
        # Find subscribed connections
        connections = self._get_subscribed_connections(deployment_id)

        if not connections:
            logger.info(f"No connections subscribed to {deployment_id}")
            return

        # Prepare message
        message = {
            'type': event_type,
            'deployment_id': deployment_id,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
        }

        message_json = json.dumps(message)

        # Send to all connections
        success_count = 0
        failed_connections = []

        for connection in connections:
            connection_id = connection['connectionId']

            try:
                self.apigateway.post_to_connection(
                    ConnectionId=connection_id,
                    Data=message_json
                )
                success_count += 1

            except self.apigateway.exceptions.GoneException:
                # Connection no longer exists
                logger.warning(f"Connection gone: {connection_id}")
                failed_connections.append(connection_id)

            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                failed_connections.append(connection_id)

        # Clean up failed connections
        for connection_id in failed_connections:
            self._remove_connection(connection_id)

        logger.info(
            f"Broadcast {event_type} for {deployment_id}: "
            f"{success_count} sent, {len(failed_connections)} failed"
        )

    def _get_subscribed_connections(self, deployment_id: str) -> List[Dict]:
        """
        Get all connections subscribed to a deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            List of connection items
        """
        # Scan table for connections with this deployment_id in subscriptions
        # Note: In production, consider using a GSI for better performance
        response = connections_table.scan(
            FilterExpression='contains(subscriptions, :dep_id)',
            ExpressionAttributeValues={
                ':dep_id': deployment_id
            }
        )

        return response.get('Items', [])

    def _remove_connection(self, connection_id: str):
        """Remove stale connection from table"""
        try:
            connections_table.delete_item(
                Key={'connectionId': connection_id}
            )
            logger.info(f"Removed stale connection: {connection_id}")
        except Exception as e:
            logger.error(f"Error removing connection {connection_id}: {e}")


# Global broadcaster instance
_broadcaster: EventBroadcaster = None


def get_broadcaster() -> EventBroadcaster:
    """Get global broadcaster instance"""
    global _broadcaster
    if _broadcaster is None:
        endpoint = os.environ['APIGATEWAY_ENDPOINT']
        _broadcaster = EventBroadcaster(endpoint)
    return _broadcaster
```

---

## AppSync Subscriptions

### GraphQL Subscriptions (from Session 5)

AppSync provides an alternative WebSocket approach using GraphQL subscriptions:

```graphql
# GraphQL subscription
subscription OnDeploymentUpdated($deploymentId: ID!) {
  onDeploymentUpdated(deployment_id: $deploymentId) {
    deployment_id
    status
    updated_at
  }
}
```

**How it works:**
1. Client subscribes via AppSync WebSocket endpoint
2. AppSync automatically manages WebSocket connection
3. When mutation occurs (updateDeployment), AppSync pushes update
4. Client receives real-time update

**Advantages:**
- Type-safe schema
- Automatic Cognito auth
- No custom Lambda handlers
- Integrated with GraphQL queries/mutations

**Usage:**
```javascript
import { AWSAppSyncClient } from 'aws-appsync';

const client = new AWSAppSyncClient({
  url: 'https://xxx.appsync-api.us-east-1.amazonaws.com/graphql',
  region: 'us-east-1',
  auth: {
    type: 'AMAZON_COGNITO_USER_POOLS',
    jwtToken: idToken,
  },
});

// Subscribe to deployment updates
const subscription = client.subscribe({
  query: gql`
    subscription OnDeploymentUpdated($deploymentId: ID!) {
      onDeploymentUpdated(deployment_id: $deploymentId) {
        deployment_id
        status
        updated_at
      }
    }
  `,
  variables: { deploymentId: 'D1BRV40' },
}).subscribe({
  next: (data) => {
    console.log('Deployment updated:', data);
  },
  error: (error) => {
    console.error('Subscription error:', error);
  },
});
```

---

## Cognito Authentication

### WebSocket Authentication Flow

**Option 1: Query String Token**
```
wss://xxx.execute-api.us-east-1.amazonaws.com/production?token=<jwt_token>
```

**Option 2: Custom Header (HTTP Upgrade)**
```
GET /production HTTP/1.1
Host: xxx.execute-api.us-east-1.amazonaws.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: xxx
Authorization: Bearer <jwt_token>
```

**Token Validation:**
- Performed in $connect handler
- Uses same Cognito verification as REST API (Session 4)
- Connection rejected if token invalid or expired

**Token Refresh:**
- Clients must reconnect with new token before expiration
- Typically: ID token valid for 1 hour
- Client libraries handle auto-reconnect with refreshed token

---

## Message Protocol

### Message Types

**Client → Server Messages:**

```json
// Subscribe to deployment
{
  "action": "subscribe",
  "deployment_id": "D1BRV40"
}

// Unsubscribe from deployment
{
  "action": "unsubscribe",
  "deployment_id": "D1BRV40"
}

// Ping (keep-alive)
{
  "action": "ping"
}
```

**Server → Client Messages:**

```json
// Deployment status changed
{
  "type": "deployment.status",
  "deployment_id": "D1BRV40",
  "data": {
    "status": "deploying",
    "current_layer": 2,
    "total_layers": 4
  },
  "timestamp": "2025-10-23T10:05:00Z"
}

// Stack deployed
{
  "type": "stack.deployed",
  "deployment_id": "D1BRV40",
  "data": {
    "stack_name": "network",
    "environment": "dev",
    "duration_seconds": 300,
    "resource_count": 15
  },
  "timestamp": "2025-10-23T10:10:00Z"
}

// Stack failed
{
  "type": "stack.failed",
  "deployment_id": "D1BRV40",
  "data": {
    "stack_name": "database-rds",
    "environment": "dev",
    "error_message": "Subnet not found"
  },
  "timestamp": "2025-10-23T10:12:00Z"
}

// New log entry
{
  "type": "log.created",
  "deployment_id": "D1BRV40",
  "data": {
    "level": "info",
    "message": "Starting deployment of security-dev",
    "stack_name": "security",
    "environment": "dev"
  },
  "timestamp": "2025-10-23T10:06:00Z"
}

// Pong (response to ping)
{
  "type": "pong",
  "timestamp": "2025-10-23T10:05:30Z"
}
```

---

## Client Implementation

### Python WebSocket Client

#### File: `client/python/cloud_ws_client/client.py`

```python
"""
Python WebSocket Client
Architecture 3.1
"""

import asyncio
import json
from typing import Callable, Optional, Dict
import websockets
from websockets.exceptions import ConnectionClosed

from cloud_ws_client.reconnect import ReconnectWebSocket
from cloud_ws_client.utils.logger import get_logger

logger = get_logger(__name__)


class CloudWebSocketClient:
    """
    WebSocket client for Cloud Platform real-time monitoring.

    Features:
    - Automatic reconnection
    - Message handlers
    - Subscription management
    - Keep-alive pings
    """

    def __init__(
        self,
        endpoint: str,
        token: str,
        auto_reconnect: bool = True,
        ping_interval: int = 30,
    ):
        """
        Initialize WebSocket client.

        Args:
            endpoint: WebSocket endpoint URL (wss://...)
            token: Cognito JWT token
            auto_reconnect: Enable automatic reconnection
            ping_interval: Seconds between keep-alive pings
        """
        self.endpoint = f"{endpoint}?token={token}"
        self.token = token
        self.auto_reconnect = auto_reconnect
        self.ping_interval = ping_interval

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: set = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.running = False

    async def connect(self):
        """Connect to WebSocket server"""
        logger.info(f"Connecting to {self.endpoint}")

        if self.auto_reconnect:
            self.ws = await ReconnectWebSocket(self.endpoint)
        else:
            self.ws = await websockets.connect(self.endpoint)

        logger.info("Connected")
        self.running = True

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.running = False

        if self.ws:
            await self.ws.close()
            self.ws = None

        logger.info("Disconnected")

    async def subscribe(self, deployment_id: str):
        """
        Subscribe to deployment events.

        Args:
            deployment_id: Deployment ID to subscribe to
        """
        message = {
            "action": "subscribe",
            "deployment_id": deployment_id
        }

        await self.ws.send(json.dumps(message))
        self.subscriptions.add(deployment_id)

        logger.info(f"Subscribed to {deployment_id}")

    async def unsubscribe(self, deployment_id: str):
        """
        Unsubscribe from deployment events.

        Args:
            deployment_id: Deployment ID to unsubscribe from
        """
        message = {
            "action": "unsubscribe",
            "deployment_id": deployment_id
        }

        await self.ws.send(json.dumps(message))
        self.subscriptions.discard(deployment_id)

        logger.info(f"Unsubscribed from {deployment_id}")

    def on(self, message_type: str, handler: Callable):
        """
        Register message handler.

        Args:
            message_type: Message type (e.g., "deployment.status")
            handler: Async function to handle message
        """
        self.message_handlers[message_type] = handler

    async def _send_ping(self):
        """Send keep-alive ping"""
        while self.running:
            await asyncio.sleep(self.ping_interval)

            if self.ws:
                try:
                    await self.ws.send(json.dumps({"action": "ping"}))
                    logger.debug("Sent ping")
                except Exception as e:
                    logger.error(f"Error sending ping: {e}")

    async def _receive_messages(self):
        """Receive and handle messages"""
        while self.running:
            try:
                message_raw = await self.ws.recv()
                message = json.loads(message_raw)

                message_type = message.get('type')
                logger.debug(f"Received message: {message_type}")

                # Call registered handler
                if message_type in self.message_handlers:
                    handler = self.message_handlers[message_type]
                    await handler(message)

            except ConnectionClosed:
                logger.warning("Connection closed")
                if not self.auto_reconnect:
                    break
                # Auto-reconnect will handle this
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error receiving message: {e}", exc_info=True)

    async def run(self):
        """
        Run client (blocking).

        Starts message receiving and ping sending tasks.
        """
        await self.connect()

        # Start tasks
        tasks = [
            asyncio.create_task(self._receive_messages()),
            asyncio.create_task(self._send_ping()),
        ]

        # Wait for tasks
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Interrupted")
        finally:
            await self.disconnect()
```

---

#### Example Usage: `client/python/examples/monitor.py`

```python
"""
Example: Monitor deployment progress
"""

import asyncio
from cloud_ws_client import CloudWebSocketClient

# Cognito token (from authentication)
JWT_TOKEN = "eyJraWQ..."

# WebSocket endpoint
ENDPOINT = "wss://xxx.execute-api.us-east-1.amazonaws.com/production"


async def on_deployment_status(message):
    """Handle deployment status updates"""
    data = message['data']
    print(f"Deployment {message['deployment_id']}: {data['status']}")
    print(f"  Layer {data['current_layer']}/{data['total_layers']}")


async def on_stack_deployed(message):
    """Handle stack deployed events"""
    data = message['data']
    print(f"✓ Stack {data['stack_name']}-{data['environment']} deployed")
    print(f"  Duration: {data['duration_seconds']}s")
    print(f"  Resources: {data['resource_count']}")


async def on_stack_failed(message):
    """Handle stack failed events"""
    data = message['data']
    print(f"✗ Stack {data['stack_name']}-{data['environment']} FAILED")
    print(f"  Error: {data['error_message']}")


async def main():
    # Create client
    client = CloudWebSocketClient(
        endpoint=ENDPOINT,
        token=JWT_TOKEN,
        auto_reconnect=True,
    )

    # Register handlers
    client.on("deployment.status", on_deployment_status)
    client.on("stack.deployed", on_stack_deployed)
    client.on("stack.failed", on_stack_failed)

    # Connect
    await client.connect()

    # Subscribe to deployment
    await client.subscribe("D1BRV40")

    # Run (blocking)
    print("Monitoring deployment D1BRV40...")
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
```

---

### JavaScript WebSocket Client

#### File: `client/javascript/src/client.ts`

```typescript
/**
 * JavaScript/TypeScript WebSocket Client
 * Architecture 3.1
 */

export interface CloudWebSocketOptions {
  endpoint: string;
  token: string;
  autoReconnect?: boolean;
  pingInterval?: number;
}

export interface Message {
  type: string;
  deployment_id?: string;
  data: any;
  timestamp: string;
}

export type MessageHandler = (message: Message) => void;

export class CloudWebSocketClient {
  private endpoint: string;
  private token: string;
  private autoReconnect: boolean;
  private pingInterval: number;

  private ws: WebSocket | null = null;
  private subscriptions: Set<string> = new Set();
  private messageHandlers: Map<string, MessageHandler> = new Map();
  private pingTimer: number | null = null;
  private running: boolean = false;

  constructor(options: CloudWebSocketOptions) {
    this.endpoint = `${options.endpoint}?token=${options.token}`;
    this.token = options.token;
    this.autoReconnect = options.autoReconnect ?? true;
    this.pingInterval = options.pingInterval ?? 30000; // 30 seconds
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log(`Connecting to ${this.endpoint}`);

      this.ws = new WebSocket(this.endpoint);

      this.ws.onopen = () => {
        console.log('Connected');
        this.running = true;
        this.startPing();
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('Connection closed');
        this.running = false;
        this.stopPing();

        if (this.autoReconnect) {
          setTimeout(() => this.connect(), 5000);
        }
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };
    });
  }

  disconnect(): void {
    this.running = false;
    this.stopPing();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    console.log('Disconnected');
  }

  async subscribe(deploymentId: string): Promise<void> {
    const message = {
      action: 'subscribe',
      deployment_id: deploymentId,
    };

    this.send(message);
    this.subscriptions.add(deploymentId);

    console.log(`Subscribed to ${deploymentId}`);
  }

  async unsubscribe(deploymentId: string): Promise<void> {
    const message = {
      action: 'unsubscribe',
      deployment_id: deploymentId,
    };

    this.send(message);
    this.subscriptions.delete(deploymentId);

    console.log(`Unsubscribed from ${deploymentId}`);
  }

  on(messageType: string, handler: MessageHandler): void {
    this.messageHandlers.set(messageType, handler);
  }

  private send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  private handleMessage(data: string): void {
    try {
      const message: Message = JSON.parse(data);
      const messageType = message.type;

      console.log(`Received message: ${messageType}`);

      // Call registered handler
      const handler = this.messageHandlers.get(messageType);
      if (handler) {
        handler(message);
      }
    } catch (error) {
      console.error('Error handling message:', error);
    }
  }

  private startPing(): void {
    this.pingTimer = window.setInterval(() => {
      if (this.running) {
        this.send({ action: 'ping' });
      }
    }, this.pingInterval);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}
```

---

#### Example Usage: `client/javascript/examples/monitor.html`

```html
<!DOCTYPE html>
<html>
<head>
  <title>Cloud Platform - Real-time Monitor</title>
  <script type="module">
    import { CloudWebSocketClient } from './client.js';

    // Cognito token (from authentication)
    const JWT_TOKEN = 'eyJraWQ...';

    // WebSocket endpoint
    const ENDPOINT = 'wss://xxx.execute-api.us-east-1.amazonaws.com/production';

    // Create client
    const client = new CloudWebSocketClient({
      endpoint: ENDPOINT,
      token: JWT_TOKEN,
      autoReconnect: true,
    });

    // Register handlers
    client.on('deployment.status', (message) => {
      const data = message.data;
      console.log(`Deployment ${message.deployment_id}: ${data.status}`);
      console.log(`  Layer ${data.current_layer}/${data.total_layers}`);

      // Update UI
      document.getElementById('status').textContent = data.status;
      document.getElementById('progress').textContent =
        `${data.current_layer}/${data.total_layers}`;
    });

    client.on('stack.deployed', (message) => {
      const data = message.data;
      console.log(`✓ Stack ${data.stack_name}-${data.environment} deployed`);

      // Update UI
      const stacksList = document.getElementById('stacks-list');
      const li = document.createElement('li');
      li.textContent = `✓ ${data.stack_name}-${data.environment} (${data.duration_seconds}s)`;
      li.style.color = 'green';
      stacksList.appendChild(li);
    });

    client.on('stack.failed', (message) => {
      const data = message.data;
      console.log(`✗ Stack ${data.stack_name}-${data.environment} FAILED`);

      // Update UI
      const stacksList = document.getElementById('stacks-list');
      const li = document.createElement('li');
      li.textContent = `✗ ${data.stack_name}-${data.environment}: ${data.error_message}`;
      li.style.color = 'red';
      stacksList.appendChild(li);
    });

    // Connect and subscribe
    async function start() {
      await client.connect();
      await client.subscribe('D1BRV40');
      console.log('Monitoring deployment D1BRV40...');
    }

    start();
  </script>
</head>
<body>
  <h1>Deployment Monitor</h1>

  <div>
    <h2>Status: <span id="status">-</span></h2>
    <h3>Progress: <span id="progress">-</span></h3>
  </div>

  <h2>Stacks:</h2>
  <ul id="stacks-list"></ul>
</body>
</html>
```

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py                       # Shared fixtures
│
├── test_handlers/                    # Handler tests (12 tests)
│   ├── test_connect.py               # 4 tests
│   ├── test_disconnect.py            # 2 tests
│   ├── test_default.py               # 4 tests
│   └── test_authorize.py             # 2 tests
│
├── test_broadcast/                   # Broadcast tests (6 tests)
│   ├── test_broadcaster.py           # 4 tests
│   └── test_connection_manager.py    # 2 tests
│
├── test_protocol/                    # Protocol tests (4 tests)
│   ├── test_messages.py              # 2 tests
│   └── test_serializer.py            # 2 tests
│
├── test_client/                      # Client tests (8 tests)
│   ├── test_python_client.py         # 4 tests
│   └── test_reconnect.py             # 4 tests
│
└── test_integration/                 # Integration tests (6 tests)
    ├── test_full_flow.py             # 3 tests
    └── test_cognito_integration.py   # 3 tests

Total: ~36 tests
```

### Example Handler Test

```python
"""
Tests for Connect Handler
Architecture 3.1
"""

import pytest
import json
from unittest.mock import Mock, patch

from cloud_ws.handlers.connect import lambda_handler


def test_connect_with_valid_token(mock_dynamodb_table, mock_cognito_token):
    """Test connection with valid Cognito token"""
    event = {
        'requestContext': {
            'connectionId': 'test-connection-123'
        },
        'queryStringParameters': {
            'token': mock_cognito_token
        }
    }

    with patch('cloud_ws.handlers.authorize.verify_cognito_token') as mock_verify:
        mock_verify.return_value = {
            'user_id': 'user-123',
            'email': 'user@example.com'
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        assert 'Connected' in response['body']


def test_connect_without_token(mock_dynamodb_table):
    """Test connection without token"""
    event = {
        'requestContext': {
            'connectionId': 'test-connection-123'
        },
        'queryStringParameters': {}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 401
    assert 'Unauthorized' in response['body']


# ... 2 more connect handler tests
```

---

## Implementation Plan

### Phase 1: API Gateway Setup (Est: 4 hours)

**1.1 WebSocket API**
- Create Pulumi infrastructure code
- Configure routes ($connect, $disconnect, $default)
- Deploy API Gateway WebSocket API
- Test connection with wscat

**1.2 Connection Table**
- Create DynamoDB table for connections
- Configure TTL
- Test table operations

---

### Phase 2: Lambda Handlers (Est: 8 hours)

**2.1 Connect Handler** (2 hours)
- Implement Cognito JWT verification
- Store connection in DynamoDB
- Test authentication flow

**2.2 Disconnect Handler** (1 hour)
- Implement connection cleanup
- Test disconnect handling

**2.3 Default Handler** (3 hours)
- Implement subscribe/unsubscribe/ping actions
- Test message routing

**2.4 Broadcaster** (2 hours)
- Implement event broadcasting
- Query subscribed connections
- Send messages via API Gateway Management API

---

### Phase 3: Client Libraries (Est: 8 hours)

**3.1 Python Client** (4 hours)
- Implement WebSocket client
- Add auto-reconnect
- Add message handlers
- Test client

**3.2 JavaScript Client** (4 hours)
- Implement TypeScript WebSocket client
- Add auto-reconnect
- Add message handlers
- Create example dashboard

---

### Phase 4: Integration (Est: 4 hours)

**4.1 Event Publishing**
- Update orchestrator to publish events
- Update stack operations to publish events
- Test event flow

**4.2 AppSync Integration**
- Configure AppSync subscriptions
- Test subscription flow

---

### Phase 5: Testing (Est: 6 hours)

**5.1 Unit Tests** (3 hours)
- Handler tests (12 tests)
- Broadcast tests (6 tests)
- Protocol tests (4 tests)

**5.2 Client Tests** (2 hours)
- Python client tests (4 tests)
- Reconnect tests (4 tests)

**5.3 Integration Tests** (1 hour)
- Full flow tests (3 tests)
- Cognito integration tests (3 tests)

---

### Phase 6: Documentation (Est: 2 hours)

**6.1 WebSocket Documentation**
- Connection guide
- Message protocol reference
- Client library docs

**6.2 Examples**
- CLI monitoring example
- Web dashboard example
- Mobile app example

**Total Estimated Time: 32 hours**

---

## Success Criteria

### Functional Requirements

- [ ] **API Gateway WebSocket API** deployed and accessible
- [ ] **Cognito authentication** working on connect
- [ ] **Lambda handlers** for connect/disconnect/messages
- [ ] **Event broadcasting** to subscribed connections
- [ ] **Python client library** with auto-reconnect
- [ ] **JavaScript client library** with auto-reconnect
- [ ] **36+ tests passing** (handlers + broadcast + protocol + client)
- [ ] **AppSync subscriptions** working (from Session 5)

### Non-Functional Requirements

- [ ] **Connection latency** < 100ms for connect
- [ ] **Message latency** < 50ms for broadcast
- [ ] **Throughput** Support 10,000+ concurrent connections
- [ ] **Reliability** Auto-reconnect on connection loss
- [ ] **Security** All connections require Cognito auth
- [ ] **Scalability** Horizontal scaling with Lambda

### Code Quality

- [ ] **Type hints** on all Python functions
- [ ] **TypeScript types** on all JavaScript code
- [ ] **Docstrings** on all public functions
- [ ] **Tests** 90%+ code coverage
- [ ] **Error handling** All edge cases covered

---

**End of Session 6 Document**

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 6
**Document Version:** 1.0
**Last Updated:** 2025-10-23
