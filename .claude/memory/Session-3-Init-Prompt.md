# Session 3 - Initialization Prompt

**Platform:** cloud-0.7
**Architecture:** 3.1
**Session:** 3
**Purpose:** Execute complete CLI implementation
**Date:** 2025-10-23

---

## Instructions for AI

When starting Session 3, execute the following:

### 1. Read Session-3.1.md

```
Read: C:/Users/Admin/Documents/Workspace/cloud/.claude/memory/Session-3.1.md
```

This document contains:
- Complete CLI implementation plan
- All 25+ command specifications
- Core business logic modules
- Testing strategy
- Implementation phases

### 2. Review Current State

Check what already exists from Session 2.1:
```
- cloud/tools/cli/ directory structure
- Basic main.py with Typer
- Placeholder commands
- Test framework setup
```

### 3. Execute Implementation

Follow the plan in Session-3.1.md:

**Phase 1: Core Business Logic (8-10 hours)**
- Implement Orchestrator (`orchestrator/`)
- Implement Template Manager (`templates/`)
- Implement Deployment Manager (`deployment/`)
- Implement Runtime Resolver (`runtime/`)
- Implement Pulumi Wrapper (`pulumi/`)
- Implement Validators (`validation/`)

**Phase 2: CLI Commands (6-8 hours)**
- Implement all 25+ commands in `commands/`
- Wire commands to business logic
- Add rich formatting

**Phase 3: Testing (4-6 hours)**
- Write 40+ unit tests
- Write 10+ integration tests
- Achieve 90%+ coverage

**Phase 4: Documentation (2 hours)**
- Update CLI README
- Add command examples
- Create troubleshooting guide

### 4. Key Principles

- **Python 3.11+** - Use modern Python features (type hints, dataclasses)
- **Typer Framework** - Rich CLI with auto-help generation
- **Pydantic Validation** - Validate all inputs
- **Code Reuse** - 70-80% code will be reused in REST API (Session 4)
- **Testing** - Test-driven development, 90%+ coverage
- **Error Handling** - Clear error messages with suggestions

### 5. Success Criteria

Before marking Session 3 complete, verify:

- [ ] All 25+ CLI commands implemented and working
- [ ] All core business logic modules complete
- [ ] 40+ unit tests passing
- [ ] 10+ integration tests passing
- [ ] Code coverage 90%+
- [ ] CLI can initialize, validate, and deploy a full deployment
- [ ] Documentation updated

### 6. Integration Points

The CLI will be integrated with:
- **Session 4 (REST API)** - Shared business logic via `cloud/tools/shared/`
- **Session 5 (Database)** - Store deployment state in DynamoDB
- **Session 6 (WebSocket)** - Real-time monitoring support

### 7. File Organization

Move shared code to `cloud/tools/shared/` for reuse:

```
cloud/tools/shared/                # NEW: Shared business logic
├── orchestrator/
├── templates/
├── deployment/
├── runtime/
├── pulumi/
├── validation/
└── utils/

cloud/tools/cli/                   # CLI-specific code
├── commands/                      # Typer command handlers
├── main.py                        # CLI entry point
└── utils/                         # CLI-only utilities
```

### 8. Example Command Execution

After implementation, verify with:

```bash
# Initialize new deployment
python -m cloud_cli.main init \
  --organization MyOrg \
  --project my-project \
  --domain myproject.example.com \
  --template default

# Deploy all stacks
python -m cloud_cli.main deploy D1BRV40 --env dev

# Check status
python -m cloud_cli.main status D1BRV40

# List deployments
python -m cloud_cli.main list
```

### 9. Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=cloud_cli --cov-report=html --cov-report=term

# Run integration tests
pytest tests/test_integration/ -v
```

### 10. Common Issues

**Issue: Import errors**
- Solution: Ensure virtual environment activated
- Solution: Run `pip install -e .` in CLI directory

**Issue: Pulumi not found**
- Solution: Install Pulumi CLI: `curl -fsSL https://get.pulumi.com | sh`

**Issue: AWS credentials**
- Solution: Run `aws configure` to set credentials

---

## Quick Start

To begin Session 3 execution:

```bash
# 1. Read the plan
Read: cloud/.claude/memory/Session-3.1.md

# 2. Activate environment
cd cloud/tools/cli
source venv/Scripts/activate  # Windows Git Bash

# 3. Start implementing
# Follow phases in Session-3.1.md

# 4. Test as you go
pytest tests/ -v

# 5. Verify complete implementation
python -m cloud_cli.main --help
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-23
**Estimated Duration:** 20-26 hours
**Dependencies:** Sessions 1, 2.1 complete

**End of Session 3 Initialization Prompt**
