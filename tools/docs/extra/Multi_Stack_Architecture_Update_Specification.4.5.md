# Multi_Stack_Architecture - Update Specification (v4.5)

**Date:** 2025-10-30
**Purpose:** Complete specification for architecture document updates through v4.5
**Status:** Implementation Guide

---

## Overview

This document provides complete specifications for updating the Multi_Stack_Architecture document through multiple versions:
- v3.1 to v4.1: Major Python implementation and enhanced template system
- v4.1 to v4.5: Dynamic Pulumi.yaml management and template defaults

---

## Updates from v4.1 to v4.5

### Overview of v4.5 Changes

Version 4.5 introduces a critical enhancement to solve the Pulumi project naming incompatibility discovered in v4.1 implementation.

### 1. Dynamic Pulumi.yaml Management (New Major Feature)

**Problem Statement:**
- Architecture specifies stacks grouped by deployment project in Pulumi Cloud
- Pulumi validates project name against `Pulumi.yaml` in stack directory
- Stack directories have hardcoded names (network, security, etc.)
- Creates incompatibility between architecture intent and Pulumi requirements

**Solution:**
- Context manager pattern for temporary Pulumi.yaml modification
- Automatic backup before operations
- Dynamic generation with deployment project name
- Guaranteed restoration after operations

**Required Documentation Updates:**

1. **Add New "What's New in v4.5" Section:**
   ```markdown
   ## What's New in v4.5

   ### Dynamic Pulumi.yaml Management
   - Problem: Pulumi project naming incompatibility
   - Solution: Context manager with backup/restore
   - Implementation: PulumiWrapper.deployment_context()
   - Benefits: Correct stack organization, concurrent safety
   ```

2. **Add Detailed Implementation Section:**
   ```markdown
   ## Dynamic Pulumi.yaml Management (v4.5+)

   ### The Problem
   [Explain incompatibility between architecture and Pulumi validation]

   ### The Solution
   [Describe context manager approach]

   ### Implementation Details
   - Backup Process
   - Generation Process
   - Restoration Process
   - Usage Pattern

   ### Benefits
   - Correct Pulumi Cloud organization
   - Shared stack directories (99.9% savings)
   - Concurrent deployment support
   - Backward compatibility
   ```

3. **Update Key Capabilities in Executive Summary:**
   ```markdown
   **Dynamic Pulumi.yaml Management (NEW in v4.5)**
   - Context manager pattern for temporary modification
   - Deployment-specific project naming
   - Guaranteed restoration with retry logic
   - Support for concurrent deployments
   ```

4. **Update References to Pulumi Stack Naming:**
   ```markdown
   OLD: Stacks organized as {pulumiOrg}/{stack-type}/{deployment-stack-env}
   NEW: Stacks organized as {pulumiOrg}/{project}/{deployment-stack-env}
   Note: Requires Dynamic Pulumi.yaml Management (v4.5+)
   ```

### 2. Template Defaults Change

**Change:** All stacks disabled by default in deployment templates

**Impact:**
- Explicit opt-in model for stack deployment
- Better production safety
- Prevents accidental infrastructure deployment

**Required Documentation Updates:**

1. **Update Template System Section:**
   ```markdown
   ### Default Stack Enablement (v4.5)

   All stacks are disabled by default in templates:

   ```yaml
   stacks:
     network:
       enabled: false  # Changed from true in v4.1
   ```

   Users must explicitly enable stacks:
   - Via CLI flags: --enable-stack network
   - Via manifest edit: enabled: true
   ```

2. **Update "What's New in v4.5" Section:**
   ```markdown
   ### Template Changes in v4.5
   - All stacks disabled by default
   - Explicit opt-in model
   - Better production safety
   ```

### 3. Version References Throughout Document

**Update all version references:**
```
OLD: Cloud Infrastructure Orchestration Platform v4.1
NEW: Cloud Infrastructure Orchestration Platform v4.5

OLD: Version: 4.1
NEW: Version: 4.5

OLD: Platform: cloud-0.7
KEEP: Platform: cloud-0.7 (unchanged)

OLD: Date: 2025-10-29
NEW: Date: 2025-10-30
```

### 4. Alignment References

**Update alignment statement:**
```markdown
**Alignment with Authoritative Documents:**
This document (v4.5) is fully aligned with and extends:
- Complete_Stack_Management_Guide_v4.md
- Stack_Parameters_and_Registration_Guide_v4.md
- Complete_Guide_Templates_Stacks_Config_and_Registration_v4.md
- Addendum_Dynamic_Pulumi_YAML_Implementation.4.1.md (NEW in v4.5)
```

