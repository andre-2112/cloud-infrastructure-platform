# Session 4: REST API Implementation

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 4
**Focus:** REST API with FastAPI + AWS Cognito Authentication
**Date:** 2025-10-23

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Session Context](#session-context)
3. [REST API Architecture](#rest-api-architecture)
4. [Core Business Logic Reuse](#core-business-logic-reuse)
5. [FastAPI Application Structure](#fastapi-application-structure)
6. [API Endpoints Specification](#api-endpoints-specification)
7. [AWS Cognito Authentication](#aws-cognito-authentication)
8. [Request/Response Models](#requestresponse-models)
9. [Error Handling](#error-handling)
10. [Testing Strategy](#testing-strategy)
11. [Implementation Plan](#implementation-plan)
12. [Success Criteria](#success-criteria)

---

## Executive Summary

### Purpose of Session 4

Session 4 implements a **production-ready REST API** that provides programmatic access to the Cloud Infrastructure Orchestration Platform. The API is built using **FastAPI** (Python 3.11+) and secured with **AWS Cognito** authentication.

### Key Objectives

1. **Implement REST API** - Create 15+ endpoints covering all CLI functionality
2. **Reuse CLI Business Logic** - Leverage 70-80% shared code from Session 3
3. **Implement Cognito Auth** - Secure all endpoints with JWT token validation
4. **OpenAPI Documentation** - Auto-generate API docs with FastAPI
5. **Testing** - 40+ endpoint tests, 10+ authentication tests
6. **Production Ready** - CORS, rate limiting, logging, monitoring

### What Gets Built

```
cloud/tools/api/
├── src/
│   └── cloud_api/
│       ├── main.py                    # FastAPI application
│       ├── routes/                    # API route handlers (15+ endpoints)
│       │   ├── __init__.py
│       │   ├── deployment.py          # Deployment endpoints
│       │   ├── stack.py               # Stack endpoints
│       │   ├── template.py            # Template endpoints
│       │   ├── validation.py          # Validation endpoints
│       │   └── monitoring.py          # Monitoring endpoints
│       ├── auth/                      # Authentication
│       │   ├── __init__.py
│       │   ├── cognito.py             # Cognito JWT validator
│       │   ├── dependencies.py        # FastAPI dependencies
│       │   └── permissions.py         # Permission checks
│       ├── models/                    # Pydantic models
│       │   ├── __init__.py
│       │   ├── requests.py            # Request models
│       │   ├── responses.py           # Response models
│       │   └── errors.py              # Error models
│       ├── middleware/                # Middleware
│       │   ├── __init__.py
│       │   ├── cors.py                # CORS configuration
│       │   ├── logging.py             # Request logging
│       │   └── rate_limit.py          # Rate limiting
│       ├── exceptions/                # Exception handlers
│       │   ├── __init__.py
│       │   └── handlers.py            # Custom exception handlers
│       └── utils/                     # Utilities
│           ├── __init__.py
│           ├── logger.py              # API logger
│           └── response.py            # Response helpers
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_routes/                   # Route tests
│   │   ├── test_deployment.py
│   │   ├── test_stack.py
│   │   ├── test_template.py
│   │   ├── test_validation.py
│   │   └── test_monitoring.py
│   ├── test_auth/                     # Auth tests
│   │   ├── test_cognito.py
│   │   └── test_permissions.py
│   └── test_integration/              # Integration tests
│       ├── test_full_deployment.py
│       └── test_auth_flow.py
├── requirements.txt                   # Dependencies
├── pyproject.toml                     # Project config
├── setup.py                           # Setup script
└── README.md                          # API documentation

SHARED CODE (from Session 3):
cloud/tools/shared/                    # Shared business logic
├── orchestrator/                      # 100% reused
├── templates/                         # 100% reused
├── deployment/                        # 100% reused
├── runtime/                           # 100% reused
├── pulumi/                            # 100% reused
├── validation/                        # 100% reused
└── utils/                             # 100% reused
```

### Code Sharing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REST API (FastAPI)                       │
│                                                             │
│  Routes Layer (20%)                                         │
│  ├── FastAPI route handlers                                │
│  ├── Request/response models (Pydantic)                    │
│  ├── Authentication middleware (Cognito)                   │
│  └── OpenAPI documentation                                 │
│                                                             │
│  ▼                                                          │
│                                                             │
│  Shared Business Logic Layer (80%)                         │
│  ├── Orchestrator (from Session 3)                         │
│  ├── Template Manager (from Session 3)                     │
│  ├── Deployment Manager (from Session 3)                   │
│  ├── Runtime Resolver (from Session 3)                     │
│  ├── Pulumi Wrapper (from Session 3)                       │
│  ├── Validators (from Session 3)                           │
│  └── Utilities (from Session 3)                            │
│                                                             │
│  ▼                                                          │
│                                                             │
│  Infrastructure Layer                                      │
│  ├── Pulumi CLI                                            │
│  ├── AWS SDK (boto3)                                       │
│  └── AWS Cognito                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Session Context

### What Was Built Before

**Session 1:** Complete documentation (16 documents)
**Session 2.1:** CLI framework (directory structure, basic commands)
**Session 3:** Complete CLI implementation (orchestrator, business logic, 25+ commands)

### What Session 4 Adds

1. **REST API Endpoints** - HTTP interface to all CLI functionality
2. **Authentication** - AWS Cognito JWT validation for all endpoints
3. **API Documentation** - Auto-generated OpenAPI/Swagger docs
4. **Production Features** - CORS, rate limiting, logging, error handling
5. **Testing** - Comprehensive test suite for API and auth

### Dependencies

- **Python 3.11+** (same as CLI)
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **python-jose** - JWT token validation
- **boto3** - AWS SDK for Cognito
- **pytest** - Testing framework
- **httpx** - Async HTTP client for tests

---

## REST API Architecture

### Design Principles

1. **Code Reuse** - Leverage 70-80% shared code from CLI
2. **Hexagonal Architecture** - Routes → Business Logic → Infrastructure
3. **OpenAPI Contract** - FastAPI generates OpenAPI schema automatically
4. **Stateless** - All endpoints are stateless, use JWT for authentication
5. **RESTful** - Follow REST conventions for resource naming and HTTP methods
6. **Async-First** - Use async/await for all I/O operations

### FastAPI Advantages

- **Automatic OpenAPI docs** - Swagger UI and ReDoc
- **Pydantic validation** - Request/response validation with type hints
- **Async support** - Native async/await support
- **Performance** - One of the fastest Python frameworks
- **Modern Python** - Uses type hints, Python 3.11+ features
- **Dependency injection** - Built-in DI for auth, database connections

### Authentication Flow

```
1. Client obtains JWT token from AWS Cognito
   └─> POST to Cognito User Pool with username/password
   └─> Receives ID token, access token, refresh token

2. Client includes token in Authorization header
   └─> Authorization: Bearer <id_token>

3. API validates token on every request
   └─> Decode JWT token
   └─> Verify signature with Cognito public keys
   └─> Check expiration
   └─> Extract user identity (sub, email, groups)

4. API executes business logic
   └─> Call shared orchestrator/template/deployment logic
   └─> Return response

5. Client receives JSON response
   └─> Success: 200/201 with data
   └─> Error: 400/401/403/500 with error details
```

---

## Core Business Logic Reuse

### Shared Modules (from Session 3)

All business logic from Session 3 CLI is **100% reused** in the REST API:

#### 1. Orchestrator (`cloud/tools/shared/orchestrator/`)

**Files:**
- `orchestrator.py` - Main orchestration engine
- `dependency_resolver.py` - Dependency graph resolution
- `layer_calculator.py` - Execution layer calculation
- `execution_engine.py` - Stack execution coordination

**Usage in API:**
```python
# In routes/deployment.py
from cloud_shared.orchestrator import Orchestrator

@router.post("/deployments/{deployment_id}/deploy")
async def deploy_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    orchestrator = Orchestrator(deployment_id)
    result = await orchestrator.deploy_all()
    return {"status": "success", "result": result}
```

#### 2. Template Manager (`cloud/tools/shared/templates/`)

**Files:**
- `template_manager.py` - Template loading and selection
- `manifest_generator.py` - Manifest generation from templates
- `template_renderer.py` - Jinja2 template rendering

**Usage in API:**
```python
# In routes/template.py
from cloud_shared.templates import TemplateManager

@router.post("/templates/{template_name}/generate")
async def generate_manifest(
    template_name: str,
    params: TemplateParams,
    current_user: User = Depends(get_current_user)
):
    template_mgr = TemplateManager()
    manifest = template_mgr.generate_manifest(template_name, params.dict())
    return manifest
```

#### 3. Deployment Manager (`cloud/tools/shared/deployment/`)

**Files:**
- `deployment_manager.py` - Deployment lifecycle management
- `state_manager.py` - Deployment state tracking
- `config_generator.py` - Pulumi config generation

**Usage in API:**
```python
# In routes/deployment.py
from cloud_shared.deployment import DeploymentManager

@router.get("/deployments")
async def list_deployments(
    current_user: User = Depends(get_current_user)
):
    deployment_mgr = DeploymentManager()
    deployments = deployment_mgr.list_deployments()
    return {"deployments": deployments}
```

#### 4. Runtime Resolver (`cloud/tools/shared/runtime/`)

**Files:**
- `placeholder_resolver.py` - Runtime placeholder resolution
- `stack_reference_resolver.py` - StackReference resolution
- `aws_query_resolver.py` - AWS API queries

**Usage in API:**
```python
# In routes/stack.py
from cloud_shared.runtime import PlaceholderResolver

@router.post("/stacks/{stack_name}/resolve")
async def resolve_placeholders(
    stack_name: str,
    manifest: dict,
    current_user: User = Depends(get_current_user)
):
    resolver = PlaceholderResolver(manifest)
    resolved = resolver.resolve_all(stack_name)
    return {"resolved": resolved}
```

#### 5. Pulumi Wrapper (`cloud/tools/shared/pulumi/`)

**Files:**
- `pulumi_wrapper.py` - Pulumi CLI wrapper
- `stack_operations.py` - Stack CRUD operations
- `state_queries.py` - State inspection

**Usage in API:**
```python
# In routes/stack.py
from cloud_shared.pulumi import PulumiWrapper

@router.get("/stacks/{stack_name}/outputs")
async def get_stack_outputs(
    stack_name: str,
    current_user: User = Depends(get_current_user)
):
    pulumi = PulumiWrapper()
    outputs = pulumi.get_stack_outputs(stack_name)
    return {"outputs": outputs}
```

#### 6. Validators (`cloud/tools/shared/validation/`)

**Files:**
- `manifest_validator.py` - Manifest validation
- `dependency_validator.py` - Dependency validation
- `aws_validator.py` - AWS resource validation
- `stack_validator.py` - Stack validation

**Usage in API:**
```python
# In routes/validation.py
from cloud_shared.validation import ManifestValidator

@router.post("/validate/manifest")
async def validate_manifest(
    manifest: dict,
    current_user: User = Depends(get_current_user)
):
    validator = ManifestValidator()
    result = validator.validate(manifest)
    return {"valid": result.is_valid, "errors": result.errors}
```

### API-Specific Code (20%)

Only the HTTP layer is API-specific:

1. **Route handlers** - FastAPI route decorators and functions
2. **Request/response models** - Pydantic models for HTTP
3. **Authentication** - Cognito JWT validation middleware
4. **Error handling** - HTTP exception handlers
5. **Middleware** - CORS, logging, rate limiting

---

## FastAPI Application Structure

### Main Application (`main.py`)

```python
"""
FastAPI Application - Cloud Infrastructure Orchestration Platform
Architecture 3.1
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cloud_api.routes import (
    deployment,
    stack,
    template,
    validation,
    monitoring,
)
from cloud_api.middleware.logging import LoggingMiddleware
from cloud_api.middleware.rate_limit import RateLimitMiddleware
from cloud_api.exceptions.handlers import (
    validation_exception_handler,
    general_exception_handler,
)
from cloud_api.utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cloud Infrastructure Orchestration Platform API",
    description="REST API for multi-stack AWS infrastructure deployment",
    version="0.7.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(deployment.router, prefix="/api/v1/deployments", tags=["deployments"])
app.include_router(stack.router, prefix="/api/v1/stacks", tags=["stacks"])
app.include_router(template.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(validation.router, prefix="/api/v1/validate", tags=["validation"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Cloud API v0.7.0")
    logger.info("Architecture 3.1")
    logger.info("API documentation: /api/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Cloud API")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Cloud Infrastructure Orchestration Platform API",
        "version": "0.7.0",
        "architecture": "3.1",
        "docs": "/api/docs",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.7.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "cloud_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
```

### Directory Structure Details

```
cloud/tools/api/
├── src/
│   └── cloud_api/                     # Main API package
│       │
│       ├── main.py                    # FastAPI app (above)
│       │
│       ├── routes/                    # Route handlers
│       │   ├── __init__.py
│       │   ├── deployment.py          # Deployment endpoints (8 routes)
│       │   ├── stack.py               # Stack endpoints (7 routes)
│       │   ├── template.py            # Template endpoints (4 routes)
│       │   ├── validation.py          # Validation endpoints (3 routes)
│       │   └── monitoring.py          # Monitoring endpoints (2 routes)
│       │
│       ├── auth/                      # Authentication
│       │   ├── __init__.py
│       │   ├── cognito.py             # JWT validation
│       │   ├── dependencies.py        # FastAPI dependencies
│       │   └── permissions.py         # Permission checks
│       │
│       ├── models/                    # Pydantic models
│       │   ├── __init__.py
│       │   ├── requests.py            # Request models (15+)
│       │   ├── responses.py           # Response models (15+)
│       │   └── errors.py              # Error models (5+)
│       │
│       ├── middleware/                # Middleware
│       │   ├── __init__.py
│       │   ├── cors.py                # CORS config
│       │   ├── logging.py             # Request logging
│       │   └── rate_limit.py          # Rate limiting
│       │
│       ├── exceptions/                # Exception handlers
│       │   ├── __init__.py
│       │   └── handlers.py            # Custom handlers
│       │
│       └── utils/                     # Utilities
│           ├── __init__.py
│           ├── logger.py              # Logger config
│           └── response.py            # Response helpers
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   │
│   ├── test_routes/                   # Route tests (24+ tests)
│   │   ├── __init__.py
│   │   ├── test_deployment.py         # 8 tests
│   │   ├── test_stack.py              # 7 tests
│   │   ├── test_template.py           # 4 tests
│   │   ├── test_validation.py         # 3 tests
│   │   └── test_monitoring.py         # 2 tests
│   │
│   ├── test_auth/                     # Auth tests (10+ tests)
│   │   ├── __init__.py
│   │   ├── test_cognito.py            # 6 tests
│   │   └── test_permissions.py        # 4 tests
│   │
│   └── test_integration/              # Integration tests (6+ tests)
│       ├── __init__.py
│       ├── test_full_deployment.py    # 3 tests
│       └── test_auth_flow.py          # 3 tests
│
├── requirements.txt                   # Dependencies
├── pyproject.toml                     # Project config
├── setup.py                           # Setup script
└── README.md                          # API documentation
```

---

## API Endpoints Specification

### Overview

**Total Endpoints:** 24 (grouped into 5 categories)

1. **Deployment Endpoints** (8) - Manage deployments
2. **Stack Endpoints** (7) - Manage individual stacks
3. **Template Endpoints** (4) - Manage templates
4. **Validation Endpoints** (3) - Validate configurations
5. **Monitoring Endpoints** (2) - Monitor operations

All endpoints require authentication via AWS Cognito JWT token in Authorization header.

---

### 1. Deployment Endpoints (`routes/deployment.py`)

#### 1.1 Initialize New Deployment

**Endpoint:** `POST /api/v1/deployments/init`
**Description:** Initialize a new deployment from a template
**Auth:** Required (Cognito JWT)

**Request Body:**
```json
{
  "organization": "MyOrg",
  "project": "my-project",
  "domain": "myproject.example.com",
  "template": "default",
  "environments": {
    "dev": {
      "enabled": true,
      "region": "us-east-1",
      "account_id": "111111111111"
    },
    "stage": {
      "enabled": true,
      "region": "us-east-1",
      "account_id": "222222222222"
    }
  }
}
```

**Response (201):**
```json
{
  "deployment_id": "D1BRV40",
  "manifest_path": "/workspace/cloud/deployments/D1BRV40/manifest.yaml",
  "status": "initialized",
  "created_at": "2025-10-23T10:00:00Z"
}
```

**Implementation:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from cloud_api.auth.dependencies import get_current_user
from cloud_api.models.requests import InitDeploymentRequest
from cloud_api.models.responses import InitDeploymentResponse
from cloud_shared.templates import TemplateManager
from cloud_shared.deployment import DeploymentManager
from cloud_shared.utils.deployment_id import generate_deployment_id

router = APIRouter()

@router.post("/init", response_model=InitDeploymentResponse, status_code=status.HTTP_201_CREATED)
async def initialize_deployment(
    request: InitDeploymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize a new deployment from a template.

    Creates a deployment directory, generates manifest, and initializes state.
    """
    # Generate unique deployment ID
    deployment_id = generate_deployment_id()

    # Generate manifest from template
    template_mgr = TemplateManager()
    manifest = template_mgr.generate_manifest(
        template_name=request.template,
        params={
            "organization": request.organization,
            "project": request.project,
            "domain": request.domain,
            "environments": request.environments,
            "deployment_id": deployment_id,
        }
    )

    # Initialize deployment
    deployment_mgr = DeploymentManager()
    deployment = deployment_mgr.initialize_deployment(
        deployment_id=deployment_id,
        manifest=manifest
    )

    return InitDeploymentResponse(
        deployment_id=deployment_id,
        manifest_path=deployment.manifest_path,
        status="initialized",
        created_at=deployment.created_at
    )
```

---

#### 1.2 Deploy All Stacks

**Endpoint:** `POST /api/v1/deployments/{deployment_id}/deploy`
**Description:** Deploy all stacks in a deployment
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `environment` (optional): Specific environment (dev/stage/prod)
- `dry_run` (optional, default: false): Perform dry run only

**Response (200):**
```json
{
  "deployment_id": "D1BRV40",
  "status": "deploying",
  "layers": [
    {
      "layer": 1,
      "stacks": ["network", "security"],
      "status": "in_progress"
    },
    {
      "layer": 2,
      "stacks": ["dns", "secrets"],
      "status": "pending"
    }
  ],
  "started_at": "2025-10-23T10:05:00Z"
}
```

**Implementation:**
```python
@router.post("/{deployment_id}/deploy", response_model=DeploymentStatusResponse)
async def deploy_deployment(
    deployment_id: str,
    environment: Optional[str] = None,
    dry_run: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Deploy all stacks in a deployment.

    Executes deployment in layers based on dependencies.
    Returns immediately with deployment status.
    """
    # Load deployment manifest
    deployment_mgr = DeploymentManager()
    manifest = deployment_mgr.load_manifest(deployment_id)

    # Create orchestrator
    from cloud_shared.orchestrator import Orchestrator
    orchestrator = Orchestrator(manifest)

    # Start deployment (async)
    if dry_run:
        result = await orchestrator.preview_all(environment)
    else:
        result = await orchestrator.deploy_all(environment)

    return DeploymentStatusResponse(
        deployment_id=deployment_id,
        status="deploying" if not dry_run else "preview",
        layers=result.layers,
        started_at=result.started_at
    )
```

---

#### 1.3 Get Deployment Status

**Endpoint:** `GET /api/v1/deployments/{deployment_id}/status`
**Description:** Get current status of a deployment
**Auth:** Required (Cognito JWT)

**Response (200):**
```json
{
  "deployment_id": "D1BRV40",
  "status": "deploying",
  "current_layer": 2,
  "total_layers": 4,
  "stacks": {
    "network-dev": {"status": "deployed", "outputs": {...}},
    "security-dev": {"status": "deployed", "outputs": {...}},
    "dns-dev": {"status": "deploying", "progress": 45},
    "secrets-dev": {"status": "pending"}
  },
  "started_at": "2025-10-23T10:05:00Z",
  "updated_at": "2025-10-23T10:10:00Z"
}
```

---

#### 1.4 List All Deployments

**Endpoint:** `GET /api/v1/deployments`
**Description:** List all deployments
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `status` (optional): Filter by status (initialized/deploying/deployed/failed)
- `limit` (optional, default: 50): Max results
- `offset` (optional, default: 0): Pagination offset

**Response (200):**
```json
{
  "deployments": [
    {
      "deployment_id": "D1BRV40",
      "organization": "MyOrg",
      "project": "my-project",
      "status": "deployed",
      "created_at": "2025-10-23T10:00:00Z",
      "updated_at": "2025-10-23T10:15:00Z"
    },
    {
      "deployment_id": "D2XYZ90",
      "organization": "MyOrg",
      "project": "another-project",
      "status": "deploying",
      "created_at": "2025-10-23T09:00:00Z",
      "updated_at": "2025-10-23T10:05:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

---

#### 1.5 Get Deployment Manifest

**Endpoint:** `GET /api/v1/deployments/{deployment_id}/manifest`
**Description:** Get deployment manifest
**Auth:** Required (Cognito JWT)

**Response (200):**
```json
{
  "version": "3.1",
  "deployment_id": "D1BRV40",
  "organization": "MyOrg",
  "project": "my-project",
  "domain": "myproject.example.com",
  "template": "default",
  "environments": {...},
  "stacks": {...}
}
```

---

#### 1.6 Update Deployment Manifest

**Endpoint:** `PUT /api/v1/deployments/{deployment_id}/manifest`
**Description:** Update deployment manifest
**Auth:** Required (Cognito JWT)

**Request Body:** Full manifest JSON

**Response (200):**
```json
{
  "deployment_id": "D1BRV40",
  "manifest_path": "/workspace/cloud/deployments/D1BRV40/manifest.yaml",
  "updated_at": "2025-10-23T10:20:00Z"
}
```

---

#### 1.7 Destroy Deployment

**Endpoint:** `DELETE /api/v1/deployments/{deployment_id}`
**Description:** Destroy all stacks in a deployment
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `environment` (optional): Specific environment to destroy

**Response (200):**
```json
{
  "deployment_id": "D1BRV40",
  "status": "destroying",
  "started_at": "2025-10-23T10:25:00Z"
}
```

---

#### 1.8 Get Deployment Outputs

**Endpoint:** `GET /api/v1/deployments/{deployment_id}/outputs`
**Description:** Get all stack outputs for a deployment
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `environment` (required): Environment (dev/stage/prod)

**Response (200):**
```json
{
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "outputs": {
    "network": {
      "vpc_id": "vpc-12345",
      "public_subnet_ids": ["subnet-11111", "subnet-22222"],
      "private_subnet_ids": ["subnet-33333", "subnet-44444"]
    },
    "security": {
      "default_security_group_id": "sg-12345"
    }
  }
}
```

---

### 2. Stack Endpoints (`routes/stack.py`)

#### 2.1 Deploy Single Stack

**Endpoint:** `POST /api/v1/stacks/{stack_name}/deploy`
**Description:** Deploy a single stack
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment (dev/stage/prod)
- `dry_run` (optional, default: false): Perform preview only

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "status": "deploying",
  "started_at": "2025-10-23T10:30:00Z"
}
```

---

#### 2.2 Get Stack Status

**Endpoint:** `GET /api/v1/stacks/{stack_name}/status`
**Description:** Get status of a single stack
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "status": "deployed",
  "resources": 15,
  "outputs": {...},
  "updated_at": "2025-10-23T10:35:00Z"
}
```

---

#### 2.3 Get Stack Outputs

**Endpoint:** `GET /api/v1/stacks/{stack_name}/outputs`
**Description:** Get outputs of a single stack
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "outputs": {
    "vpc_id": "vpc-12345",
    "public_subnet_ids": ["subnet-11111", "subnet-22222"],
    "private_subnet_ids": ["subnet-33333", "subnet-44444"]
  }
}
```

---

#### 2.4 Destroy Single Stack

**Endpoint:** `DELETE /api/v1/stacks/{stack_name}`
**Description:** Destroy a single stack
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "status": "destroying",
  "started_at": "2025-10-23T10:40:00Z"
}
```

---

#### 2.5 Refresh Stack State

**Endpoint:** `POST /api/v1/stacks/{stack_name}/refresh`
**Description:** Refresh stack state from cloud provider
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "status": "refreshed",
  "changes_detected": false,
  "refreshed_at": "2025-10-23T10:45:00Z"
}
```

---

#### 2.6 Get Stack Resources

**Endpoint:** `GET /api/v1/stacks/{stack_name}/resources`
**Description:** Get list of resources in a stack
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "resources": [
    {
      "type": "aws:ec2/vpc:Vpc",
      "name": "main-vpc",
      "urn": "urn:pulumi:...",
      "status": "up-to-date"
    },
    {
      "type": "aws:ec2/subnet:Subnet",
      "name": "public-subnet-1",
      "urn": "urn:pulumi:...",
      "status": "up-to-date"
    }
  ],
  "total": 15
}
```

---

#### 2.7 Export Stack

**Endpoint:** `GET /api/v1/stacks/{stack_name}/export`
**Description:** Export stack state
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `deployment_id` (required): Deployment ID
- `environment` (required): Environment

**Response (200):**
```json
{
  "stack_name": "network",
  "deployment_id": "D1BRV40",
  "environment": "dev",
  "state": {
    "version": 3,
    "deployment": {...},
    "resources": [...]
  },
  "exported_at": "2025-10-23T10:50:00Z"
}
```

---

### 3. Template Endpoints (`routes/template.py`)

#### 3.1 List Templates

**Endpoint:** `GET /api/v1/templates`
**Description:** List available templates
**Auth:** Required (Cognito JWT)

**Response (200):**
```json
{
  "templates": [
    {
      "name": "default",
      "description": "Default multi-stack template with all 16 stacks",
      "version": "3.1",
      "stacks": 16
    },
    {
      "name": "minimal",
      "description": "Minimal template with essential stacks only",
      "version": "3.1",
      "stacks": 8
    }
  ],
  "total": 2
}
```

---

#### 3.2 Get Template Details

**Endpoint:** `GET /api/v1/templates/{template_name}`
**Description:** Get details of a specific template
**Auth:** Required (Cognito JWT)

**Response (200):**
```json
{
  "name": "default",
  "description": "Default multi-stack template",
  "version": "3.1",
  "stacks": [
    "network",
    "security",
    "dns",
    "secrets",
    "authentication",
    "storage",
    "database-rds",
    "containers-images",
    "containers-apps",
    "services-ecr",
    "services-ecs",
    "services-eks",
    "services-api",
    "compute-ec2",
    "compute-lambda",
    "monitoring"
  ],
  "parameters": {
    "organization": {
      "type": "string",
      "required": true,
      "description": "Organization name"
    },
    "project": {
      "type": "string",
      "required": true,
      "description": "Project name"
    }
  }
}
```

---

#### 3.3 Generate Manifest from Template

**Endpoint:** `POST /api/v1/templates/{template_name}/generate`
**Description:** Generate deployment manifest from template
**Auth:** Required (Cognito JWT)

**Request Body:**
```json
{
  "organization": "MyOrg",
  "project": "my-project",
  "domain": "myproject.example.com",
  "environments": {
    "dev": {
      "enabled": true,
      "region": "us-east-1",
      "account_id": "111111111111"
    }
  }
}
```

**Response (200):**
```json
{
  "manifest": {
    "version": "3.1",
    "deployment_id": "D1BRV40",
    "organization": "MyOrg",
    "project": "my-project",
    "domain": "myproject.example.com",
    "environments": {...},
    "stacks": {...}
  }
}
```

---

#### 3.4 Validate Template

**Endpoint:** `POST /api/v1/templates/{template_name}/validate`
**Description:** Validate a template
**Auth:** Required (Cognito JWT)

**Response (200):**
```json
{
  "template_name": "default",
  "valid": true,
  "errors": [],
  "warnings": []
}
```

---

### 4. Validation Endpoints (`routes/validation.py`)

#### 4.1 Validate Manifest

**Endpoint:** `POST /api/v1/validate/manifest`
**Description:** Validate a deployment manifest
**Auth:** Required (Cognito JWT)

**Request Body:** Full manifest JSON

**Response (200):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Stack 'compute-lambda' has no configuration overrides"
  ]
}
```

---

#### 4.2 Validate Dependencies

**Endpoint:** `POST /api/v1/validate/dependencies`
**Description:** Validate stack dependencies
**Auth:** Required (Cognito JWT)

**Request Body:**
```json
{
  "deployment_id": "D1BRV40",
  "stacks": {
    "network": {...},
    "database-rds": {
      "dependencies": ["network", "security"]
    }
  }
}
```

**Response (200):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "dependency_graph": {
    "nodes": ["network", "security", "database-rds"],
    "edges": [
      {"from": "database-rds", "to": "network"},
      {"from": "database-rds", "to": "security"}
    ]
  }
}
```

---

#### 4.3 Validate AWS Resources

**Endpoint:** `POST /api/v1/validate/aws`
**Description:** Validate AWS resources and permissions
**Auth:** Required (Cognito JWT)

**Request Body:**
```json
{
  "region": "us-east-1",
  "account_id": "111111111111",
  "checks": [
    "credentials",
    "permissions",
    "quotas"
  ]
}
```

**Response (200):**
```json
{
  "valid": true,
  "errors": [],
  "checks": {
    "credentials": {
      "valid": true,
      "account_id": "111111111111"
    },
    "permissions": {
      "valid": true,
      "missing_permissions": []
    },
    "quotas": {
      "valid": true,
      "warnings": [
        "VPC limit: 4/5 used"
      ]
    }
  }
}
```

---

### 5. Monitoring Endpoints (`routes/monitoring.py`)

#### 5.1 Get Deployment Logs

**Endpoint:** `GET /api/v1/monitoring/deployments/{deployment_id}/logs`
**Description:** Get deployment logs
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `environment` (optional): Filter by environment
- `stack_name` (optional): Filter by stack
- `level` (optional): Log level (debug/info/warn/error)
- `limit` (optional, default: 100): Max log entries
- `since` (optional): ISO 8601 timestamp

**Response (200):**
```json
{
  "deployment_id": "D1BRV40",
  "logs": [
    {
      "timestamp": "2025-10-23T10:05:00Z",
      "level": "info",
      "stack": "network",
      "environment": "dev",
      "message": "Starting deployment of network-dev"
    },
    {
      "timestamp": "2025-10-23T10:06:30Z",
      "level": "info",
      "stack": "network",
      "environment": "dev",
      "message": "Created VPC: vpc-12345"
    }
  ],
  "total": 2
}
```

---

#### 5.2 Get System Metrics

**Endpoint:** `GET /api/v1/monitoring/metrics`
**Description:** Get system metrics
**Auth:** Required (Cognito JWT)

**Query Parameters:**
- `period` (optional, default: 1h): Time period (1h/24h/7d/30d)

**Response (200):**
```json
{
  "period": "1h",
  "metrics": {
    "deployments_started": 5,
    "deployments_completed": 3,
    "deployments_failed": 1,
    "stacks_deployed": 48,
    "average_deployment_time_seconds": 450,
    "api_requests": 1250,
    "api_errors": 12
  },
  "timestamp": "2025-10-23T11:00:00Z"
}
```

---

## AWS Cognito Authentication

### Overview

All API endpoints are secured with **AWS Cognito** using JWT (JSON Web Token) authentication.

### Authentication Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                              │
│  (Web App, Mobile App, CLI, curl, etc.)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 1. Authenticate
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Cognito User Pool                    │
│  - User registration and login                              │
│  - JWT token generation                                     │
│  - User groups and permissions                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 2. Return JWT tokens
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                         Client                              │
│  Stores: ID token, Access token, Refresh token              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 3. API request with token
                           │    Authorization: Bearer <id_token>
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Application                    │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │         Authentication Middleware                   │   │
│  │  1. Extract token from Authorization header        │   │
│  │  2. Decode JWT token                               │   │
│  │  3. Verify signature with Cognito public keys      │   │
│  │  4. Check expiration                               │   │
│  │  5. Extract user info (sub, email, groups)         │   │
│  │  6. Inject user into request context               │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │         Route Handler                               │   │
│  │  - Access authenticated user via dependency        │   │
│  │  - Check permissions                               │   │
│  │  - Execute business logic                          │   │
│  │  - Return response                                 │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Cognito Configuration

**User Pool Setup:**

```yaml
# Cognito User Pool Configuration
UserPool:
  Name: cloud-platform-users
  Region: us-east-1

  # Sign-in options
  UsernameAttributes:
    - email

  # Password policy
  PasswordPolicy:
    MinimumLength: 12
    RequireUppercase: true
    RequireLowercase: true
    RequireNumbers: true
    RequireSymbols: true

  # MFA
  MfaConfiguration: OPTIONAL
  EnabledMfas:
    - SOFTWARE_TOKEN_MFA

  # User groups
  Groups:
    - Name: Administrators
      Description: Full access to all resources
      Precedence: 1
    - Name: Developers
      Description: Deploy and manage deployments
      Precedence: 2
    - Name: ReadOnly
      Description: Read-only access
      Precedence: 3

  # App client
  AppClient:
    Name: cloud-platform-api
    GenerateSecret: false  # For JavaScript/mobile apps
    ExplicitAuthFlows:
      - ALLOW_USER_PASSWORD_AUTH
      - ALLOW_REFRESH_TOKEN_AUTH
    TokenValidityUnits:
      IdToken: hours
      AccessToken: hours
      RefreshToken: days
    IdTokenValidity: 1
    AccessTokenValidity: 1
    RefreshTokenValidity: 30
```

### Authentication Implementation

#### File: `auth/cognito.py`

```python
"""
AWS Cognito JWT Authentication
Architecture 3.1
"""

import os
from typing import Dict, Optional
from jose import JWTError, jwt
from jose.backends import RSAKey
import requests
from functools import lru_cache

from cloud_api.utils.logger import get_logger

logger = get_logger(__name__)

# Cognito configuration (from environment variables)
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
COGNITO_APP_CLIENT_ID = os.environ["COGNITO_APP_CLIENT_ID"]

# Cognito URLs
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def get_cognito_public_keys() -> Dict[str, RSAKey]:
    """
    Fetch and cache Cognito public keys for JWT verification.

    Keys are cached to avoid repeated HTTP requests.
    """
    try:
        response = requests.get(COGNITO_JWKS_URL, timeout=10)
        response.raise_for_status()
        jwks = response.json()

        # Convert JWKS to dict of kid -> RSAKey
        keys = {}
        for key_data in jwks["keys"]:
            kid = key_data["kid"]
            keys[kid] = key_data

        logger.info(f"Loaded {len(keys)} Cognito public keys")
        return keys

    except Exception as e:
        logger.error(f"Failed to load Cognito public keys: {e}")
        raise


def decode_jwt_token(token: str) -> Dict:
    """
    Decode and verify a JWT token from Cognito.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or signature verification fails
    """
    try:
        # Decode header to get key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]

        # Get public key for this kid
        public_keys = get_cognito_public_keys()
        if kid not in public_keys:
            raise JWTError(f"Public key not found for kid: {kid}")

        public_key = public_keys[kid]

        # Decode and verify token
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

        logger.debug(f"Successfully decoded JWT for user: {payload.get('sub')}")
        return payload

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT: {e}")
        raise JWTError(f"Token decoding failed: {e}")


def extract_user_info(token_payload: Dict) -> Dict:
    """
    Extract user information from decoded JWT payload.

    Args:
        token_payload: Decoded JWT payload

    Returns:
        User info dictionary with standardized fields
    """
    return {
        "user_id": token_payload.get("sub"),
        "username": token_payload.get("cognito:username"),
        "email": token_payload.get("email"),
        "email_verified": token_payload.get("email_verified", False),
        "groups": token_payload.get("cognito:groups", []),
        "token_use": token_payload.get("token_use"),
        "auth_time": token_payload.get("auth_time"),
        "exp": token_payload.get("exp"),
    }


def verify_token(token: str) -> Dict:
    """
    Verify JWT token and return user info.

    This is the main entry point for authentication.

    Args:
        token: JWT token string

    Returns:
        User info dictionary

    Raises:
        JWTError: If token is invalid
    """
    payload = decode_jwt_token(token)
    user_info = extract_user_info(payload)
    return user_info
```

---

#### File: `auth/dependencies.py`

```python
"""
FastAPI Authentication Dependencies
Architecture 3.1
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from cloud_api.auth.cognito import verify_token
from cloud_api.utils.logger import get_logger

logger = get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to get current authenticated user.

    Extracts JWT token from Authorization header, verifies it,
    and returns user information.

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            return {"user": current_user}

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        User info dictionary

    Raises:
        HTTPException(401): If token is missing or invalid
    """
    token = credentials.credentials

    try:
        user_info = verify_token(token)
        logger.debug(f"Authenticated user: {user_info['email']}")
        return user_info

    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    FastAPI dependency to get current user (optional).

    Similar to get_current_user but returns None if no token provided.
    Useful for endpoints that work with or without authentication.

    Args:
        credentials: HTTP Authorization credentials (optional)

    Returns:
        User info dictionary or None
    """
    if credentials is None:
        return None

    try:
        return verify_token(credentials.credentials)
    except Exception:
        return None
```

---

#### File: `auth/permissions.py`

```python
"""
Permission Checks
Architecture 3.1
"""

from typing import List
from fastapi import HTTPException, status

from cloud_api.utils.logger import get_logger

logger = get_logger(__name__)


# User group hierarchy (lower number = higher privilege)
GROUP_HIERARCHY = {
    "Administrators": 1,
    "Developers": 2,
    "ReadOnly": 3,
}


def require_groups(allowed_groups: List[str]):
    """
    FastAPI dependency factory to require user to be in specific groups.

    Usage:
        @router.post("/deployments/init")
        async def init_deployment(
            current_user: dict = Depends(get_current_user),
            _: None = Depends(require_groups(["Administrators", "Developers"]))
        ):
            # Only Administrators and Developers can access this
            ...

    Args:
        allowed_groups: List of allowed group names

    Returns:
        Dependency function
    """
    def check_groups(current_user: dict) -> None:
        user_groups = current_user.get("groups", [])

        # Check if user is in any of the allowed groups
        if not any(group in allowed_groups for group in user_groups):
            logger.warning(
                f"User {current_user['email']} denied access. "
                f"Required groups: {allowed_groups}, User groups: {user_groups}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required groups: {', '.join(allowed_groups)}"
            )

    return check_groups


def require_admin(current_user: dict) -> None:
    """
    Require user to be in Administrators group.

    Usage:
        @router.delete("/deployments/{deployment_id}")
        async def delete_deployment(
            deployment_id: str,
            current_user: dict = Depends(get_current_user),
            _: None = Depends(require_admin)
        ):
            # Only Administrators can delete
            ...
    """
    if "Administrators" not in current_user.get("groups", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )


def can_write_deployment(current_user: dict) -> bool:
    """
    Check if user can write (create/update/deploy) deployments.

    Returns:
        True if user has write permissions
    """
    user_groups = current_user.get("groups", [])
    return any(group in ["Administrators", "Developers"] for group in user_groups)


def can_delete_deployment(current_user: dict) -> bool:
    """
    Check if user can delete deployments.

    Returns:
        True if user has delete permissions
    """
    return "Administrators" in current_user.get("groups", [])


def get_user_max_privilege(current_user: dict) -> int:
    """
    Get user's maximum privilege level.

    Lower number = higher privilege.

    Returns:
        Privilege level (1-3) or 999 if no groups
    """
    user_groups = current_user.get("groups", [])

    if not user_groups:
        return 999  # No privileges

    # Return lowest number (highest privilege) from user's groups
    privileges = [GROUP_HIERARCHY.get(group, 999) for group in user_groups]
    return min(privileges)
```

---

### Client Authentication Example

#### Using curl

```bash
# 1. Authenticate with Cognito (using AWS CLI)
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <APP_CLIENT_ID> \
  --auth-parameters USERNAME=user@example.com,PASSWORD=SecurePass123! \
  --region us-east-1

# Response contains:
# - IdToken (use this for API authentication)
# - AccessToken
# - RefreshToken

# 2. Store ID token
export ID_TOKEN="eyJraWQ..."

# 3. Make API request
curl -X POST https://api.example.com/api/v1/deployments/init \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization": "MyOrg",
    "project": "my-project",
    "domain": "myproject.example.com",
    "template": "default",
    "environments": {...}
  }'
```

#### Using Python requests

```python
import requests
import boto3

# 1. Authenticate with Cognito
client = boto3.client('cognito-idp', region_name='us-east-1')

response = client.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'user@example.com',
        'PASSWORD': 'SecurePass123!'
    },
    ClientId='<APP_CLIENT_ID>'
)

id_token = response['AuthenticationResult']['IdToken']

# 2. Make API request
headers = {
    'Authorization': f'Bearer {id_token}',
    'Content-Type': 'application/json'
}

response = requests.post(
    'https://api.example.com/api/v1/deployments/init',
    headers=headers,
    json={
        'organization': 'MyOrg',
        'project': 'my-project',
        'domain': 'myproject.example.com',
        'template': 'default',
        'environments': {...}
    }
)

print(response.json())
```

---

## Request/Response Models

### Pydantic Models Overview

All API requests and responses use **Pydantic models** for:
- Type validation
- Data serialization/deserialization
- Automatic OpenAPI schema generation
- Clear API contracts

### File: `models/requests.py`

```python
"""
Request Models (Pydantic)
Architecture 3.1
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class EnvironmentConfig(BaseModel):
    """Configuration for a single environment"""
    enabled: bool = Field(True, description="Whether this environment is enabled")
    region: str = Field(..., description="AWS region (e.g., us-east-1)")
    account_id: str = Field(..., description="AWS account ID (12 digits)")

    @validator('account_id')
    def validate_account_id(cls, v):
        if not v.isdigit() or len(v) != 12:
            raise ValueError('AWS account ID must be 12 digits')
        return v


class InitDeploymentRequest(BaseModel):
    """Request body for initializing a deployment"""
    organization: str = Field(..., description="Organization name", min_length=1, max_length=50)
    project: str = Field(..., description="Project name", min_length=1, max_length=50)
    domain: str = Field(..., description="Base domain (e.g., example.com)")
    template: str = Field("default", description="Template name")
    environments: Dict[str, EnvironmentConfig] = Field(..., description="Environment configurations")

    class Config:
        schema_extra = {
            "example": {
                "organization": "MyOrg",
                "project": "my-project",
                "domain": "myproject.example.com",
                "template": "default",
                "environments": {
                    "dev": {
                        "enabled": True,
                        "region": "us-east-1",
                        "account_id": "111111111111"
                    }
                }
            }
        }


class DeployStackRequest(BaseModel):
    """Request body for deploying a stack"""
    deployment_id: str = Field(..., description="Deployment ID", pattern=r'^D[A-Z0-9]{6}$')
    environment: str = Field(..., description="Environment (dev/stage/prod)")
    dry_run: bool = Field(False, description="Perform dry run (preview) only")

    class Config:
        schema_extra = {
            "example": {
                "deployment_id": "D1BRV40",
                "environment": "dev",
                "dry_run": False
            }
        }


class TemplateParams(BaseModel):
    """Parameters for template generation"""
    organization: str
    project: str
    domain: str
    environments: Dict[str, EnvironmentConfig]


class ValidateManifestRequest(BaseModel):
    """Request body for manifest validation"""
    manifest: Dict = Field(..., description="Deployment manifest")

    class Config:
        schema_extra = {
            "example": {
                "manifest": {
                    "version": "3.1",
                    "deployment_id": "D1BRV40",
                    "organization": "MyOrg",
                    "project": "my-project",
                    "environments": {...},
                    "stacks": {...}
                }
            }
        }


# ... additional request models
```

---

### File: `models/responses.py`

```python
"""
Response Models (Pydantic)
Architecture 3.1
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InitDeploymentResponse(BaseModel):
    """Response for deployment initialization"""
    deployment_id: str = Field(..., description="Generated deployment ID")
    manifest_path: str = Field(..., description="Path to manifest file")
    status: str = Field(..., description="Deployment status")
    created_at: datetime = Field(..., description="Creation timestamp")


class StackStatus(BaseModel):
    """Status of a single stack"""
    stack_name: str
    status: str  # pending/deploying/deployed/failed
    progress: Optional[int] = None  # 0-100
    outputs: Optional[Dict] = None
    error: Optional[str] = None


class LayerStatus(BaseModel):
    """Status of a deployment layer"""
    layer: int
    stacks: List[str]
    status: str  # pending/in_progress/completed/failed


class DeploymentStatusResponse(BaseModel):
    """Response for deployment status"""
    deployment_id: str
    status: str
    layers: List[LayerStatus]
    started_at: datetime
    updated_at: Optional[datetime] = None


class DeploymentListItem(BaseModel):
    """Single deployment in list response"""
    deployment_id: str
    organization: str
    project: str
    status: str
    created_at: datetime
    updated_at: datetime


class DeploymentListResponse(BaseModel):
    """Response for listing deployments"""
    deployments: List[DeploymentListItem]
    total: int
    limit: int
    offset: int


class StackOutputsResponse(BaseModel):
    """Response for stack outputs"""
    stack_name: str
    deployment_id: str
    environment: str
    outputs: Dict


class ValidationResult(BaseModel):
    """Result of validation"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime


# ... additional response models
```

---

### File: `models/errors.py`

```python
"""
Error Models
Architecture 3.1
"""

from typing import Optional
from pydantic import BaseModel


class APIError(Exception):
    """Base API exception"""
    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class DeploymentNotFoundError(APIError):
    """Deployment not found"""
    def __init__(self, deployment_id: str):
        super().__init__(
            message=f"Deployment not found: {deployment_id}",
            status_code=404,
            error_code="DEPLOYMENT_NOT_FOUND"
        )


class StackNotFoundError(APIError):
    """Stack not found"""
    def __init__(self, stack_name: str):
        super().__init__(
            message=f"Stack not found: {stack_name}",
            status_code=404,
            error_code="STACK_NOT_FOUND"
        )


class TemplateNotFoundError(APIError):
    """Template not found"""
    def __init__(self, template_name: str):
        super().__init__(
            message=f"Template not found: {template_name}",
            status_code=404,
            error_code="TEMPLATE_NOT_FOUND"
        )


class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR"
        )


class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class PermissionError(APIError):
    """Permission denied error"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PERMISSION_DENIED"
        )
```

---

## Error Handling

### Exception Handlers (`exceptions/handlers.py`)

```python
"""
Custom Exception Handlers
Architecture 3.1
"""

from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from cloud_api.models.errors import APIError
from cloud_api.utils.logger import get_logger

logger = get_logger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors"""
    logger.warning(f"API error: {exc.message} (code: {exc.error_code})")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py                       # Shared fixtures
│
├── test_routes/                      # Route tests (24 tests)
│   ├── test_deployment.py            # 8 tests
│   ├── test_stack.py                 # 7 tests
│   ├── test_template.py              # 4 tests
│   ├── test_validation.py            # 3 tests
│   └── test_monitoring.py            # 2 tests
│
├── test_auth/                        # Auth tests (10 tests)
│   ├── test_cognito.py               # 6 tests
│   └── test_permissions.py           # 4 tests
│
└── test_integration/                 # Integration tests (6 tests)
    ├── test_full_deployment.py       # 3 tests
    └── test_auth_flow.py             # 3 tests

Total: ~40 tests
```

### Test Fixtures (`conftest.py`)

```python
"""
Pytest Fixtures for API Testing
Architecture 3.1
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from cloud_api.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_cognito_token():
    """Mock valid Cognito JWT token"""
    return "eyJraWQiOiJtb2NrLWtpZCIsImFsZyI6IlJTMjU2In0..."


@pytest.fixture
def mock_user_admin():
    """Mock authenticated admin user"""
    return {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "admin",
        "email": "admin@example.com",
        "email_verified": True,
        "groups": ["Administrators"],
        "token_use": "id",
    }


@pytest.fixture
def mock_user_developer():
    """Mock authenticated developer user"""
    return {
        "user_id": "223e4567-e89b-12d3-a456-426614174001",
        "username": "developer",
        "email": "dev@example.com",
        "email_verified": True,
        "groups": ["Developers"],
        "token_use": "id",
    }


@pytest.fixture
def mock_user_readonly():
    """Mock authenticated read-only user"""
    return {
        "user_id": "323e4567-e89b-12d3-a456-426614174002",
        "username": "readonly",
        "email": "readonly@example.com",
        "email_verified": True,
        "groups": ["ReadOnly"],
        "token_use": "id",
    }


@pytest.fixture
def auth_headers_admin(mock_cognito_token):
    """Authorization headers for admin"""
    return {"Authorization": f"Bearer {mock_cognito_token}"}


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator"""
    with patch('cloud_shared.orchestrator.Orchestrator') as mock:
        yield mock


@pytest.fixture
def mock_template_manager():
    """Mock template manager"""
    with patch('cloud_shared.templates.TemplateManager') as mock:
        yield mock


@pytest.fixture
def mock_deployment_manager():
    """Mock deployment manager"""
    with patch('cloud_shared.deployment.DeploymentManager') as mock:
        yield mock
```

---

### Example Route Tests (`test_routes/test_deployment.py`)

```python
"""
Tests for Deployment Endpoints
Architecture 3.1
"""

import pytest
from unittest.mock import Mock, patch


def test_initialize_deployment_success(client, auth_headers_admin, mock_template_manager, mock_deployment_manager):
    """Test successful deployment initialization"""
    # Mock template manager
    mock_template_manager.return_value.generate_manifest.return_value = {
        "version": "3.1",
        "deployment_id": "D1BRV40",
        "organization": "TestOrg",
        "project": "test-project",
    }

    # Mock deployment manager
    mock_deployment = Mock()
    mock_deployment.manifest_path = "/path/to/manifest.yaml"
    mock_deployment.created_at = "2025-10-23T10:00:00Z"
    mock_deployment_manager.return_value.initialize_deployment.return_value = mock_deployment

    # Make request
    response = client.post(
        "/api/v1/deployments/init",
        headers=auth_headers_admin,
        json={
            "organization": "TestOrg",
            "project": "test-project",
            "domain": "test.example.com",
            "template": "default",
            "environments": {
                "dev": {
                    "enabled": True,
                    "region": "us-east-1",
                    "account_id": "111111111111"
                }
            }
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "deployment_id" in data
    assert data["status"] == "initialized"


def test_initialize_deployment_unauthorized(client):
    """Test deployment initialization without authentication"""
    response = client.post(
        "/api/v1/deployments/init",
        json={
            "organization": "TestOrg",
            "project": "test-project",
            "domain": "test.example.com",
            "template": "default",
            "environments": {}
        }
    )

    assert response.status_code == 401


def test_deploy_deployment_success(client, auth_headers_admin, mock_orchestrator):
    """Test successful deployment"""
    # Mock orchestrator
    mock_result = Mock()
    mock_result.layers = [
        {"layer": 1, "stacks": ["network"], "status": "in_progress"}
    ]
    mock_result.started_at = "2025-10-23T10:05:00Z"
    mock_orchestrator.return_value.deploy_all.return_value = mock_result

    response = client.post(
        "/api/v1/deployments/D1BRV40/deploy",
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deployment_id"] == "D1BRV40"
    assert data["status"] == "deploying"


# ... 5 more deployment endpoint tests
```

---

### Example Auth Tests (`test_auth/test_cognito.py`)

```python
"""
Tests for Cognito Authentication
Architecture 3.1
"""

import pytest
from unittest.mock import Mock, patch
from jose import JWTError

from cloud_api.auth.cognito import decode_jwt_token, verify_token


def test_decode_valid_token():
    """Test decoding a valid JWT token"""
    with patch('cloud_api.auth.cognito.jwt.decode') as mock_decode:
        mock_decode.return_value = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "cognito:username": "user",
            "cognito:groups": ["Developers"],
        }

        token = "valid.jwt.token"
        result = decode_jwt_token(token)

        assert result["sub"] == "123e4567-e89b-12d3-a456-426614174000"
        assert result["email"] == "user@example.com"


def test_decode_expired_token():
    """Test decoding an expired token"""
    with patch('cloud_api.auth.cognito.jwt.decode') as mock_decode:
        mock_decode.side_effect = JWTError("Token expired")

        token = "expired.jwt.token"
        with pytest.raises(JWTError):
            decode_jwt_token(token)


def test_decode_invalid_signature():
    """Test decoding a token with invalid signature"""
    with patch('cloud_api.auth.cognito.jwt.decode') as mock_decode:
        mock_decode.side_effect = JWTError("Signature verification failed")

        token = "invalid.jwt.token"
        with pytest.raises(JWTError):
            decode_jwt_token(token)


# ... 3 more Cognito tests
```

---

### Example Integration Tests (`test_integration/test_full_deployment.py`)

```python
"""
Integration Tests for Full Deployment Flow
Architecture 3.1
"""

import pytest
from unittest.mock import Mock, patch


def test_full_deployment_flow(client, auth_headers_admin):
    """Test complete deployment flow from init to deploy"""
    # 1. Initialize deployment
    with patch('cloud_shared.templates.TemplateManager'), \
         patch('cloud_shared.deployment.DeploymentManager'):

        response = client.post(
            "/api/v1/deployments/init",
            headers=auth_headers_admin,
            json={
                "organization": "TestOrg",
                "project": "test-project",
                "domain": "test.example.com",
                "template": "default",
                "environments": {
                    "dev": {
                        "enabled": True,
                        "region": "us-east-1",
                        "account_id": "111111111111"
                    }
                }
            }
        )

        assert response.status_code == 201
        deployment_id = response.json()["deployment_id"]

    # 2. Deploy deployment
    with patch('cloud_shared.orchestrator.Orchestrator'):
        response = client.post(
            f"/api/v1/deployments/{deployment_id}/deploy",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deploying"

    # 3. Check status
    with patch('cloud_shared.deployment.DeploymentManager'):
        response = client.get(
            f"/api/v1/deployments/{deployment_id}/status",
            headers=auth_headers_admin
        )

        assert response.status_code == 200


# ... 2 more integration tests
```

---

## Implementation Plan

### Phase 1: Core API Setup (Est: 4 hours)

**1.1 Project Setup**
- Create `cloud/tools/api/` directory structure
- Create `pyproject.toml` and `requirements.txt`
- Configure FastAPI application
- Setup logging

**1.2 Authentication**
- Implement Cognito JWT validation (`auth/cognito.py`)
- Implement FastAPI dependencies (`auth/dependencies.py`)
- Implement permission checks (`auth/permissions.py`)
- Test authentication flow

**1.3 Models**
- Create request models (`models/requests.py`)
- Create response models (`models/responses.py`)
- Create error models (`models/errors.py`)

---

### Phase 2: API Endpoints (Est: 8 hours)

**2.1 Deployment Endpoints** (3 hours)
- Implement `routes/deployment.py` (8 endpoints)
- Connect to shared orchestrator and deployment manager
- Test each endpoint

**2.2 Stack Endpoints** (2 hours)
- Implement `routes/stack.py` (7 endpoints)
- Connect to shared Pulumi wrapper
- Test each endpoint

**2.3 Template Endpoints** (1 hour)
- Implement `routes/template.py` (4 endpoints)
- Connect to shared template manager
- Test each endpoint

**2.4 Validation Endpoints** (1 hour)
- Implement `routes/validation.py` (3 endpoints)
- Connect to shared validators
- Test each endpoint

**2.5 Monitoring Endpoints** (1 hour)
- Implement `routes/monitoring.py` (2 endpoints)
- Implement log aggregation
- Test each endpoint

---

### Phase 3: Production Features (Est: 4 hours)

**3.1 Middleware**
- CORS configuration (`middleware/cors.py`)
- Request logging (`middleware/logging.py`)
- Rate limiting (`middleware/rate_limit.py`)

**3.2 Error Handling**
- Exception handlers (`exceptions/handlers.py`)
- Error response formatting
- Error logging

**3.3 Utilities**
- Logger configuration (`utils/logger.py`)
- Response helpers (`utils/response.py`)

---

### Phase 4: Testing (Est: 6 hours)

**4.1 Route Tests** (3 hours)
- Test deployment endpoints (8 tests)
- Test stack endpoints (7 tests)
- Test template endpoints (4 tests)
- Test validation endpoints (3 tests)
- Test monitoring endpoints (2 tests)

**4.2 Auth Tests** (2 hours)
- Test Cognito JWT validation (6 tests)
- Test permission checks (4 tests)

**4.3 Integration Tests** (1 hour)
- Test full deployment flow (3 tests)
- Test authentication flow (3 tests)

---

### Phase 5: Documentation & Deployment (Est: 2 hours)

**5.1 Documentation**
- API README
- Environment configuration guide
- Authentication setup guide

**5.2 Deployment**
- Docker configuration
- Environment variables
- Deployment scripts

**Total Estimated Time: 24 hours**

---

## Success Criteria

### Functional Requirements

- [ ] **24 API endpoints implemented** and tested
- [ ] **AWS Cognito authentication** working on all endpoints
- [ ] **70-80% code reuse** from CLI business logic
- [ ] **OpenAPI documentation** auto-generated at `/api/docs`
- [ ] **40+ tests passing** (route + auth + integration)
- [ ] **Error handling** for all error cases
- [ ] **Production middleware** (CORS, logging, rate limiting)

### Non-Functional Requirements

- [ ] **Response time** < 200ms for non-deployment endpoints
- [ ] **Authentication** < 100ms token validation
- [ ] **Availability** 99.9% uptime
- [ ] **Security** All endpoints require authentication
- [ ] **Logging** All requests and errors logged
- [ ] **Documentation** Complete OpenAPI schema

### Code Quality

- [ ] **Type hints** on all functions
- [ ] **Docstrings** on all public functions
- [ ] **Tests** 90%+ code coverage
- [ ] **Linting** Pass ruff/black checks
- [ ] **Security** No secrets in code

---

## Appendix: Dependencies

### `requirements.txt`

```txt
# FastAPI and server
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Authentication
python-jose[cryptography]==3.3.0
boto3==1.29.0
requests==2.31.0

# Pydantic
pydantic==2.5.0
pydantic-settings==2.1.0

# Shared code (from CLI)
-e ../shared

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Development
black==23.11.0
ruff==0.1.6
mypy==1.7.1
```

---

**End of Session 4 Document**

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 4
**Document Version:** 1.0
**Last Updated:** 2025-10-23
