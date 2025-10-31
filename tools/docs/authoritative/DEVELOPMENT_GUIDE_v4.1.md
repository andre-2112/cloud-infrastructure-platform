# Development Guide - v4.1

**Platform:** cloud-0.7
**Architecture Version:** 4.1
**Document Type:** Developer Guide
**Date:** 2025-10-29
**Status:** Authoritative

---

## Table of Contents

1. [Introduction](#introduction)
2. [Governance Model: Dual Authority](#governance-model-dual-authority)
3. [When to Consult Documentation vs Code](#when-to-consult-documentation-vs-code)
4. [Handling Documentation-Code Conflicts](#handling-documentation-code-conflicts)
5. [Development Workflows](#development-workflows)
6. [Best Practices for Compliant Development](#best-practices-for-compliant-development)
7. [Testing Requirements](#testing-requirements)
8. [Documentation Standards](#documentation-standards)
9. [Code Review Checklist](#code-review-checklist)
10. [Common Development Scenarios](#common-development-scenarios)

---

## Introduction

### Purpose

This guide defines how to develop features, stacks, configurations, and tools for the cloud-0.7 platform in a way that ensures compliance with the v4.1 architecture.

### Dual Authority Principle

The platform uses a **dual authority model** where both documentation and implemented code serve as authoritative references, each with specific domains of authority.

**Key Insight:** Documentation and code are complementary, not redundant. Both are required for compliant development.

---

## Governance Model: Dual Authority

### Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│               AUTHORITATIVE REFERENCE MODEL                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TIER 1: STRATEGIC AUTHORITY - DOCUMENTATION                │
│  Domain: Architecture, design intent, workflows             │
│  Source: v4.1 Documentation (Multi_Stack_Architecture.4.1)  │
│                                                              │
│  Use documentation for:                                      │
│    • Understanding system architecture                       │
│    • Learning design patterns and principles                │
│    • Planning new features or stacks                         │
│    • Understanding workflows and processes                   │
│    • Configuration formats and structures                    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TIER 2: TACTICAL AUTHORITY - CODE                          │
│  Domain: Implementation contracts, exact behavior           │
│  Source: tools/core/cloud_core/, tools/cli/src/cloud_cli/  │
│                                                              │
│  Use code for:                                              │
│    • Exact API signatures and return types                  │
│    • Data structures and field names                        │
│    • Error messages and exception types                     │
│    • Edge case behavior                                     │
│    • Validation rules and logic                             │
│    • Performance characteristics                            │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TIER 3: CONFLICT RESOLUTION                                │
│  When documentation and code disagree:                       │
│                                                              │
│  1. Code behavior is authoritative (proven by tests)        │
│  2. Document the discrepancy as an issue                    │
│  3. Resolve based on design intent:                         │
│     • Fix code to match docs if code violates design        │
│     • Update docs to match code if docs are outdated        │
│  4. Never leave conflicts unresolved                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why This Model?

**Documentation Provides:**
- Big picture understanding
- Design rationale
- Intended behavior
- Best practices
- Onboarding path

**Code Provides:**
- Exact specifications
- Current implementation
- Working examples
- Edge case handling
- Performance details

**Together They Provide:**
- Complete development guidance
- Mutual validation
- Clear path from concept to implementation

---

## When to Consult Documentation vs Code

### Decision Matrix

| Task | Consult Documentation | Consult Code |
|------|----------------------|--------------|
| **Understanding the system** | ✅ PRIMARY | ❌ Not needed |
| **Designing a new feature** | ✅ PRIMARY | ⚠️ For patterns |
| **Implementing a feature** | ⚠️ For structure | ✅ PRIMARY |
| **Creating a new stack** | ✅ PRIMARY | ⚠️ For examples |
| **Debugging an issue** | ⚠️ For context | ✅ PRIMARY |
| **Reviewing code** | ✅ For compliance | ✅ For correctness |
| **Writing tests** | ⚠️ For behavior | ✅ PRIMARY |
| **Creating config** | ✅ PRIMARY | ⚠️ For validation |
| **Error handling** | ❌ Usually missing | ✅ PRIMARY |
| **API integration** | ❌ High-level only | ✅ PRIMARY |

**Legend:**
- ✅ PRIMARY: Start here, main source of truth
- ⚠️ For X: Consult for specific purpose
- ❌ Not needed / Usually missing

### Detailed Guidance

#### Scenario 1: Understanding the System

**Start with:** Documentation
- **Read:** Multi_Stack_Architecture.4.1.md (sections 1-5)
- **Purpose:** Understand core/CLI separation, module organization, design principles
- **Outcome:** Mental model of system architecture

**Then:** Browse code structure
- **Look at:** Directory structure, module organization
- **Purpose:** Confirm understanding matches implementation
- **Outcome:** Confidence in architecture knowledge

#### Scenario 2: Designing a New Feature

**Start with:** Documentation
- **Read:** Relevant architecture sections
- **Check:** Existing patterns and workflows
- **Purpose:** Ensure design aligns with architecture

**Then:** Review similar code
- **Look at:** Existing implementations
- **Purpose:** Understand implementation patterns
- **Outcome:** Design that's both architecturally sound and practically implementable

**Example:**
```
Task: Add new validation rule for stack parameters

1. Read: Multi_Stack_Architecture.4.1.md section 15 (Validation)
   → Understand validation philosophy and patterns

2. Read: Stack_Parameters_and_Registration_Guide_v4.md
   → Understand parameter structure

3. Review: tools/core/cloud_core/validation/stack_code_validator.py
   → See how existing validation works

4. Design: New validation rule following existing patterns

5. Implement: Add to StackCodeValidator following API patterns

6. Test: Write tests matching existing test patterns

7. Document: Update docs if adding new capability
```

#### Scenario 3: Implementing a Feature

**Start with:** Documentation for structure
- **Read:** Architecture section for the module
- **Purpose:** Understand where feature fits

**Then:** Code for exact implementation
- **Read:** Related module source files
- **Check:** API signatures, data structures, patterns
- **Purpose:** Implement correctly

**Example:**
```
Task: Implement cross-stack dependency validation

1. Docs: Read section 12.3 (Cross-Stack Dependencies)
   → Understand how dependencies should work

2. Code: Read cloud_core/validation/dependency_validator.py
   → See actual validation logic

3. Code: Read cloud_core/orchestrator/dependency_resolver.py
   → Understand dependency resolution

4. Implement: Following patterns from existing code
   → Use actual data structures and methods

5. Test: Match behavior described in docs
   → Verify implementation meets design intent
```

#### Scenario 4: Creating a New Stack

**Start with:** Documentation
- **Read:** Complete_Stack_Management_Guide_v4.md
- **Read:** Stack_Parameters_and_Registration_Guide_v4.md
- **Purpose:** Understand stack structure and registration process

**Then:** Reference templates and existing stacks
- **Look at:** tools/templates/config/<stack>.yaml
- **Look at:** Existing stack implementations
- **Purpose:** Follow established patterns

**Workflow:**
```bash
# 1. Understand from docs
#    - Read Complete_Stack_Management_Guide_v4.md
#    - Review enhanced template structure

# 2. Create stack code
mkdir -p stacks/my-new-stack
cd stacks/my-new-stack

# 3. Write TypeScript following patterns
cat > index.ts << 'EOF'
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Get config - follows doc patterns
const config = new pulumi.Config();
const myParam = config.require("myParam");

// Implementation...

// Export outputs - follows doc patterns
export const myOutput = resource.id;
EOF

# 4. Auto-extract and register (from docs)
cd ../../tools/cli
python -m cloud_cli.main register-stack my-new-stack --auto-extract

# 5. Validate (from docs)
python -m cloud_cli.main validate-stack my-new-stack --strict
```

#### Scenario 5: Debugging an Issue

**Start with:** Code
- **Find:** Where error occurs
- **Read:** Surrounding implementation
- **Purpose:** Understand actual behavior

**Then:** Documentation for context
- **Read:** Architecture section for the module
- **Purpose:** Understand intended behavior
- **Outcome:** Determine if bug is in code or understanding

**Example:**
```
Issue: Stack validation fails with unexpected error

1. Code: Read error message and stack trace
   → Error in stack_code_validator.py line 145

2. Code: Read validation logic around line 145
   → See what condition triggered error

3. Code: Read test files for this scenario
   → See if this is tested/expected

4. Docs: Read validation section
   → Understand intended behavior

5. Compare: Does code match doc intent?
   → If yes: May be valid error
   → If no: Bug in code or docs

6. Fix: Based on design intent
```

#### Scenario 6: Writing Tests

**Start with:** Code
- **Read:** Existing test files
- **Copy:** Test patterns and structure
- **Purpose:** Match existing test style

**Then:** Documentation for behavior
- **Read:** Architecture section for expected behavior
- **Purpose:** Ensure tests validate documented behavior

**Test Structure:**
```python
# File: tools/core/tests/test_validation/test_my_feature.py

import pytest
from pathlib import Path
from cloud_core.validation.stack_code_validator import StackCodeValidator

class TestMyFeature:
    """Test suite for my new feature"""

    def test_basic_case(self):
        """Test basic functionality matches docs"""
        # Arrange: Set up according to docs
        validator = StackCodeValidator()
        template = {...}  # From doc examples

        # Act: Call API from code
        result = validator.validate(...)

        # Assert: Verify behavior from docs
        assert result.valid == True

    def test_edge_case(self):
        """Test edge case discovered in code"""
        # Test based on code behavior

    def test_error_handling(self):
        """Test error handling from code"""
        # Test based on actual error structures
```

---

## Handling Documentation-Code Conflicts

### When Conflicts Arise

Conflicts occur when:
- Documentation describes behavior X
- Code implements behavior Y
- X ≠ Y

### Resolution Process

```
┌────────────────────────────────────────────────────────┐
│          CONFLICT RESOLUTION WORKFLOW                   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  1. IDENTIFY CONFLICT                                   │
│     • Note exact discrepancy                            │
│     • Document both behaviors                           │
│     • Check if tests cover this case                    │
│                                                         │
│  2. DETERMINE ROOT CAUSE                                │
│     • Is code wrong? (violates design intent)           │
│     • Are docs wrong? (outdated or incorrect)           │
│     • Are both valid? (design decision needed)          │
│                                                         │
│  3. DECIDE RESOLUTION                                   │
│                                                         │
│     If code violates design intent:                     │
│       → Fix code to match docs                          │
│       → Update tests to match docs                      │
│       → Document why code was wrong                     │
│                                                         │
│     If docs are outdated/incorrect:                     │
│       → Update docs to match code                       │
│       → Document why docs were wrong                    │
│       → Verify tests validate actual behavior           │
│                                                         │
│     If both are valid interpretations:                  │
│       → Escalate to architecture team                   │
│       → Choose based on design principles               │
│       → Update both code and docs to align              │
│                                                         │
│  4. IMPLEMENT RESOLUTION                                │
│     • Make changes to code and/or docs                  │
│     • Update tests to validate correct behavior         │
│     • Add comments referencing resolution               │
│                                                         │
│  5. VERIFY RESOLUTION                                   │
│     • Tests pass and validate correct behavior          │
│     • Docs accurately describe implementation           │
│     • No ambiguity remains                              │
│                                                         │
│  6. DOCUMENT RESOLUTION                                 │
│     • Add note to changelog                             │
│     • Comment in code if complex                        │
│     • Update related documentation                      │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Decision Criteria

**Fix Code When:**
- Code violates documented design principles
- Tests were written to match docs and now fail
- Behavior breaks documented workflows
- Implementation was a mistake

**Update Docs When:**
- Implementation is correct and intentional
- Code has 393+ tests proving it works
- Docs were written before implementation
- Docs misunderstood requirements

**Escalate When:**
- Both interpretations are valid
- Changes affect multiple components
- Design decision needed
- Breaking change required

### Example Resolution

**Conflict:**
```
Documentation says: "Type mismatches are errors"
Code implements: Type mismatches generate warnings, not errors

File: stack_code_validator.py line 174
if code_type != template_type:
    result.add_warning(...)  # Not add_error()
```

**Resolution Process:**

1. **Identify:** Docs say error, code does warning

2. **Root Cause:** Check tests and git history
   - Tests expect warnings
   - Design decision: Type mismatches shouldn't block validation
   - Rationale: TypeScript type inference may differ from template declarations

3. **Decision:** Docs are wrong, code is correct
   - Design intent: Flexible type checking
   - Code behavior is intentional

4. **Implementation:**
   - Update Multi_Stack_Architecture.4.1.md section 15
   - Change "type mismatches are errors" to "type mismatches generate warnings"
   - Add note explaining rationale

5. **Verification:**
   - Tests still pass
   - Docs now match code
   - No ambiguity

6. **Documentation:**
   ```markdown
   ### Type Validation

   Type mismatches between code and template generate **warnings**, not errors.
   This allows for flexibility when TypeScript type inference may differ from
   template declarations (e.g., a number literal "10.0.0.0/16" inferred as
   string vs explicitly typed as string).

   **Rationale:** Strict type checking would block valid stacks where types
   are semantically correct but syntactically different.
   ```

---

## Development Workflows

### Workflow 1: Implementing a New Feature

```
┌─────────────────────────────────────────────────────────────┐
│              NEW FEATURE IMPLEMENTATION WORKFLOW             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE 1: UNDERSTAND                                         │
│  ─────────────────────────────────────────────────────────  │
│  1. Read relevant architecture documentation                │
│     • Multi_Stack_Architecture.4.1.md (relevant sections)   │
│     • Component-specific guides                              │
│                                                              │
│  2. Review existing similar features                         │
│     • Read related code modules                              │
│     • Study test files for patterns                          │
│                                                              │
│  3. Document your understanding                              │
│     • Write design document or notes                         │
│     • List assumptions and questions                         │
│                                                              │
│  PHASE 2: DESIGN                                             │
│  ─────────────────────────────────────────────────────────  │
│  1. Design following architecture patterns                   │
│     • Align with documented design principles               │
│     • Use existing patterns where possible                   │
│                                                              │
│  2. Define API contracts                                     │
│     • Method signatures (matching code patterns)             │
│     • Data structures (matching existing structures)         │
│     • Error handling (matching existing patterns)            │
│                                                              │
│  3. Plan testing approach                                    │
│     • Unit tests for core logic                              │
│     • Integration tests for workflows                        │
│     • Match existing test patterns                           │
│                                                              │
│  PHASE 3: IMPLEMENT                                          │
│  ─────────────────────────────────────────────────────────  │
│  1. Write tests first (TDD)                                  │
│     • Follow existing test file structure                    │
│     • Test documented behavior                               │
│                                                              │
│  2. Implement following code patterns                        │
│     • Match existing API style                               │
│     • Use existing data structures                           │
│     • Follow error handling patterns                         │
│                                                              │
│  3. Run tests continuously                                   │
│     • pytest <test-file> -v                                  │
│     • Fix issues as they arise                               │
│                                                              │
│  PHASE 4: VALIDATE                                           │
│  ─────────────────────────────────────────────────────────  │
│  1. Run full test suite                                      │
│     • pytest tests/ -v                                       │
│     • Ensure no regressions                                  │
│                                                              │
│  2. Test integration                                         │
│     • Manual testing of workflows                            │
│     • Verify with actual stacks                              │
│                                                              │
│  3. Check documentation compliance                           │
│     • Does implementation match architecture?                │
│     • Are design principles followed?                        │
│                                                              │
│  PHASE 5: DOCUMENT                                           │
│  ─────────────────────────────────────────────────────────  │
│  1. Update documentation if needed                           │
│     • New capabilities: Update architecture docs             │
│     • Changed behavior: Update relevant sections             │
│     • New APIs: Update API reference                         │
│                                                              │
│  2. Add code comments                                        │
│     • Complex logic needs explanation                        │
│     • Reference docs for context                             │
│                                                              │
│  3. Write commit message                                     │
│     • Explain what and why                                   │
│     • Reference documentation sections                       │
│                                                              │
│  PHASE 6: REVIEW                                             │
│  ─────────────────────────────────────────────────────────  │
│  1. Self-review against checklist (see below)               │
│  2. Submit for code review                                   │
│  3. Address feedback                                         │
│  4. Merge when approved                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Workflow 2: Creating a New Stack

```
┌─────────────────────────────────────────────────────────────┐
│                NEW STACK CREATION WORKFLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  STEP 1: UNDERSTAND REQUIREMENTS                             │
│  ─────────────────────────────────────────────────────────  │
│  • What AWS resources are needed?                            │
│  • What inputs does this stack need?                         │
│  • What outputs will other stacks need?                      │
│  • What stacks does this depend on?                          │
│                                                              │
│  Read: Complete_Stack_Management_Guide_v4.md                │
│       Stack_Parameters_and_Registration_Guide_v4.md         │
│                                                              │
│  STEP 2: DESIGN STACK STRUCTURE                              │
│  ─────────────────────────────────────────────────────────  │
│  1. Define parameters:                                       │
│     Inputs:                                                  │
│       - What configuration values are needed?                │
│       - Which are required vs optional?                      │
│       - What are sensible defaults?                          │
│     Outputs:                                                 │
│       - What resources do other stacks need?                 │
│       - What should be exposed for cross-stack refs?         │
│                                                              │
│  2. Identify dependencies:                                   │
│     - Which stacks must exist first?                         │
│     - What outputs do you need from them?                    │
│                                                              │
│  3. Determine layer:                                         │
│     - Calculate based on dependency depth                    │
│     - Verify no circular dependencies                        │
│                                                              │
│  STEP 3: IMPLEMENT STACK CODE                                │
│  ─────────────────────────────────────────────────────────  │
│  mkdir -p stacks/<stack-name>                                │
│  cd stacks/<stack-name>                                      │
│                                                              │
│  Create index.ts:                                            │
│    1. Import Pulumi and AWS packages                         │
│    2. Get configuration with Config.require*()               │
│    3. Get cross-stack references with StackReference          │
│    4. Create AWS resources                                   │
│    5. Export outputs                                         │
│                                                              │
│  Follow patterns from existing stacks                        │
│                                                              │
│  STEP 4: AUTO-EXTRACT TEMPLATE                               │
│  ─────────────────────────────────────────────────────────  │
│  cd ../../tools/cli                                          │
│  source venv/Scripts/activate                                │
│                                                              │
│  python -m cloud_cli.main register-stack <stack-name> \      │
│    --auto-extract                                            │
│                                                              │
│  This generates: tools/templates/config/<stack-name>.yaml   │
│                                                              │
│  STEP 5: REVIEW AND ENHANCE TEMPLATE                         │
│  ─────────────────────────────────────────────────────────  │
│  Edit tools/templates/config/<stack-name>.yaml:             │
│    • Add/improve descriptions                                │
│    • Verify types are correct                                │
│    • Set appropriate defaults                                │
│    • Add dependencies array                                  │
│    • Set layer number                                        │
│                                                              │
│  STEP 6: VALIDATE                                            │
│  ─────────────────────────────────────────────────────────  │
│  python -m cloud_cli.main validate-stack <stack-name> \      │
│    --strict                                                  │
│                                                              │
│  Fix any errors or warnings                                  │
│                                                              │
│  STEP 7: TEST DEPLOYMENT                                     │
│  ─────────────────────────────────────────────────────────  │
│  1. Add to test manifest:                                    │
│     deploy/TEST/manifest.yaml                                │
│                                                              │
│  2. Configure stack:                                         │
│     stacks:                                                  │
│       <stack-name>:                                          │
│         enabled: true                                        │
│         config:                                              │
│           <param>: <value>                                   │
│                                                              │
│  3. Deploy:                                                  │
│     python -m cloud_cli.main deploy TEST                     │
│                                                              │
│  4. Verify:                                                  │
│     • Check AWS console                                      │
│     • Verify outputs are correct                             │
│     • Test cross-stack references                            │
│                                                              │
│  STEP 8: DOCUMENT                                            │
│  ─────────────────────────────────────────────────────────  │
│  1. Add to stack documentation (if needed)                   │
│  2. Update deployment examples                               │
│  3. Add to template library                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Workflow 3: Fixing a Bug

```
┌─────────────────────────────────────────────────────────────┐
│                    BUG FIX WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  STEP 1: REPRODUCE                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Get exact error message and stack trace                   │
│  • Create minimal reproduction case                          │
│  • Document steps to reproduce                               │
│                                                              │
│  STEP 2: UNDERSTAND                                          │
│  ─────────────────────────────────────────────────────────  │
│  • Read code where error occurs                              │
│  • Understand the logic and intent                           │
│  • Read related documentation for expected behavior          │
│  • Check tests for this scenario                             │
│                                                              │
│  STEP 3: DIAGNOSE                                            │
│  ─────────────────────────────────────────────────────────  │
│  Questions to answer:                                        │
│  • Is this a code bug? (logic error, typo, etc.)            │
│  • Is this a design bug? (wrong approach)                    │
│  • Is this a doc bug? (wrong expectations)                   │
│  • Is this expected behavior? (not actually a bug)           │
│                                                              │
│  STEP 4: WRITE FAILING TEST                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Create test that reproduces the bug                       │
│  • Test should fail with current code                        │
│  • Test should pass when bug is fixed                        │
│                                                              │
│  STEP 5: FIX                                                 │
│  ─────────────────────────────────────────────────────────  │
│  If code bug:                                                │
│    • Fix the code                                            │
│    • Ensure tests pass                                       │
│    • Check for similar bugs elsewhere                        │
│                                                              │
│  If doc bug:                                                 │
│    • Update documentation                                    │
│    • Verify code behavior is correct                         │
│    • Update tests if needed                                  │
│                                                              │
│  STEP 6: VERIFY                                              │
│  ─────────────────────────────────────────────────────────  │
│  • New test passes                                           │
│  • All existing tests still pass                             │
│  • Reproduction case now works                               │
│  • No regressions introduced                                 │
│                                                              │
│  STEP 7: DOCUMENT                                            │
│  ─────────────────────────────────────────────────────────  │
│  • Update changelog                                          │
│  • Add comment in code if complex                            │
│  • Update docs if behavior changed                           │
│  • Reference issue/ticket in commit                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Best Practices for Compliant Development

### 1. Always Start with Architecture

**DON'T:**
```python
# Just start coding without understanding
def new_feature():
    # I'll figure it out as I go...
    pass
```

**DO:**
```python
# Read architecture docs first
# File: cloud_core/validation/new_validator.py

"""
New validation feature following architecture from
Multi_Stack_Architecture.4.1.md section 15.

Design intent: Template-first validation ensures code matches declarations.
This validator extends that pattern to validate X.

See: Stack_Parameters_and_Registration_Guide_v4.md for parameter structure.
"""

class NewValidator:
    """
    Validates X against Y following template-first pattern.

    Architecture: Part of validation module (cloud_core.validation)
    Dependencies: StackTemplateManager, ParameterExtractor
    Used by: CLI validate commands, deployment workflows
    """
```

### 2. Follow Existing Patterns

**DON'T:**
```python
# Invent new patterns
def my_custom_validation(data: dict) -> bool:
    # Returns True/False
    if something_wrong:
        return False
    return True
```

**DO:**
```python
# Follow ValidationResult pattern from existing code
def my_custom_validation(data: Dict) -> ValidationResult:
    """Validate X following ValidationResult pattern"""
    result = ValidationResult(valid=True)

    if something_wrong:
        result.add_error("Description of error", location="field:name")

    if something_suspicious:
        result.add_warning("Description of warning")

    return result
```

### 3. Write Tests Matching Documentation

**DON'T:**
```python
# Test arbitrary behavior
def test_validation():
    assert validator.validate(data) == True
```

**DO:**
```python
# Test documented behavior
def test_validation_matches_architecture():
    """
    Test validation following behavior documented in
    Multi_Stack_Architecture.4.1.md section 15.3

    Expected behavior:
    - Undeclared inputs → error
    - Unused inputs → warning (or error if strict=True)
    - Type mismatches → warning
    """
    validator = StackCodeValidator()

    # Test undeclared input (should be error)
    result = validator.validate(code_with_undeclared_input, template)
    assert result.get_error_count() == 1
    assert "undeclared" in result.errors[0].message.lower()

    # Test unused input non-strict (should be warning)
    result = validator.validate(code_without_input, template, strict=False)
    assert result.get_warning_count() == 1
    assert "unused" in result.warnings[0].message.lower()

    # Test unused input strict (should be error)
    result = validator.validate(code_without_input, template, strict=True)
    assert result.get_error_count() == 1
```

### 4. Handle Errors Consistently

**DON'T:**
```python
# Inconsistent error handling
try:
    result = do_something()
except:
    print("Error!")
    return None
```

**DO:**
```python
# Follow existing error handling patterns
from ..utils.logger import get_logger

logger = get_logger(__name__)

try:
    result = do_something()
except SpecificException as e:
    logger.error(f"Failed to do something: {str(e)}")
    # Return ValidationResult with error, or raise with context
    raise SomeError(f"Failed to do something: {str(e)}") from e
```

### 5. Document References

**DON'T:**
```python
# No context
def complex_logic():
    # Complex implementation
    pass
```

**DO:**
```python
def complex_logic():
    """
    Implements dependency resolution using topological sort.

    Architecture: Multi_Stack_Architecture.4.1.md section 9.2
    Algorithm: Kahn's algorithm for topological sorting
    Reference: Complete_Stack_Management_Guide_v4.md "Layer Calculation"

    Returns:
        List of layers, where each layer contains stacks that can be
        deployed in parallel.
    """
    # Implementation follows documented algorithm
```

### 6. Maintain Dual Sync

**DON'T:**
```python
# Change behavior without updating docs
def validate(self, strict: bool = True):  # Changed default!
    # Now strict by default
    pass
# → Docs still say strict=False is default → CONFLICT
```

**DO:**
```python
# Change behavior AND update docs
def validate(self, strict: bool = True):  # Changed default
    """
    NOTE: strict default changed to True in v4.2
    Updated: Multi_Stack_Architecture.4.1.md section 15
    Rationale: Strict validation catches more errors
    """
    pass

# AND update docs:
# Multi_Stack_Architecture.4.1.md:
# "validate() now defaults to strict=True (changed in v4.2)"
```

### 7. Use Type Hints

**DON'T:**
```python
def process(data):
    return result
```

**DO:**
```python
from pathlib import Path
from typing import Dict, List, Optional

def process(
    data: Dict[str, Any],
    options: Optional[List[str]] = None
) -> ValidationResult:
    """Process data with optional configuration"""
    return result
```

### 8. Keep Functions Focused

**DON'T:**
```python
def do_everything(stack_dir, template, config, env, options):
    # 200 lines of mixed concerns
    pass
```

**DO:**
```python
def validate_stack(stack_dir: Path, template: Dict) -> ValidationResult:
    """Validate stack code matches template. Single responsibility."""
    pass

def format_result(result: ValidationResult) -> str:
    """Format validation result for display. Single responsibility."""
    pass

def save_result(result: ValidationResult, output_path: Path) -> None:
    """Save validation result to file. Single responsibility."""
    pass
```

---

## Testing Requirements

### Test Coverage Requirements

**Minimum Coverage:**
- Core modules: 90%+ line coverage
- CLI commands: 80%+ line coverage
- Critical paths: 100% coverage

**What Must Be Tested:**
1. All public APIs
2. Error handling paths
3. Edge cases
4. Integration between modules
5. Documented behavior

### Test Categories

#### Unit Tests

**Purpose:** Test individual functions and classes in isolation

**Location:** `tools/core/tests/test_<module>/`

**Example:**
```python
# File: tools/core/tests/test_validation/test_stack_code_validator.py

import pytest
from pathlib import Path
from cloud_core.validation.stack_code_validator import StackCodeValidator

class TestStackCodeValidator:
    """Unit tests for StackCodeValidator"""

    def test_validate_matching_code_and_template(self):
        """Test validation passes when code matches template"""
        # Arrange
        validator = StackCodeValidator()
        template = {
            "parameters": {
                "inputs": {
                    "vpcCidr": {"type": "string", "required": True}
                },
                "outputs": {
                    "vpcId": {"type": "string"}
                }
            }
        }
        # Mock or fixture stack directory with matching code

        # Act
        result = validator.validate(stack_dir, template)

        # Assert
        assert result.valid == True
        assert result.get_error_count() == 0

    def test_validate_undeclared_input(self):
        """Test error when code uses undeclared input"""
        # Test that using Config.require("undeclared") generates error
        pass

    # More unit tests...
```

#### Integration Tests

**Purpose:** Test interaction between modules

**Location:** `tools/core/tests/test_integration/`

**Example:**
```python
# File: tools/core/tests/test_integration/test_validation_workflow.py

def test_register_and_validate_workflow():
    """
    Test complete workflow: extract → register → validate

    This integration test verifies the workflow documented in
    Complete_Stack_Management_Guide_v4.md section 4.
    """
    # 1. Extract parameters from stack code
    extractor = ParameterExtractor()
    extraction = extractor.extract_from_stack(stack_dir, "test-stack")
    assert extraction["success"] == True

    # 2. Generate template
    success, error = extractor.generate_template_file(
        stack_dir, template_path, "test-stack"
    )
    assert success == True

    # 3. Validate code matches template
    validator = StackCodeValidator()
    template = load_template(template_path)
    result = validator.validate(stack_dir, template)

    assert result.valid == True
```

#### CLI Tests

**Purpose:** Test CLI commands end-to-end

**Location:** `tools/cli/tests/`

**Example:**
```python
# File: tools/cli/tests/test_commands/test_validate_cmd.py

from click.testing import CliRunner
from cloud_cli.main import cli

def test_validate_stack_command():
    """Test 'cloud validate-stack' command"""
    runner = CliRunner()

    # Setup: Create test stack and template

    # Execute command
    result = runner.invoke(cli, ['validate-stack', 'test-stack'])

    # Verify output
    assert result.exit_code == 0
    assert "✓ Validation passed" in result.output
```

### Test Data and Fixtures

**Use Fixtures for Common Test Data:**

```python
# File: tools/core/tests/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def sample_template():
    """Fixture providing sample template data"""
    return {
        "name": "test-stack",
        "parameters": {
            "inputs": {
                "param1": {"type": "string", "required": True}
            },
            "outputs": {
                "output1": {"type": "string"}
            }
        }
    }

@pytest.fixture
def temp_stack_dir(tmp_path):
    """Fixture providing temporary stack directory"""
    stack_dir = tmp_path / "test-stack"
    stack_dir.mkdir()

    # Create sample index.ts
    (stack_dir / "index.ts").write_text("""
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const param1 = config.require("param1");

export const output1 = "value";
    """)

    return stack_dir
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tools/core/tests/test_validation/test_stack_code_validator.py

# Run specific test
pytest tools/core/tests/test_validation/test_stack_code_validator.py::TestStackCodeValidator::test_validate_matching_code_and_template

# Run with coverage
pytest --cov=cloud_core --cov-report=html

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

---

## Documentation Standards

### Code Documentation

#### Module Docstrings

```python
"""
Stack Code Validator

Validates that stack TypeScript code matches template parameter declarations.
Ensures template-first enforcement.

Architecture: Part of validation module (cloud_core.validation)
Reference: Multi_Stack_Architecture.4.1.md section 15

Usage:
    validator = StackCodeValidator()
    result = validator.validate(stack_dir, template)
    if not result.valid:
        print(validator.format_validation_result(result))
"""
```

#### Class Docstrings

```python
class StackCodeValidator:
    """
    Validates stack code against template declarations.

    This class implements the template-first validation pattern described in
    Multi_Stack_Architecture.4.1.md. It ensures that stack TypeScript code
    matches the parameter declarations in the enhanced template.

    Architecture:
        - Extracts parameters from TypeScript code using ParameterExtractor
        - Compares extracted parameters with template declarations
        - Reports errors (violations) and warnings (inconsistencies)

    Attributes:
        None (stateless validator)

    Example:
        >>> validator = StackCodeValidator()
        >>> template = load_template("network")
        >>> result = validator.validate(Path("stacks/network"), template)
        >>> if not result.valid:
        ...     print(result.get_error_count(), "errors found")
    """
```

#### Method Docstrings

```python
def validate(
    self,
    stack_dir: Path,
    template_data: Dict,
    stack_name: Optional[str] = None,
    strict: bool = False
) -> ValidationResult:
    """
    Validate stack code against template.

    Extracts parameters from the stack's TypeScript code and compares them
    with the template's parameter declarations. Reports errors for violations
    and warnings for inconsistencies.

    Args:
        stack_dir: Path to stack directory containing TypeScript code
        template_data: Enhanced template data with parameter declarations
        stack_name: Optional stack name (defaults to directory name)
        strict: If True, treat warnings as errors (stricter validation)

    Returns:
        ValidationResult containing validation status, errors, and warnings

    Raises:
        Exception: If parameter extraction fails or stack directory not found

    Behavior:
        - Undeclared inputs (used in code but not in template): ERROR
        - Unused inputs (in template but not in code):
            * strict=False: WARNING
            * strict=True: ERROR
        - Missing outputs (in template but not exported): ERROR
        - Extra outputs (exported but not in template):
            * strict=False: WARNING
            * strict=True: ERROR
        - Type mismatches: WARNING (always, even in strict mode)

    Example:
        >>> validator = StackCodeValidator()
        >>> template = {"parameters": {"inputs": {...}, "outputs": {...}}}
        >>> result = validator.validate(Path("stacks/network"), template)
        >>> if not result.valid:
        ...     for error in result.errors:
        ...         print(f"Error: {error.message}")

    Reference:
        Multi_Stack_Architecture.4.1.md section 15 (Validation)
    """
```

### Inline Comments

**When to Comment:**
- Complex algorithms
- Non-obvious logic
- Workarounds or hacks
- References to documentation or issues

**When NOT to Comment:**
- Obvious code
- Redundant with docstrings
- Explaining bad code (refactor instead)

**Good Comments:**
```python
# Use Kahn's algorithm for topological sort to calculate layers
# Reference: Multi_Stack_Architecture.4.1.md section 9.2
layers = self._topological_sort(dependency_graph)

# Type mismatches generate warnings, not errors, because TypeScript
# type inference may legitimately differ from template declarations
# See: GitHub issue #123
if code_type != template_type:
    result.add_warning(...)

# WORKAROUND: Pulumi state queries require exact stack name format
# TODO: Remove when pulumi/pulumi#1234 is resolved
stack_name = f"{project}-{env}-{stack}"
```

**Bad Comments:**
```python
# Increment counter
counter += 1

# Loop through items
for item in items:
    # Process item
    process(item)

# This code is confusing [← REFACTOR THE CODE!]
weird_logic()
```

### Documentation Updates

**When Code Changes Require Doc Updates:**

1. **New Feature Added:**
   - Add to Multi_Stack_Architecture.4.1.md
   - Update CLI_Commands_Reference if CLI command
   - Add examples to guides

2. **Behavior Changed:**
   - Update all docs mentioning the behavior
   - Add note about version when changed
   - Update examples

3. **API Changed:**
   - Update API_Reference_v4.1.md
   - Update code examples
   - Add migration guide if breaking

4. **Bug Fixed:**
   - Update docs if they described wrong behavior
   - Add to changelog
   - Note any behavior changes

**Documentation Checklist:**
- [ ] Architecture docs updated if design changed
- [ ] API reference updated if signatures changed
- [ ] Examples updated if usage changed
- [ ] Guides updated if workflows changed
- [ ] Changelog entry added
- [ ] Version notes added if breaking change

---

## Code Review Checklist

### Architecture Compliance

- [ ] **Follows documented architecture**
  - Respects core/CLI separation
  - Uses appropriate module for functionality
  - Follows design patterns from docs

- [ ] **Matches design principles**
  - Template-first approach followed
  - Dependency-driven design
  - Layer-based execution respected

- [ ] **Consistent with existing code**
  - Uses existing data structures
  - Follows existing API patterns
  - Matches error handling style

### Code Quality

- [ ] **Well-structured**
  - Functions have single responsibility
  - Classes have clear purpose
  - Modules are cohesive

- [ ] **Type hints used**
  - All function parameters typed
  - Return types specified
  - Complex types properly defined

- [ ] **Error handling**
  - Errors caught appropriately
  - Error messages are clear
  - Follows existing error patterns

- [ ] **Readable**
  - Clear variable names
  - Logical flow
  - Not overly complex

### Testing

- [ ] **Tests exist**
  - Unit tests for new functions
  - Integration tests for workflows
  - Edge cases covered

- [ ] **Tests pass**
  - All new tests pass
  - No existing tests broken
  - No regressions introduced

- [ ] **Tests match documentation**
  - Test documented behavior
  - Cover expected use cases
  - Verify error handling

### Documentation

- [ ] **Code documented**
  - Module docstring present
  - Class docstrings present
  - Method docstrings complete

- [ ] **Complex logic explained**
  - Non-obvious code has comments
  - References to docs/issues included
  - Workarounds noted

- [ ] **Docs updated**
  - Architecture docs if needed
  - API reference if needed
  - Guides if needed

### Dual Authority Compliance

- [ ] **Respects documentation**
  - Implements documented behavior
  - Doesn't contradict docs without reason
  - Design intent preserved

- [ ] **Updates both code and docs**
  - Behavior changes update docs
  - New features add to docs
  - No conflicts left unresolved

- [ ] **Maintains patterns**
  - Follows patterns from docs
  - Uses patterns from code
  - Both sources remain authoritative

### Example Code Review Comments

**Good Review Comment:**
```
📚 Architecture Alignment:
This follows the template-first pattern from Multi_Stack_Architecture.4.1.md
section 15. The ValidationResult return type matches the existing pattern.

✅ Looks good!

Minor suggestion: Add a reference to the architecture doc in the docstring
so future developers understand the design intent.
```

**Another Good Review Comment:**
```
⚠️ Potential Doc-Code Conflict:
This changes validation behavior from warning to error for type mismatches.
However, Multi_Stack_Architecture.4.1.md section 15.3 says type mismatches
should be warnings.

Questions:
1. Is this intentional? If so, please update the docs.
2. Or should this remain a warning per the architecture?

See: Governance_and_Gap_Analysis_v4.1.md for conflict resolution process.
```

---

## Common Development Scenarios

### Scenario 1: Adding a New Validation Rule

**Task:** Add validation that stack names follow naming convention

**Steps:**

1. **Understand from docs:**
   ```
   Read: Multi_Stack_Architecture.4.1.md section 15 (Validation)
   Learn: How validation is structured
   Pattern: ValidationResult with errors/warnings
   ```

2. **Review existing code:**
   ```python
   # File: cloud_core/validation/stack_code_validator.py
   # See how existing validation works
   # Note: Returns ValidationResult
   ```

3. **Write test:**
   ```python
   # File: tests/test_validation/test_stack_naming.py

   def test_stack_name_validation():
       """Test stack names follow convention"""
       validator = StackNamingValidator()

       # Valid names
       assert validator.validate("network").valid
       assert validator.validate("database-rds").valid

       # Invalid names
       result = validator.validate("Network")  # Capital letter
       assert not result.valid
       assert "lowercase" in result.errors[0].message

       result = validator.validate("my_stack")  # Underscore
       assert not result.valid
       assert "hyphen" in result.errors[0].message
   ```

4. **Implement:**
   ```python
   # File: cloud_core/validation/stack_naming_validator.py

   """
   Stack Naming Validator

   Validates stack names follow the platform naming convention.

   Convention:
   - Lowercase letters
   - Hyphens for word separation (not underscores)
   - No spaces or special characters
   - Length: 3-50 characters

   Reference: Multi_Stack_Architecture.4.1.md section 3.2
   """

   import re
   from .stack_code_validator import ValidationResult

   class StackNamingValidator:
       """Validates stack names follow naming convention"""

       PATTERN = r'^[a-z][a-z0-9-]{2,49}$'

       def validate(self, stack_name: str) -> ValidationResult:
           """
           Validate stack name follows convention.

           Args:
               stack_name: Stack name to validate

           Returns:
               ValidationResult with errors if invalid
           """
           result = ValidationResult(valid=True, stack_name=stack_name)

           if not re.match(self.PATTERN, stack_name):
               result.add_error(
                   "Stack name must be lowercase letters, numbers, and "
                   "hyphens only, 3-50 characters, starting with a letter"
               )

           return result
   ```

5. **Integrate:**
   ```python
   # Add to existing validation workflows
   # Update CLI validate command to include naming check
   ```

6. **Update docs:**
   ```markdown
   # In Multi_Stack_Architecture.4.1.md section 3.2:

   ### Stack Naming Convention

   Stack names must follow these rules:
   - Lowercase letters only (a-z)
   - Numbers allowed (0-9)
   - Hyphens for word separation (-)
   - No underscores, spaces, or special characters
   - Length: 3-50 characters
   - Must start with a letter

   Valid examples: `network`, `database-rds`, `compute-ecs-api`
   Invalid examples: `Network` (capital), `my_stack` (underscore)

   **Validation:** The `StackNamingValidator` enforces this convention
   during stack registration and validation.
   ```

### Scenario 2: Implementing a New CLI Command

**Task:** Add `cloud compare-stacks` command

**Steps:**

1. **Understand CLI structure:**
   ```
   Read: CLI_Commands_Reference.3.1.md
   Review: tools/cli/src/cloud_cli/commands/*.py
   Pattern: Click-based command with validation
   ```

2. **Design command:**
   ```bash
   # Usage:
   cloud compare-stacks <stack1> <stack2> [--show-diff]

   # Purpose: Compare two stacks' configurations
   # Output: Differences in parameters, dependencies, etc.
   ```

3. **Write test:**
   ```python
   # File: tools/cli/tests/test_commands/test_compare_cmd.py

   from click.testing import CliRunner
   from cloud_cli.main import cli

   def test_compare_stacks_command():
       """Test compare-stacks command"""
       runner = CliRunner()

       # Setup: Create two stacks with different configs

       # Execute
       result = runner.invoke(cli, [
           'compare-stacks', 'stack1', 'stack2', '--show-diff'
       ])

       # Verify
       assert result.exit_code == 0
       assert "Differences found" in result.output
   ```

4. **Implement:**
   ```python
   # File: tools/cli/src/cloud_cli/commands/compare_cmd.py

   """
   Stack Comparison Commands

   CLI commands for comparing stacks.

   Reference: Multi_Stack_Architecture.4.1.md
   """

   import click
   from pathlib import Path
   from cloud_core.templates.stack_template_manager import StackTemplateManager

   @click.command()
   @click.argument('stack1')
   @click.argument('stack2')
   @click.option('--show-diff', is_flag=True,
                 help='Show detailed differences')
   def compare_stacks(stack1: str, stack2: str, show_diff: bool):
       """Compare two stacks' configurations"""

       template_manager = StackTemplateManager()

       # Load templates
       try:
           tmpl1 = template_manager.load_template(stack1)
           tmpl2 = template_manager.load_template(stack2)
       except Exception as e:
           click.echo(f"Error loading templates: {e}", err=True)
           raise click.Abort()

       # Compare
       differences = _compare_templates(tmpl1, tmpl2)

       # Output
       if not differences:
           click.echo(f"✓ {stack1} and {stack2} are identical")
       else:
           click.echo(f"Differences found between {stack1} and {stack2}:")
           _print_differences(differences, show_diff)

   def _compare_templates(tmpl1: dict, tmpl2: dict) -> dict:
       """Compare two templates"""
       # Implementation...
       pass

   def _print_differences(differences: dict, detailed: bool):
       """Print differences"""
       # Implementation...
       pass
   ```

5. **Register command:**
   ```python
   # File: tools/cli/src/cloud_cli/main.py

   from .commands.compare_cmd import compare_stacks

   cli.add_command(compare_stacks)
   ```

6. **Update docs:**
   ```markdown
   # Add to CLI_Commands_Reference.3.1.md:

   ### compare-stacks

   Compare two stacks' configurations.

   **Usage:**
   ```bash
   cloud compare-stacks <stack1> <stack2> [--show-diff]
   ```

   **Arguments:**
   - `stack1`: First stack name
   - `stack2`: Second stack name

   **Options:**
   - `--show-diff`: Show detailed differences (default: summary only)

   **Example:**
   ```bash
   $ cloud compare-stacks network database-rds --show-diff
   Differences found between network and database-rds:

   Dependencies:
     network: []
     database-rds: [network, security]

   Inputs:
     Only in network: vpcCidr, availabilityZones
     Only in database-rds: instanceClass, allocatedStorage
   ```
   ```

### Scenario 3: Handling a Doc-Code Conflict

**Situation:** Documentation says X, code implements Y

**Example:** Docs say "unused inputs are errors", code generates warnings

**Resolution:**

1. **Document the conflict:**
   ```markdown
   # Create issue: docs/issues/conflict-unused-inputs.md

   ## Conflict: Unused Input Handling

   **Documentation says:**
   Multi_Stack_Architecture.4.1.md section 15:
   "Unused inputs (declared in template but not used in code) are errors"

   **Code implements:**
   stack_code_validator.py line 159:
   ```python
   if strict:
       result.add_error(...)
   else:
       result.add_warning(...)  # Warning in non-strict mode!
   ```

   **Tests expect:**
   test_stack_code_validator.py:
   ```python
   def test_validate_unused_input_non_strict():
       # Test expects warning, not error
       assert result.get_warning_count() == 1
   ```

   **Analysis:**
   Code intentionally generates warnings in non-strict mode.
   Tests validate this behavior (393+ passing tests).
   Docs were written before implementation details finalized.

   **Recommendation:**
   Update docs to match code (code is authoritative here).
   ```

2. **Determine resolution:**
   - Review design intent: Flexibility for unused inputs
   - Check tests: Tests expect warnings
   - Check git history: Intentional design decision
   - Decision: Code is correct, docs are outdated

3. **Update documentation:**
   ```markdown
   # Multi_Stack_Architecture.4.1.md section 15:

   ### Unused Input Validation

   When a parameter is declared in the template but not used in code:

   **Non-strict mode (default):**
   - Generates **WARNING**
   - Allows flexible templating (e.g., optional features)
   - Validation still passes

   **Strict mode:**
   - Generates **ERROR**
   - Enforces exact template-code match
   - Validation fails

   **Rationale:** Templates may declare optional parameters for
   flexibility. Non-strict mode allows this while warning developers.
   Strict mode enforces exact matching for production deployment.

   **Changed in v4.2:** Previous documentation incorrectly stated unused
   inputs were always errors. The implementation has always generated
   warnings in non-strict mode.
   ```

4. **Add tests if needed:**
   ```python
   # Verify tests cover both modes
   def test_unused_input_strict_vs_non_strict():
       """Document and test strict vs non-strict behavior"""
       # Non-strict: warning
       result = validator.validate(..., strict=False)
       assert result.valid == True  # Still valid!
       assert result.get_warning_count() == 1

       # Strict: error
       result = validator.validate(..., strict=True)
       assert result.valid == False  # Now invalid
       assert result.get_error_count() == 1
   ```

5. **Close issue:**
   ```markdown
   ## Resolution

   Updated Multi_Stack_Architecture.4.1.md section 15 to correctly
   document the strict vs non-strict behavior.

   Code behavior is correct and intentional. Documentation has been
   aligned with implementation.

   **Commit:** abc123 "docs: fix unused input validation description"
   ```

---

## Conclusion

### Key Takeaways

1. **Dual Authority Model:** Both docs and code are authoritative, each in their domain
2. **Start with Docs:** Understand architecture and design intent first
3. **Implement from Code:** Follow exact patterns from existing implementation
4. **Test Everything:** Validate both documented and actual behavior
5. **Keep Synchronized:** Update both docs and code when making changes
6. **Resolve Conflicts:** Never leave docs and code in disagreement

### Quick Reference

**When to use what:**
- **Design:** Documentation
- **Implementation:** Code + Documentation
- **Debugging:** Code + Documentation
- **Testing:** Code patterns, documented behavior
- **Learning:** Documentation → Code
- **Contributing:** Follow this guide

**Essential documents:**
- Architecture: Multi_Stack_Architecture.4.1.md
- This guide: DEVELOPMENT_GUIDE_v4.1.md
- API Reference: API_Reference_v4.1.md
- Governance: Governance_and_Gap_Analysis_v4.1.md

### Getting Help

**Questions about architecture?**
→ Read Multi_Stack_Architecture.4.1.md

**Questions about implementation?**
→ Read the code, check tests

**Found a conflict?**
→ Follow conflict resolution process

**Need clarification?**
→ Ask in team chat, reference this guide

---

**Document Version:** 4.1
**Last Updated:** 2025-10-29
**Status:** Authoritative Guide
**Next Review:** Quarterly

**Maintainers:** Platform Architecture Team
**Questions:** Contact platform-team@example.com or open GitHub issue
