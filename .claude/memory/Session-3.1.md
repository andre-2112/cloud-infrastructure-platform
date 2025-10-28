# Session 3.1 - Complete CLI Implementation

**Session Type:** CLI Completion & Core Business Logic
**Target:** Complete full CLI implementation with all 25+ commands
**Status:** Ready to Execute
**Expected Duration:** Full session (~80-120K tokens)
**Architecture Version:** 3.1
**Platform:** cloud-0.7

---

## Executive Summary

**What Happened:** Session 2.1 successfully delivered the platform foundation (directory structure, 16 migrated stacks, Python CLI framework), but did NOT deliver the complete CLI implementation as originally planned. Only the CLI framework and placeholders were created.

**What's Needed:** This session will complete the full CLI implementation with all business logic, orchestration, validation, and 25+ working commands.

**Why This Matters:** The CLI is the primary interface for the platform. The REST API (Session 4) and all other components depend on a working CLI as the authoritative implementation.

---

## Context & Background

### Previous Sessions Recap

**Session 1 (COMPLETED):**
- Generated complete Architecture 3.1 documentation (16 documents)
- All specifications ready for implementation

**Session 2.1 (COMPLETED):**
- Created complete directory structure
- Migrated all 16 Pulumi stacks (index.ts at root, correct structure)
- Created Python CLI framework:
  - Project structure with Typer
  - Module directories (commands/, orchestrator/, etc.)
  - Basic utilities (deployment_id, logger)
  - Manifest validator with Pydantic
  - 10 passing tests
- Generated generic templates
- **BUT:** Only framework created, not full implementation

**What Session 2.1 Delivered (CLI-specific):**
```
cloud/tools/cli/
├── src/cloud_cli/
│   ├── main.py              # ✅ Entry point with placeholders
│   ├── commands/            # ❌ Empty (needs 25+ commands)
│   ├── orchestrator/        # ❌ Empty (needs full orchestration)
│   ├── templates/           # ❌ Empty (needs template management)
│   ├── deployment/          # ❌ Empty (needs deployment manager)
│   ├── runtime/             # ❌ Empty (needs runtime resolver)
│   ├── pulumi/              # ❌ Empty (needs Pulumi wrapper)
│   ├── validation/          # ✅ manifest_validator.py only
│   └── utils/               # ✅ deployment_id.py, logger.py only
└── tests/                   # ✅ 10 tests (but only for utils/validation)
```

### What This Session Must Deliver

**Complete, working CLI with:**
1. All 25+ command implementations
2. Full orchestration engine
3. Complete template management system
4. Deployment lifecycle management
5. Runtime value resolution
6. Pulumi integration wrapper
7. All validators (manifest, dependency, AWS, Pulumi)
8. Comprehensive test suite
9. Integration testing

---

## Deep Analysis: What's Needed for Complete CLI

### 1. Core Business Logic Modules

These modules contain the platform's core intelligence and will be shared with the REST API:

#### A. **Orchestrator Engine** (`src/cloud_cli/orchestrator/`)

**Purpose:** Layer-based deployment execution with dependency resolution

**Required Files:**
```python
orchestrator/
├── __init__.py
├── orchestrator.py           # Main orchestration logic
├── dependency_resolver.py    # Build dependency graph, detect cycles
├── layer_calculator.py       # Calculate execution layers
└── execution_engine.py       # Execute stacks in order
```

**Key Responsibilities:**
- Parse deployment manifest
- Build dependency graph from stack declarations
- Detect circular dependencies
- Calculate execution layers
- Execute stacks layer by layer
- Support parallel execution within layers
- Handle errors and rollback
- Emit progress events

**Core Algorithm:**
```python
# 1. Parse manifest → get enabled stacks
# 2. Build dependency graph (stack → [dependencies])
# 3. Detect cycles (DFS-based cycle detection)
# 4. Calculate layers using topological sort:
#    - Layer 1: Stacks with no dependencies
#    - Layer N: Stacks depending only on layers < N
# 5. Execute layer by layer:
#    - For each layer:
#      - Execute stacks in parallel (up to max_parallel)
#      - Wait for all to complete
#      - Check for errors
#      - If error: stop and rollback
# 6. Return results
```