### 5. File Naming

**Rename file:**
```
OLD: Multi_Stack_Architecture.4.1.md
NEW: Multi_Stack_Architecture.4.5.md
```

---

## Updates from v3.1 to v4.1

This section retained from original specification...

---

## Critical Changes Required

### 1. Implementation Language Update (Throughout Document)

**Current (v3.1):** References TypeScript CLI implementation
**Required (v4.1):** Update to Python CLI implementation

**Sections to Update:**
- Executive Summary → CLI tool description
- Architecture Overview → System Components diagram
- CLI Tool Specification (entire section)
- All code examples
- All command examples

**Changes:**
```
OLD: TypeScript CLI at tools/cli/src/index.ts
NEW: Python CLI at tools/cli/src/cloud_cli/main.py

OLD: Commands like "cloud init"
NEW: Commands like "cloud-cli init" or "python -m cloud_cli.main init"

OLD: TypeScript code examples
NEW: Python code examples
```

---

### 2. Core/CLI Architecture Split (New Section)

**Add New Section After "Architecture Overview":**

```markdown
## Core/CLI Architecture (NEW in v4)

### Two-Tier Design

The platform uses a clean separation between business logic and user interface:

**tools/core/ - Business Logic Library (cloud_core)**
- Python package with core functionality
- Independent of CLI, can be used by API or other interfaces
- Modules:
  - deployment/ - Deployment management
  - orchestrator/ - Dependency resolution, layer calculation, execution
  - runtime/ - Placeholder resolution, stack references
  - templates/ - Enhanced template system
  - validation/ - Template-first validation
  - pulumi/ - Pulumi wrapper
  - utils/ - Utilities

**tools/cli/ - User Interface (cloud_cli)**
- Python package providing CLI commands
- Thin wrapper around cloud_core
- Modules:
  - commands/ - CLI command handlers
  - parser/ - Auto-extraction system (ParameterExtractor, TypeScriptParser)
  - main.py - Entry point

### Benefits of Separation
- Modularity and reusability
- Easier testing (business logic isolated)
- Multiple interfaces possible (CLI, API, SDK)
- Clear separation of concerns
```

---

### 3. Enhanced Template System (Major Update)

**Update "Template System" Section:**

Add comprehensive documentation of enhanced v4 template format:

```markdown
### Enhanced Template Format (v4.0)

Stack templates now include structured parameter declarations:

**parameters.inputs** - Input parameters
- type: string, number, boolean, array, object
- required: true/false
- default: default value
- description: parameter description

**parameters.outputs** - Output declarations
- type: output type
- description: output description

**Example Enhanced Template:**
```yaml
name: network
version: "1.0"
description: "VPC and networking infrastructure"

parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for VPC"

    availabilityZones:
      type: number
      required: true
      default: 3
      description: "Number of AZs to span"

    enableNatGateway:
      type: boolean
      required: false
      default: true
      description: "Enable NAT gateway for private subnets"

  outputs:
    vpcId:
      type: string
      description: "VPC ID for cross-stack references"

    privateSubnetIds:
      type: array
      description: "Private subnet IDs for RDS/ECS"

    publicSubnetIds:
      type: array
      description: "Public subnet IDs for ALB"

dependencies: []
layer: 1
```

### Template Validation

Templates are validated for:
- Schema correctness
- Type consistency
- Required fields present
- Valid dependency references
```

---

### 4. Auto-Extraction System (New Section)

**Add New Section: "Auto-Extraction System"**

```markdown
## Auto-Extraction System (NEW in v4)

### Overview

The auto-extraction system automatically generates stack templates from TypeScript stack code, eliminating manual template creation.

### Components

**ParameterExtractor (cloud_core.parser.parameter_extractor)**
- Scans TypeScript stack code
- Identifies pulumi.Config() usage
- Extracts parameter names, types, defaults
- Generates template structure

**TypeScriptParser (cloud_core.parser.typescript_parser)**
- Parses TypeScript AST
- Finds Config.require(), Config.get(), Config.requireSecret()
- Extracts output exports
- Determines parameter types from usage

### Workflow

1. **Developer writes stack code:**
```typescript
// stacks/network/index.ts
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const vpcCidr = config.require("vpcCidr");
const azCount = config.requireNumber("availabilityZones");
const enableNat = config.getBoolean("enableNatGateway") ?? true;