#### B. **Template Management** (`src/cloud_cli/templates/`)

**Purpose:** Load, validate, and generate manifests from templates

**Required Files:**
```python
templates/
├── __init__.py
├── template_manager.py       # Load and validate templates
├── manifest_generator.py     # Generate manifest from template
└── template_renderer.py      # Render template placeholders
```

**Key Responsibilities:**
- Load templates from `tools/templates/default/` and `tools/templates/custom/`
- Validate template structure
- Generate deployment manifest from template
- Render placeholders ({{STACK_NAME}}, {{DEPLOYMENT_ID}}, etc.)
- Merge template defaults with user overrides

#### C. **Deployment Manager** (`src/cloud_cli/deployment/`)

**Purpose:** Manage deployment lifecycle and state

**Required Files:**
```python
deployment/
├── __init__.py
├── deployment_manager.py     # CRUD operations on deployments
├── state_manager.py          # Track deployment state
└── config_generator.py       # Generate stack config files
```

**Key Responsibilities:**
- Create deployment directory structure
- Generate manifest from template
- Generate stack config files (stack.env.yaml)
- Track deployment state (initialized, deploying, deployed, failed)
- List all deployments
- Get deployment status
- Clean up deployments

#### D. **Runtime Resolver** (`src/cloud_cli/runtime/`)

**Purpose:** Resolve runtime placeholders and cross-stack references

**Required Files:**
```python
runtime/
├── __init__.py
├── placeholder_resolver.py   # Resolve {{placeholders}}
├── stack_reference_resolver.py  # Resolve cross-stack refs
└── aws_query_resolver.py     # Query AWS for runtime values
```

**Key Responsibilities:**
- Parse and resolve runtime placeholders
- Query Pulumi state for stack outputs
- Query AWS for resource information
- Cache resolved values
- Handle missing references gracefully

**Placeholder Types:**
```python
# Stack output references
{{stack.network.vpcId}}  # → Query Pulumi state

# AWS queries
{{aws.vpc.default}}      # → Query AWS

# Deployment values
{{deployment.id}}        # → From manifest
{{deployment.org}}       # → From manifest
```

#### E. **Pulumi Wrapper** (`src/cloud_cli/pulumi/`)

**Purpose:** Interact with Pulumi Cloud and execute Pulumi operations

**Required Files:**
```python
pulumi/
├── __init__.py
├── pulumi_wrapper.py         # Pulumi Automation API wrapper
├── stack_operations.py       # up, destroy, preview, refresh
└── state_queries.py          # Query stack outputs
```

**Key Responsibilities:**
- Initialize Pulumi stacks
- Execute `pulumi up` / `pulumi destroy` / `pulumi preview`
- Query stack outputs
- Handle Pulumi errors
- Stream Pulumi output
- Manage Pulumi configuration

**Using Pulumi Automation API:**
```python
import pulumi.automation as auto

# Create or select stack
stack = auto.create_or_select_stack(
    stack_name=f"{deployment_id}-{stack_name}-{environment}",
    project_name=project_name,  # Business project
    work_dir=stack_dir,
)

# Set configuration
stack.set_config("aws:region", auto.ConfigValue(value=region))
stack.set_config("deploymentId", auto.ConfigValue(value=deployment_id))

# Execute
up_result = stack.up(on_output=print)
```

#### F. **Validators** (`src/cloud_cli/validation/`)

**Purpose:** Validate all aspects of deployment

**Required Files:**
```python
validation/
├── __init__.py
├── manifest_validator.py     # ✅ Already exists
├── dependency_validator.py   # Validate dependency graph
├── aws_validator.py          # Validate AWS credentials
├── pulumi_validator.py       # Validate Pulumi setup
└── stack_validator.py        # Validate stack structure
```

**Key Responsibilities:**
- Validate manifest syntax and schema
- Validate dependency graph (no cycles)
- Validate AWS credentials and permissions
- Validate Pulumi Cloud access
- Validate stack code structure
- Pre-deployment validation

---

### 2. CLI Commands Implementation

All 25+ commands need full implementation. Organized by category:

#### A. **Deployment Lifecycle Commands** (6 commands)

**1. `cloud init`**
```python
# commands/init_cmd.py
def init(
    deployment_id: Optional[str],
    org: str,
    project: str,
    domain: str,
    template: str,
    region: str,
    account_dev: str,
    ...
):
    # 1. Generate deployment ID if not provided
    # 2. Create deployment directory
    # 3. Load template
    # 4. Generate manifest
    # 5. Generate config files for all stacks
    # 6. Create deployment state file
```

**2. `cloud deploy`**
```python
# commands/deploy_cmd.py
def deploy(deployment_id: str, environment: str, ...):
    # 1. Load manifest
    # 2. Validate deployment
    # 3. Build orchestration plan
    # 4. Execute orchestrator
    # 5. Track progress
    # 6. Report results
```

**3. `cloud deploy-stack`**
```python
# commands/deploy_stack_cmd.py
def deploy_stack(deployment_id: str, stack_name: str, environment: str, ...):
    # 1. Load manifest
    # 2. Validate stack exists
    # 3. Check dependencies are deployed
    # 4. Deploy single stack
    # 5. Report result
```

**4. `cloud destroy`**
```python
# commands/destroy_cmd.py
def destroy(deployment_id: str, environment: str, ...):
    # 1. Load manifest
    # 2. Build reverse orchestration plan (reverse layers)
    # 3. Execute reverse orchestration
    # 4. Clean up state
```

**5. `cloud destroy-stack`**
```python
# commands/destroy_stack_cmd.py
def destroy_stack(deployment_id: str, stack_name: str, environment: str, ...):
    # 1. Check no other stacks depend on this
    # 2. Destroy single stack
    # 3. Update state
```

**6. `cloud rollback`**
```python
# commands/rollback_cmd.py
def rollback(deployment_id: str, environment: str, ...):
    # 1. Get previous successful state
    # 2. Calculate diff
    # 3. Roll back changes
```

#### B. **Environment Management** (3 commands)

**7. `cloud enable-environment`**
**8. `cloud disable-environment`**
**9. `cloud list-environments`**

#### C. **Stack Management** (5 commands)

**10. `cloud register-stack`** - Register new stack template
**11. `cloud update-stack`** - Update stack in manifest
**12. `cloud unregister-stack`** - Remove stack from manifest
**13. `cloud list-stacks`** - List all available stacks
**14. `cloud validate-stack`** - Validate stack structure

#### D. **Template Management** (5 commands)

**15. `cloud list-templates`**
**16. `cloud show-template`**
**17. `cloud create-template`**
**18. `cloud update-template`**
**19. `cloud validate-template`**

#### E. **Validation Commands** (4 commands)

**20. `cloud validate`** - Full deployment validation
**21. `cloud validate-dependencies`** - Validate dependency graph
**22. `cloud validate-aws`** - Validate AWS credentials
**23. `cloud validate-pulumi`** - Validate Pulumi setup

#### F. **Status & Monitoring** (4 commands)

**24. `cloud status`** - Show deployment status
**25. `cloud list`** - List all deployments
**26. `cloud logs`** - Show deployment logs
**27. `cloud discover-resources`** - Discover AWS resources

---

### 3. Testing Strategy

**Unit Tests (40+ tests):**
- Each command: 2-3 tests
- Each core module: 3-5 tests
- Utilities and validators: 2-3 tests each

**Integration Tests (10+ tests):**
- Full deployment workflow
- Rollback scenarios
- Error handling
- Cross-stack dependencies