// ... stack implementation ...

export const vpcId = vpc.id;
export const privateSubnetIds = privateSubnets.map(s => s.id);
```

2. **Run auto-extraction:**
```bash
cloud-cli register-stack network --auto-extract
```

3. **System extracts parameters:**
- Found input: vpcCidr (string, required)
- Found input: availabilityZones (number, required)
- Found input: enableNatGateway (boolean, optional, default: true)
- Found output: vpcId (string)
- Found output: privateSubnetIds (array)

4. **Template generated:**
```yaml
parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
    availabilityZones:
      type: number
      required: true
    enableNatGateway:
      type: boolean
      required: false
      default: true
  outputs:
    vpcId:
      type: string
    privateSubnetIds:
      type: array
```

5. **User reviews and confirms**

6. **Template saved to tools/templates/config/network.yaml**

### Commands

```bash
# Auto-extract and register
cloud-cli register-stack <stack-name> --auto-extract

# Specify defaults file
cloud-cli register-stack <stack-name> --defaults-file ./defaults.yaml

# Interactive registration
cloud-cli register-stack <stack-name> --interactive
```
```

---

### 5. Template-First Validation (New Section)

**Add New Section: "Template-First Validation"**

```markdown
## Template-First Validation (NEW in v4)

### Overview

Template-first validation ensures stack code matches its template declaration, preventing configuration drift and deployment errors.

### StackCodeValidator

**Location:** cloud_core.validation.stack_code_validator

**Validation Rules:**

1. **Input Parameters**
   - All template inputs must have Config.get() or Config.require() in code
   - All Config calls in code must be declared in template
   - Required parameters must use Config.require()
   - Optional parameters must use Config.get() with defaults

2. **Output Parameters**
   - All template outputs must be exported in code
   - All exports in code should be declared in template (warning if not)
   - Export types must match template declarations

3. **Type Consistency**
   - String parameters use Config.require() or Config.get()
   - Number parameters use Config.requireNumber() or Config.getNumber()
   - Boolean parameters use Config.requireBoolean() or Config.getBoolean()
   - Arrays/objects use appropriate methods

### Validation Modes

**Normal Mode:**
- Validates required parameters
- Warns on mismatches
- Allows deployment to proceed

**Strict Mode:**
- All validations must pass
- No warnings allowed
- Blocks deployment on any mismatch

### Commands

```bash
# Validate stack code
cloud-cli validate-stack <stack-name>

# Strict validation
cloud-cli validate-stack <stack-name> --strict

# Validate all stacks
cloud-cli validate-stack --all --strict
```

### Example Validation Output

```
Validating stack: network
✓ Template loaded: tools/templates/config/network.yaml
✓ Stack code loaded: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
⚠ enableNatGateway: declared in template, not found in code

Output Parameters:
✓ vpcId: declared in template, exported in code
✓ privateSubnetIds: declared in template, exported in code
✓ publicSubnetIds: declared in template, exported in code

Result: PASSED with 1 warning
```
```

---

### 6. Configuration Management Updates

**Update "Configuration Management" Section:**

**Change from v3.1:**
- Update manifest format from JSON to YAML
- Update config location to config/ subdirectory
- Update config format to Pulumi native
- Update placeholder syntax to ${...} or {{...}}

**Add subsections:**
- Pulumi Native Config Format
- Config Generation Process
- Runtime Resolution Process

**Example:**
```markdown
### Pulumi Native Config Format

Configuration files use Pulumi's native key-value format:

**Format:** `stackname:key: "value"`

**Example (config/network.dev.yaml):**
```yaml
network:deploymentId: "D1TEST1"
network:organization: "TestOrg"
network:vpcCidr: "10.0.0.0/16"
network:availabilityZones: "3"
aws:region: "us-east-1"
```

**Rules:**
- All keys prefixed with stack name
- All values are strings (Pulumi requirement)
- Complex types serialized as JSON strings
- AWS provider config: aws:region
```

---

### 7. Cross-Stack Dependencies (Major Expansion)

**Add Comprehensive Section: "Cross-Stack Dependencies"**

Use the network → database example from v4 authoritative documents:

```markdown
## Cross-Stack Dependencies (Complete Workflow)

### Overview

Cross-stack dependencies allow stacks to reference outputs from other stacks using placeholders in the deployment manifest.

### Example: Network → Database

#### 1. Network Stack Template Declaration

**Template (tools/templates/config/network.yaml):**
```yaml
parameters:
  outputs:
    privateSubnetIds:
      type: array
      description: "Private subnet IDs for RDS"