**Test Structure:**
```
tests/
├── test_commands/
│   ├── test_init.py
│   ├── test_deploy.py
│   ├── test_destroy.py
│   └── ... (25+ command tests)
├── test_orchestrator/
│   ├── test_dependency_resolver.py
│   ├── test_layer_calculator.py
│   └── test_execution_engine.py
├── test_templates/
│   ├── test_template_manager.py
│   └── test_manifest_generator.py
├── test_deployment/
│   ├── test_deployment_manager.py
│   └── test_state_manager.py
├── test_runtime/
│   ├── test_placeholder_resolver.py
│   └── test_stack_reference_resolver.py
├── test_pulumi/
│   ├── test_pulumi_wrapper.py
│   └── test_stack_operations.py
├── test_validation/
│   ├── test_manifest_validator.py  # ✅ Exists
│   ├── test_dependency_validator.py
│   └── test_aws_validator.py
└── integration/
    ├── test_full_deployment.py
    ├── test_rollback.py
    └── test_error_handling.py
```

---

## Implementation Plan

### Phase 1: Core Business Logic (Priority: HIGHEST)

**1.1 Orchestrator Engine**
- Dependency resolver
- Layer calculator
- Execution engine

**1.2 Template Management**
- Template loader
- Manifest generator

**1.3 Deployment Manager**
- Deployment CRUD
- State management

**1.4 Runtime Resolver**
- Placeholder resolution
- Stack reference queries

**1.5 Pulumi Wrapper**
- Automation API integration
- Stack operations

**1.6 Complete Validators**
- Dependency validator
- AWS validator
- Pulumi validator

### Phase 2: CLI Commands (Priority: HIGH)

**2.1 Critical Commands**
- `init`, `deploy`, `destroy`, `status`, `list`, `validate`

**2.2 Stack Management**
- `deploy-stack`, `destroy-stack`, `list-stacks`

**2.3 Environment Management**
- `enable-environment`, `disable-environment`, `list-environments`

**2.4 Template Management**
- `list-templates`, `show-template`, `create-template`

**2.5 Validation & Monitoring**
- `validate-*`, `logs`, `discover-resources`

### Phase 3: Testing (Priority: HIGH)

**3.1 Unit Tests**
- 40+ unit tests for all modules

**3.2 Integration Tests**
- Full workflow tests

**3.3 CLI Testing Scripts**
- Automated CLI test suite

### Phase 4: Documentation & Verification

**4.1 Update Documentation**
- CLI implementation notes
- Testing guide updates

**4.2 Create Test Scripts**
- `test_cli_full.sh` - Complete CLI test
- `test_cli_integration.py` - Integration tests

---

## Success Criteria

✅ **All 25+ commands implemented and working**
✅ **Core business logic complete (orchestrator, templates, deployment, runtime, Pulumi)**
✅ **All validators implemented**
✅ **40+ unit tests passing**
✅ **10+ integration tests passing**
✅ **Full deployment workflow tested**
✅ **CLI can initialize, deploy, and destroy a test deployment**

---

## Code Sharing Architecture (Answers to 2.4 Questions)

### Question 2.4.1: Should we share common code between CLI and REST API?

**Answer: YES, absolutely. Estimated 70-80% shared code.**

**Shared vs. Unique:**

| Component | Shared? | % Shared | Notes |
|-----------|---------|----------|-------|
| **Orchestrator** | ✅ Yes | 100% | Core business logic |
| **Template Manager** | ✅ Yes | 100% | Core business logic |
| **Deployment Manager** | ✅ Yes | 100% | Core business logic |
| **Runtime Resolver** | ✅ Yes | 100% | Core business logic |
| **Pulumi Wrapper** | ✅ Yes | 100% | Core business logic |
| **Validators** | ✅ Yes | 100% | Core business logic |
| **Utilities** | ✅ Yes | 100% | deployment_id, logger, etc. |
| **CLI Commands** | ❌ No | 0% | CLI-specific (Typer) |
| **REST API Routes** | ❌ No | 0% | API-specific (FastAPI) |
| **CLI Tests** | Partial | 50% | Business logic tests reusable |