```

#### 2. Network Stack Implementation

**Code (stacks/network/index.ts):**
```typescript
// Create private subnets
const privateSubnets = [];
for (let i = 0; i < azCount; i++) {
    const subnet = new aws.ec2.Subnet(`private-${i}`, {
        vpcId: vpc.id,
        cidrBlock: `10.0.${i + 10}.0/24`,
        availabilityZone: azs[i],
        tags: { Name: `private-${i}` }
    });
    privateSubnets.push(subnet);
}

// Export for cross-stack references
export const privateSubnetIds = privateSubnets.map(s => s.id);
```

#### 3. Database Stack Template Declaration

**Template (tools/templates/config/database-rds.yaml):**
```yaml
parameters:
  inputs:
    subnets:
      type: array
      required: true
      description: "Subnet IDs for RDS subnet group"

dependencies:
  - network
```

#### 4. Database Stack Implementation

**Code (stacks/database-rds/index.ts):**
```typescript
const config = new pulumi.Config();
const subnetsJson = config.require("subnets");
const subnetIds = JSON.parse(subnetsJson); // Array of subnet IDs

const subnetGroup = new aws.rds.SubnetGroup("db-subnet-group", {
    subnetIds: subnetIds,
    tags: { Name: "db-subnet-group" }
});
```

#### 5. Deployment Manifest

**Manifest (deploy/D1TEST1/deployment-manifest.yaml):**
```yaml
stacks:
  network:
    enabled: true
    config:
      vpcCidr: "10.0.0.0/16"
      availabilityZones: 3

  database-rds:
    enabled: true
    dependencies:
      - network
    config:
      subnets: "${network.privateSubnetIds}"  # Cross-stack reference
```

#### 6. Runtime Resolution

**Process:**
1. Network stack deploys first (layer 1)
2. Outputs exported: privateSubnetIds = ["subnet-abc", "subnet-def"]
3. Database deployment begins (layer 3)
4. StackReferenceResolver queries network stack
5. Placeholder ${network.privateSubnetIds} resolved
6. Config generated with actual values

**Generated Config (config/database-rds.dev.yaml):**
```yaml
database-rds:subnets: '["subnet-abc123", "subnet-def456"]'
```

#### 7. Database Stack Deploys

Database stack receives resolved subnet IDs and creates resources.
```

---

### 8. Placeholder Syntax Update

**Update Throughout Document:**

**OLD (v3.1):**
```
{{TYPE:source:key}}
{{RUNTIME:network:vpcId}}
{{ENV:instanceType}}
```

**NEW (v4.1):**
```
${stack.output} or {{stack.output}}
${network.vpcId}
${network.privateSubnetIds}
```

**Simpler, more intuitive syntax**

---

### 9. DependencyResolver vs StackReferenceResolver Clarification

**Update Section on Dependency Resolution:**

**Clarify roles:**
- **DependencyResolver** - Builds dependency graph, calculates layers, detects cycles
- **StackReferenceResolver** - Reads Pulumi stack outputs for cross-stack references

**OLD (v3.1 - INCORRECT):**
"DependencyResolver reads stack outputs..."

**NEW (v4.1 - CORRECT):**
"DependencyResolver builds the dependency graph. StackReferenceResolver reads Pulumi stack outputs for placeholder resolution."

---

### 10. Stack Directory Structure Fix

**Update Stack Management Section:**

**OLD (v3.1 - INCORRECT):**
```
stacks/<name>/src/index.ts
```

**NEW (v4.1 - CORRECT):**
```
stacks/<name>/index.ts          # Main entry point at root
stacks/<name>/src/              # Optional component files
stacks/<name>/src/vpc.ts
stacks/<name>/src/subnets.ts
```

**Clarification:** index.ts is at stack root, not in src/

---

### 11. Code Examples Updates

**All Code Examples Must Be Updated:**

**TypeScript Examples:** Keep (for stack code)
**CLI Examples:** Update to Python

**OLD:**
```typescript
// CLI implementation
import { Command } from 'commander';
```

**NEW:**
```python
# CLI implementation
import typer
from cloud_core.deployment import DeploymentManager
```

---

### 12. Command Examples Updates

**Update ALL command examples:**

**OLD:**
```bash
cloud init D1BRV40 --org CompanyA --project ecommerce
```

**NEW:**
```bash
cloud-cli init D1BRV40 --org CompanyA --project ecommerce
# or
python -m cloud_cli.main init D1BRV40 --org CompanyA --project ecommerce
```

---

## Section-by-Section Update Requirements

### Executive Summary
- [ ] Update CLI description to Python
- [ ] Add core/CLI architecture mention
- [ ] Add enhanced template system
- [ ] Add auto-extraction system
- [ ] Add template-first validation

### Architecture Overview
- [ ] Update system components diagram
- [ ] Update data flow diagram
- [ ] Add core/CLI split

### What's New in v3.1 (Rename to "What's New in v4.1")
- [ ] Add new features from v4.0
- [ ] Update version references

### Core Concepts
- [ ] Update configuration tiers explanation
- [ ] Add enhanced template format
- [ ] Update placeholder syntax

### Directory Structure
- [ ] Reference Directory_Structure_Diagram.4.1.md
- [ ] Update core/CLI structure
- [ ] Fix stack directory structure (index.ts at root)

### Stack Management
- [ ] Update Pulumi.yaml section
- [ ] Fix stack code structure section
- [ ] Update stack registration section
- [ ] Add auto-extraction workflow

### Template System
- [ ] Add enhanced template format section
- [ ] Document parameters.inputs and parameters.outputs
- [ ] Add type system documentation
- [ ] Update examples

### Deployment Initialization
- [ ] Update manifest format (JSON → YAML)
- [ ] Update command examples

### Configuration Management
- [ ] Add Pulumi native format section
- [ ] Update config location (config/ subdirectory)
- [ ] Update placeholder syntax
- [ ] Add config generation process

### Runtime Value Resolution
- [ ] Update placeholder syntax throughout
- [ ] Add StackReferenceResolver documentation
- [ ] Clarify DependencyResolver role

### Deployment Orchestration
- [ ] Update orchestrator description
- [ ] Add layer calculator details
- [ ] Update execution flow

### CLI Tool Specification
- [ ] **Complete rewrite for Python**
- [ ] Update all command descriptions
- [ ] Update command syntax
- [ ] Add core module references

### Verification and Validation
- [ ] Add template-first validation section
- [ ] Add StackCodeValidator documentation
- [ ] Update validation workflow

### Implementation Phases
- [ ] Update to reflect v4 completion
- [ ] Reference v4 authoritative documents

---

## New Sections to Add

1. **Core/CLI Architecture** (after Architecture Overview)
2. **Auto-Extraction System** (after Stack Registration)
3. **Template-First Validation** (after Verification and Validation)
4. **Cross-Stack Dependencies Complete Workflow** (expand existing section)
5. **Enhanced Template Format Specification** (in Template System)

---

## References Throughout Document

**Update all references:**
- v3.1 → v4.1
- TypeScript CLI → Python CLI
- JSON manifest → YAML manifest
- {{TYPE:source:key}} → ${stack.output}
- Nested config YAML → Pulumi native format
- DependencyResolver reads outputs → StackReferenceResolver reads outputs

---

## Priority Order for Updates

1. **CRITICAL:** Implementation language (TypeScript → Python)
2. **CRITICAL:** Configuration format (JSON → YAML, config/ subdirectory, Pulumi format)
3. **HIGH:** Core/CLI architecture documentation
4. **HIGH:** Enhanced template system
5. **HIGH:** Auto-extraction system
6. **HIGH:** Template-first validation
7. **MEDIUM:** Cross-stack dependencies expansion
8. **MEDIUM:** Placeholder syntax updates
9. **LOW:** Minor corrections and clarifications

---

## Validation Checklist

After updates, verify:
- [ ] No references to TypeScript CLI remain
- [ ] All commands use Python syntax
- [ ] All config examples use Pulumi format
- [ ] All placeholders use ${...} or {{...}}
- [ ] Stack directory structure shows index.ts at root
- [ ] DependencyResolver vs StackReferenceResolver clarified
- [ ] Enhanced template format documented
- [ ] Auto-extraction system documented
- [ ] Template-first validation documented
- [ ] Cross-stack dependencies fully explained
- [ ] All version references updated to 4.1
- [ ] References to authoritative v4 documents added

---

## Estimated Changes

- **Lines to modify:** ~800+ lines
- **New content to add:** ~500+ lines
- **Total updated document:** ~3250 lines
- **New sections:** 5 major sections
- **Updated sections:** 15+ sections

---

**Document Version:** 1.0
**Created:** 2025-10-29
**Purpose:** Implementation guide for Multi_Stack_Architecture.4.1.md
**Status:** Ready for implementation