**Recommended Structure:**
```
cloud/tools/
├── core/                    # ✅ Shared business logic library
│   ├── orchestrator/
│   ├── templates/
│   ├── deployment/
│   ├── runtime/
│   ├── pulumi/
│   ├── validation/
│   └── utils/
├── cli/                     # CLI-specific (thin wrapper)
│   ├── src/cloud_cli/
│   │   ├── commands/       # Typer commands → call core
│   │   └── cli_main.py
│   └── tests/
└── api/                     # API-specific (thin wrapper)
    ├── src/cloud_api/
    │   ├── routes/         # FastAPI routes → call core
    │   └── api_main.py
    └── tests/
```

### Question 2.4.2: How should we maintain code?

**Answer: CLI is authoritative. Use hexagonal architecture.**

**Maintenance Strategy:**

**1. CLI as Authoritative Implementation**
- CLI implements all business logic first
- REST API wraps CLI business logic
- WebSocket, DB, etc. all use same core

**2. Hexagonal (Ports & Adapters) Architecture**
```
┌─────────────────────────────────────┐
│         Core Business Logic         │
│     (orchestrator, templates,       │
│      deployment, runtime, etc.)     │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Interfaces (Ports)        │   │
│  │  - IOrchestrator            │   │
│  │  - ITemplateManager         │   │
│  │  - IDeploymentManager       │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
           ↑         ↑         ↑
           │         │         │
     ┌─────┘    ┌────┘    └────┐
     │          │              │
┌────▼────┐ ┌───▼────┐  ┌──────▼──────┐
│   CLI   │ │  REST  │  │  WebSocket  │
│ Adapter │ │   API  │  │   Adapter   │
│ (Typer) │ │(FastAPI)│ │             │
└─────────┘ └────────┘  └─────────────┘
```

**3. Schema as Contract**

Use **OpenAPI schema** as authoritative contract:
- Generate from CLI command structure
- REST API must match schema exactly
- Schema drives documentation
- Schema drives testing

**4. Testing Strategy**
- Core business logic: 100% coverage
- CLI adapter: Integration tests
- REST API adapter: Contract tests (against schema)

**5. Change Management Process**
```
1. Make changes to core business logic
2. Update CLI commands (if needed)
3. Update OpenAPI schema (if behavior changed)
4. REST API automatically consistent (uses same core)
5. Run all tests (core, CLI, API)
6. Deploy changes
```

---

## Session Execution Checklist

### Pre-Execution
- [ ] Verify Session 2.1 completion
- [ ] Verify all 16 stacks built successfully
- [ ] Verify CLI framework exists
- [ ] Read Architecture 3.1 document

### Phase 1: Core Business Logic
- [ ] Implement orchestrator engine
- [ ] Implement template management
- [ ] Implement deployment manager
- [ ] Implement runtime resolver
- [ ] Implement Pulumi wrapper
- [ ] Complete all validators

### Phase 2: CLI Commands
- [ ] Implement 6 deployment lifecycle commands
- [ ] Implement 3 environment commands
- [ ] Implement 5 stack management commands
- [ ] Implement 5 template commands
- [ ] Implement 6 validation/monitoring commands

### Phase 3: Testing
- [ ] Write 40+ unit tests
- [ ] Write 10+ integration tests
- [ ] All tests passing
- [ ] Test full deployment workflow

### Phase 4: Verification
- [ ] CLI can initialize deployment
- [ ] CLI can deploy all stacks
- [ ] CLI can destroy deployment
- [ ] CLI handles errors gracefully
- [ ] All commands documented

---

## Next Sessions

**Session 4:** REST API Implementation (wraps core business logic)
**Session 5:** Database Integration (DynamoDB)
**Session 6:** WebSocket Monitoring

---

**Document Version:** 1.0
**Created:** 2025-10-23
**Session:** 3.1 of 6
**Platform:** cloud-0.7
**Architecture:** 3.1
