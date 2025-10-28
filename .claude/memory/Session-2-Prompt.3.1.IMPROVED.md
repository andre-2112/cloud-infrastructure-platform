# Session 2 Prompt - Core Implementation (v3.1 IMPROVED)

**Session Type:** Core Platform Implementation
**Target:** Complete Tasks 5.1-5.10 (Implementation Only)
**Status:** Ready to Execute
**Expected Duration:** Full session (~80-100K tokens)
**Architecture Version:** 3.1 (with Pulumi state management updates)

**IMPORTANT CHANGES IN v3.1:**
- Pulumi Projects now represent business projects (not stacks)
- Stack naming: `<deployment-id>-<stack-name>-<environment>`
- All StackReference code must use new format
- Deployment directories: `<deployment-id>-<org>-<project>/`
- Manifest at deployment root (no src/ subdirectory)
- Template structure: `docs/`, `stack/`, `config/`, `default/`, `custom/`

---

## ⚠️ IMPORTANT: About Prompt-12

**Prompt-12 is a HISTORICAL REFERENCE document** showing the original task breakdown.

**All tasks have been extracted, updated, and incorporated into THIS document.**

**DO NOT use Prompt-12 as an execution guide:**
- ❌ References Architecture 3.0 (we're on 3.1)
- ❌ Uses outdated naming conventions (multi-stack, staging, etc.)
- ❌ Missing v3.1 Pulumi state management updates
- ❌ Less detailed than this document
- ❌ Incomplete path specifications

**✅ Use THIS document (Session-2-Prompt.3.1.IMPROVED.md) as the authoritative guide.**

Prompt-12 location (for reference only):
`/c/Users/Admin/Documents/Workspace/cloud/tools/docs/Prompt-12 - Implement Final Version.md`

---

## Context & Background

This is **Session 2 of 3** in a multi-session implementation strategy for Multi-Stack Architecture 3.1 (cloud-0.7 platform).

### Session Overview

- **Session 1 (COMPLETED):** Planning & All Documentation (16 documents)
- **Session 2 (THIS):** Core Implementation (directory, stacks, CLI, validation, templates)
- **Session 3 (FUTURE):** Advanced Features (REST API, WebSockets, Database planning)

### What Session 1 Delivered

**16 Complete Documents (v3.1):**
1. Multi_Stack_Architecture.3.1.md (main architecture)
2-4. CLI documents (full, testing, quick reference)
5-7. REST API documents (full, testing, quick reference)
8. Deployment Manifest Specification
9. Directory Structure Diagram
10-16. Seven addendum documents

**All documents located in:** `/c/Users/Admin/Documents/Workspace/cloud/tools/docs/`

### What Session 1 Did NOT Do (Intentionally)

**Session 1 was DOCUMENTATION ONLY:**
- ❌ Did NOT create directory structure
- ❌ Did NOT copy/migrate stacks
- ❌ Did NOT implement any code
- ❌ Did NOT create CLI tool

**These are all Session 2 tasks!**

### What This Session Must Accomplish

**Primary Goal:** Implement core platform functionality

**Deliverables:**
1. New directory structure created
2. All 16 stacks migrated and adjusted
3. CLI tool implemented (25+ commands)
4. Validation tools implemented
5. Generic templates created
6. Platform ready for deployment testing

---

## Pre-Session Verification (CRITICAL)

### Before Starting Session 2, Verify:

1. **✅ Session 1 Completed:**
   ```bash
   ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/docs/*.3.1.md | wc -l
   # Should return: 16
   ```

2. **✅ Source Files Exist (Pulumi-2):**
   ```bash
   ls -la /c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/ | head -20
   # Should show 16 stack directories
   ```

3. **✅ Working Directory:**
   ```bash
   cd /c/Users/Admin/Documents/Workspace
   pwd
   # Should show: /c/Users/Admin/Documents/Workspace
   ```

4. **✅ User Approval:**
   - All Session 1 documents reviewed
   - Architecture 3.1 approved
   - Ready to proceed with implementation

**If any verification fails, STOP and resolve before proceeding!**

---

## Working Directory Strategy

### Directory Context Throughout Session:

**Starting Point:**
```bash
cd /c/Users/Admin/Documents/Workspace
```

**Source Directory (OLD - Pulumi-2):**
```bash
SOURCE=/c/Users/Admin/Documents/Workspace/Pulumi-2
# Contains existing stacks to migrate
```

**Destination Directory (NEW - cloud):**
```bash
DEST=/c/Users/Admin/Documents/Workspace/cloud
# Will be created in this session
```

**All commands in this document use absolute paths for clarity.**

---

## Pre-Session Reading (CRITICAL)

### Must Read Before Starting:

1. **./cloud/tools/docs/Multi_Stack_Architecture.3.1.md**
   - **PRIMARY REFERENCE** for this session
   - Complete specification for implementation
   - Generated in Session 1

2. **./cloud/tools/docs/Directory_Structure_Diagram.3.1.md**
   - Authoritative directory structure
   - Reference for all path decisions

3. **./cloud/tools/docs/CLI_Commands_Reference.3.1.md**
   - Complete CLI specification
   - All commands to implement

4. **./cloud/tools/docs/Addendum_Platform_Code.3.1.md**
   - Code examples and patterns
   - Implementation guidance

5. **./cloud/tools/docs/Addendum_Verification_Architecture.3.1.md**
   - Validation tool specifications
   - Testing requirements

### Optional (Context Only):

6. **./cloud/tools/docs/Session-1-Prompt.md**
   - Context from previous session

7. **./cloud/tools/docs/Execution_Feasibility_Analysis.md**
   - Multi-session strategy rationale

8. **./cloud/tools/docs/Prompt-12 - Implement Final Version.md**
   - Historical reference only (superseded by this document)

---

## Session 2 Tasks (Implementation Only)

### Task 5.1: Implement Architecture 3.1 Core

**Objective:**
Systematically implement all aspects of Multi_Stack_Architecture.3.1 entirely.

**Scope:**
- All changes from Task 2 (already incorporated in Arch 3.1)
- Reuse existing Pulumi stack code (see 5.4)
- Follow Architecture 3.1 specifications exactly

---

### Task 5.2: Ensure Implementation Conformance

**Must implement:**
- ✅ New Directory Structure and Directory Names
- ✅ Minimal Pulumi Specification
- ✅ Multi-Environment Architecture
- ✅ Configuration Architecture (Tiers, Flow)
- ✅ Stack Registration Management
- ✅ Stack Creation (Flows and Features)
- ✅ Stack Dependencies and Resolution
- ✅ Stack configuration files (Pulumi configuration)
- ✅ Stack source code files (all Pulumi .ts code)
- ✅ Stack templates system
- ✅ Deployment flows and features
- ✅ Deployment Manifest
- ✅ Deployment configuration files
- ✅ Full Deployment Lifecycle support
- ✅ Runtime Resolution Process
- ✅ Orchestration Engine
- ✅ State Management
- ✅ Error Handling
- ✅ CLI (all commands and params)
- ✅ Verification and Validation tools for:
  - Configuration files
  - Pulumi code
  - CLI tool
- ✅ Monitoring and Logging tools

**Note:** REST API, Database, WebSockets are Session 3

---

### Task 5.3: Create New Directory Structure

**Create this structure:**

```bash
/c/Users/Admin/Documents/Workspace/cloud/
├── deploy/                          # Deployment instances
├── stacks/                          # Stack implementations
│   ├── network/
│   │   ├── docs/                    # Stack documentation
│   │   └── src/                     # Stack source code
│   │       ├── index.ts             # Main entry point
│   │       ├── Pulumi.yaml
│   │       ├── package.json
│   │       └── tsconfig.json
│   ├── security/
│   ├── dns/
│   ├── storage-s3/
│   ├── compute-ec2/
│   ├── compute-ecs/
│   ├── compute-lambda/
│   ├── data-rds/
│   ├── data-dynamodb/
│   ├── data-elasticache/
│   ├── messaging-sqs/
│   ├── messaging-sns/
│   ├── api-gateway/
│   ├── cdn-cloudfront/
│   ├── monitoring/
│   └── cicd-codepipeline/
└── tools/                           # Platform tools
    ├── api/                         # REST API (Session 3)
    ├── cli/                         # CLI tool
    │   ├── src/
    │   ├── commands/
    │   ├── lib/
    │   ├── package.json
    │   └── tsconfig.json
    ├── docs/                        # Platform documentation (already exists)
    │   ├── Multi_Stack_Architecture.3.1.md
    │   ├── CLI_Commands_Reference.3.1.md
    │   ├── REST_API_Documentation.3.1.md
    │   └── Addendum_*.md
    └── templates/
        ├── docs/                    # Stack Markdown templates
        │   ├── Stack_Prompt_Main.md.template
        │   ├── Stack_Definitions.md.template
        │   └── Stack_Resources.md.template
        ├── stack/                   # Stack Pulumi templates
        │   ├── index.ts.template
        │   ├── Pulumi.yaml.template
        │   ├── package.json.template
        │   └── tsconfig.json.template
        ├── config/                  # Stack YAML templates
        │   ├── network.yaml
        │   ├── security.yaml
        │   └── ... (16 stacks)
        ├── default/                 # Manifest templates
        │   ├── default.yaml
        │   ├── minimal.yaml
        │   └── microservices.yaml
        └── custom/                  # Custom templates
```

**Implementation:**
1. Create root: `/c/Users/Admin/Documents/Workspace/cloud/`
2. Create all subdirectories
3. Verify structure matches Architecture 3.1

---

### Task 5.4: Copy Existing Stacks and Adjust

**Source:** `/c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/<stack>/v2/`
**Destination:** `/c/Users/Admin/Documents/Workspace/cloud/stacks/<stack>/`

#### 5.4.1: Copy Stack Documents

**For each stack:**

**Source files:**
```
/c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/<stack>/v2/docs/
├── Stack_Prompt_Main.md
├── Stack_Prompt_Extra.md
├── Stack_Definitions.md
├── Stack_Resources.md
├── Stack_History_Errors.md
├── Stack_History_Fixes.md
└── Stack_History.md
```

**Destination:**
```
/c/Users/Admin/Documents/Workspace/cloud/stacks/<stack>/docs/
```

**Adjustments for EACH file:**
1. Read file content
2. Replace "multi-stack" → "cloud"
3. Replace "staging" → "stage"
4. Update directory paths:
   - `/Pulumi-2/aws/build/` → `/cloud/stacks/`
   - `./aws/build/` → `./cloud/stacks/`
   - `/admin/v2/` → `/cloud/tools/`
   - `./admin/v2/` → `./cloud/tools/`
   - `/resources/` → `/src/`
   - `resources/` → `src/`
5. Update references to Architecture 2.x → **3.1** (not 3.0)
6. Update stack naming references to v3.1 format:
   - OLD: `D1BRV40-dev` → NEW: `D1BRV40-network-dev`
7. Write to new location

**Stacks to process:** (16 total)
- network
- security
- dns
- storage-s3
- compute-ec2
- compute-ecs
- compute-lambda
- data-rds
- data-dynamodb
- data-elasticache
- messaging-sqs
- messaging-sns
- api-gateway
- cdn-cloudfront
- monitoring
- cicd-codepipeline

#### 5.4.2: Copy Stack Resources (Code)

**For each stack:**

**Source files:**
```
/c/Users/Admin/Documents/Workspace/Pulumi-2/aws/build/<stack>/v2/resources/
├── index.ts (or index.2.2.ts)
├── Pulumi.yaml
├── package.json
├── tsconfig.json
└── ... (other .ts files)
```

**Destination:**
```
/c/Users/Admin/Documents/Workspace/cloud/stacks/<stack>/src/
```

**Adjustments for EACH file:**

**For index.ts:**
1. If `index.2.2.ts` exists, rename to `index.ts`
2. Update imports:
   - Update any hardcoded paths
   - Update stack reference names if needed
3. Replace "multi-stack" → "cloud" in comments
4. Update StackReference naming (CRITICAL for v3.1):
   ```typescript
   // OLD (v2.3): `${orgName}/network/${environment}`
   // OLD (v3.0): `${deploymentId}-${environment}`
   // NEW (v3.1): `${orgName}/${projectName}/${deploymentId}-${stackName}-${environment}`

   // Example:
   // OLD: acme-corp/network/dev
   // NEW: acme-corp/ecommerce/D1BRV40-network-dev
   ```
5. Ensure DependencyResolver usage (from Arch 3.1)
6. Update Pulumi Project references to business project (not stack)

**For Pulumi.yaml:**
1. Update `name` field if needed
2. Ensure `main: index.ts` (not index.2.2.ts)
3. Minimal configuration (per Arch 3.1)
4. Example:
   ```yaml
   name: network
   runtime:
     name: nodejs
     options:
       typescript: true
   description: Network infrastructure stack
   main: index.ts
   ```

**For package.json:**
1. Update dependencies to latest versions
2. Update scripts if needed
3. Ensure consistency across stacks
4. Ensure version is 0.7.0 (platform version)

**For tsconfig.json:**
1. Standard TypeScript configuration
2. Ensure consistency across stacks

---

### Task 5.5: Consult Existing Documents (If Needed)

**Reference documents** (may contain outdated info):
- Multi_Stack_Architecture.2.2.md
- Prompt-9-1 - PULUMI_CONFIGURATION_QUESTIONS_ANSWERS.md
- Prompt-9-3 - PULUMI_CONFIGURATION_FINAL_SOLUTION.md
- Prompt-9-5 - DEPLOYMENT_INITIALIZATION_ANSWERS.md
- All Prompt-10 Response documents

**⚠️ WARNING:** These documents are OUTDATED. **Architecture 3.1 is authoritative.**

Use these ONLY if:
- You need historical context for a specific decision
- Architecture 3.1 doesn't provide enough detail on a legacy feature
- You're debugging an issue related to old code

---

### Task 5.6: Implement All CLI Commands

**Reference:** `/c/Users/Admin/Documents/Workspace/cloud/tools/docs/CLI_Commands_Reference.3.1.md`

**Structure:**
```
/c/Users/Admin/Documents/Workspace/cloud/tools/cli/
├── src/
│   ├── index.ts                     # Main CLI entry
│   ├── cli.ts                       # CLI setup (Commander.js)
│   └── config.ts                    # CLI configuration
├── commands/
│   ├── init.ts                      # cloud init
│   ├── deploy.ts                    # cloud deploy
│   ├── deploy-stack.ts              # cloud deploy-stack
│   ├── destroy.ts                   # cloud destroy
│   ├── destroy-stack.ts             # cloud destroy-stack
│   ├── rollback.ts                  # cloud rollback
│   ├── enable-environment.ts        # cloud enable-environment
│   ├── disable-environment.ts       # cloud disable-environment
│   ├── list-environments.ts         # cloud list-environments
│   ├── register-stack.ts            # cloud register-stack
│   ├── update-stack.ts              # cloud update-stack
│   ├── unregister-stack.ts          # cloud unregister-stack
│   ├── list-stacks.ts               # cloud list-stacks
│   ├── validate-stack.ts            # cloud validate-stack
│   ├── list-templates.ts            # cloud list-templates
│   ├── show-template.ts             # cloud show-template
│   ├── create-template.ts           # cloud create-template
│   ├── update-template.ts           # cloud update-template
│   ├── validate-template.ts         # cloud validate-template
│   ├── validate.ts                  # cloud validate
│   ├── validate-dependencies.ts     # cloud validate-dependencies
│   ├── validate-aws.ts              # cloud validate-aws
│   ├── validate-pulumi.ts           # cloud validate-pulumi
│   ├── status.ts                    # cloud status
│   ├── list.ts                      # cloud list
│   ├── logs.ts                      # cloud logs
│   └── discover-resources.ts        # cloud discover-resources
├── lib/
│   ├── orchestrator.ts              # Deployment orchestrator
│   ├── dependency-resolver.ts       # Dependency resolution
│   ├── runtime-resolver.ts          # Runtime placeholder resolution
│   ├── config-manager.ts            # Configuration management
│   ├── state-manager.ts             # State management
│   ├── template-manager.ts          # Template management
│   ├── validators/                  # Validation utilities
│   │   ├── manifest-validator.ts
│   │   ├── dependency-validator.ts
│   │   ├── aws-validator.ts
│   │   └── pulumi-validator.ts
│   └── utils/
│       ├── deployment-id.ts         # Deployment ID generation
│       ├── logger.ts                # Logging utility
│       └── helpers.ts               # Helper functions
├── tests/
│   ├── unit/                        # Unit tests
│   └── integration/                 # Integration tests
├── package.json
├── tsconfig.json
└── README.md
```

**Implementation approach:**
1. Set up CLI framework (Commander.js)
2. Implement commands one by one
3. Reference CLI_Commands_Reference.3.1.md for specifications
4. Create unit tests for each command
5. Focus on core commands first:
   - init, deploy, validate, status, list

**IMPORTANT:** All CLI code must use v3.1 naming conventions:
- Stack names: `<deployment-id>-<stack-name>-<environment>`
- Deployment directories: `<deployment-id>-<org>-<project>/`
- Pulumi projects: Business project names (not stack names)

---

### Task 5.7: Implement Validation Tools

**Reference:** `/c/Users/Admin/Documents/Workspace/cloud/tools/docs/Addendum_Verification_Architecture.3.1.md`

**Validation Tools to Implement:**

1. **Manifest Validator**
   - Location: `/c/Users/Admin/Documents/Workspace/cloud/tools/cli/lib/validators/manifest-validator.ts`
   - Validates deployment manifest syntax and structure

2. **Dependency Validator**
   - Location: `/c/Users/Admin/Documents/Workspace/cloud/tools/cli/lib/validators/dependency-validator.ts`
   - Validates stack dependencies, detects circular refs

3. **AWS Credentials Validator**
   - Location: `/c/Users/Admin/Documents/Workspace/cloud/tools/cli/lib/validators/aws-validator.ts`
   - Validates AWS credentials and permissions

4. **Pulumi State Validator**
   - Location: `/c/Users/Admin/Documents/Workspace/cloud/tools/cli/lib/validators/pulumi-validator.ts`
   - Validates Pulumi Cloud state accessibility

5. **Runtime Placeholder Validator**
   - Location: `/c/Users/Admin/Documents/Workspace/cloud/tools/cli/lib/validators/placeholder-validator.ts`
   - Validates runtime placeholders can be resolved

6. **Template Validator**
   - Location: `/c/Users/Admin/Documents/Workspace/cloud/tools/cli/lib/validators/template-validator.ts`
   - Validates template definitions

**Implementation:**
- Create validator classes
- Implement validation logic per Arch 3.1
- Create unit tests
- Integrate with CLI commands (cloud validate-*)

**If validation cannot run:**
- Document testing procedures in Verification Addendum
- Provide manual validation steps

---

### Task 5.8: Generate Generic Document Templates

**Purpose:** Templates for creating new stacks

**Location:** `/c/Users/Admin/Documents/Workspace/cloud/tools/templates/docs/`

**Templates to create:**

1. **Stack_Prompt_Main.md.template**
   - Generic version of stack prompt
   - Based on existing stack prompts
   - Adjusted to Arch 3.1

2. **Stack_Prompt_Extra.md.template**
   - Additional prompt instructions template
   - For custom stack requirements

3. **Stack_Definitions.md.template**
   - Stack definitions template
   - Generated from prompt execution

4. **Stack_Resources.md.template**
   - Stack resources template
   - Generated from prompt execution

5. **Stack_History_Errors.md.template**
   - Error tracking template

6. **Stack_History_Fixes.md.template**
   - Fix tracking template

7. **Stack_History.md.template**
   - Full history template

**Implementation:**
1. Review existing stack docs (from 5.4.1)
2. Extract common patterns
3. Create generic versions with placeholders
4. Example placeholders: `{{STACK_NAME}}`, `{{DESCRIPTION}}`, etc.

---

### Task 5.9: Generate Generic Pulumi File Templates

**Purpose:** Templates for creating new stack implementations

**Location:** `/c/Users/Admin/Documents/Workspace/cloud/tools/templates/stack/`

**Note:** Directory is `stack/` (singular) not `stacks/` (plural)

**Templates to create:**

1. **Pulumi.yaml.template**
   ```yaml
   name: {{STACK_NAME}}
   runtime:
     name: nodejs
     options:
       typescript: true
   description: {{STACK_DESCRIPTION}}
   main: index.ts
   ```

2. **package.json.template**
   ```json
   {
     "name": "{{STACK_NAME}}",
     "version": "0.7.0",
     "main": "index.ts",
     "devDependencies": {
       "@types/node": "^20",
       "typescript": "^5.0"
     },
     "dependencies": {
       "@pulumi/pulumi": "^3.0",
       "@pulumi/aws": "^6.0"
     }
   }
   ```

3. **tsconfig.json.template**
   ```json
   {
     "compilerOptions": {
       "target": "ES2020",
       "module": "commonjs",
       "strict": true,
       "esModuleInterop": true,
       "skipLibCheck": true,
       "forceConsistentCasingInFileNames": true
     },
     "include": ["**/*.ts"],
     "exclude": ["node_modules"]
   }
   ```

4. **index.ts.template**
   ```typescript
   import * as pulumi from "@pulumi/pulumi";
   import * as aws from "@pulumi/aws";

   // Get configuration
   const config = new pulumi.Config();
   const deploymentId = config.require("deploymentId");
   const stackName = config.require("stackName");
   const environment = config.require("environment");

   // Stack implementation
   // TODO: Implement {{STACK_NAME}} resources

   // Export outputs
   export const stack = stackName;
   export const deployment = deploymentId;
   export const env = environment;
   ```

**Implementation:**
1. Review existing stack implementations (from 5.4.2)
2. Extract common patterns
3. Create generic templates with placeholders
4. Test templates can be used for new stacks

---

### Task 5.10: No Migration Needed

**Note:** No need to backup or migrate any deployments.

This task is a no-op. Just acknowledge and continue.

---

## Execution Instructions

### Step 1: Pre-Session Verification

Run all checks from "Pre-Session Verification" section above.

**If any check fails, STOP and resolve!**

### Step 2: Create Directory Structure (Task 5.3)

```bash
# Start from Workspace root
cd /c/Users/Admin/Documents/Workspace

# Create root
mkdir -p cloud

# Create main structure
mkdir -p cloud/{deploy,stacks,tools}

# Create tools structure
mkdir -p cloud/tools/{api,cli,docs,templates}

# Create templates structure (CRITICAL: correct subdirectory names)
mkdir -p cloud/tools/templates/{docs,stack,config,default,custom}

# Create CLI structure
mkdir -p cloud/tools/cli/{src,commands,lib,tests}
mkdir -p cloud/tools/cli/lib/{validators,utils}

# Verify structure
ls -la cloud/
ls -la cloud/tools/
ls -la cloud/tools/templates/
```

**Expected output:**
```
cloud/
├── deploy/
├── stacks/
└── tools/
    ├── api/
    ├── cli/
    ├── docs/  (already has 16 .3.1.md files)
    └── templates/
        ├── config/   (NOT "stacks")
        ├── custom/
        ├── default/
        ├── docs/
        └── stack/    (NOT "stacks", singular)
```

### Step 3: Verify Documents Already in Place

```bash
# Session 1 already placed documents here
ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/docs/*.3.1.md | wc -l
# Should show: 16
```

**No copying needed - documents are already in place!**

### Step 4: Create Stack Structure

```bash
cd /c/Users/Admin/Documents/Workspace

# Create all 16 stack directories
for stack in network security dns storage-s3 compute-ec2 compute-ecs compute-lambda \
             data-rds data-dynamodb data-elasticache messaging-sqs messaging-sns \
             api-gateway cdn-cloudfront monitoring cicd-codepipeline; do
    mkdir -p cloud/stacks/$stack/{docs,src}
done

# Verify
ls -la cloud/stacks/ | wc -l
# Should show: 18 (16 stacks + . + ..)
```

### Step 5: Copy and Adjust Stacks (Task 5.4)

**For each stack (16 total):**

**Define paths:**
```bash
cd /c/Users/Admin/Documents/Workspace

SOURCE_ROOT=/c/Users/Admin/Documents/Workspace/Pulumi-2
DEST_ROOT=/c/Users/Admin/Documents/Workspace/cloud
```

**Process systematically:**

1. **Copy docs:** (5.4.1)
   ```bash
   # Example for network stack
   STACK=network

   # Copy all docs
   cp -r $SOURCE_ROOT/aws/build/$STACK/v2/docs/* \
         $DEST_ROOT/stacks/$STACK/docs/

   # Now adjust each file (read, replace, write)
   # - Replace "multi-stack" → "cloud"
   # - Replace "staging" → "stage"
   # - Update paths
   # - Update architecture references to 3.1
   ```

2. **Copy src:** (5.4.2)
   ```bash
   # Copy all resources to src
   cp -r $SOURCE_ROOT/aws/build/$STACK/v2/resources/* \
         $DEST_ROOT/stacks/$STACK/src/

   # Rename index.2.2.ts if exists
   if [ -f $DEST_ROOT/stacks/$STACK/src/index.2.2.ts ]; then
       mv $DEST_ROOT/stacks/$STACK/src/index.2.2.ts \
          $DEST_ROOT/stacks/$STACK/src/index.ts
   fi

   # Now adjust each file
   # - Update StackReference to v3.1 format
   # - Update imports and paths
   # - Update Pulumi.yaml main: index.ts
   ```

**Order of processing (by dependency layer):**
1. network (layer 1)
2. security (layer 2)
3. dns (layer 2)
4. Continue through all 16 stacks

### Step 6: Implement CLI (Task 5.6)

**Priority order:**

1. **Setup CLI framework:**
   ```bash
   cd /c/Users/Admin/Documents/Workspace/cloud/tools/cli

   # Initialize npm project
   npm init -y

   # Install dependencies
   npm install commander
   npm install --save-dev typescript @types/node

   # Create tsconfig.json
   # Create package.json scripts
   ```

2. **Implement core commands first:**
   - `cloud init`
   - `cloud validate`
   - `cloud list`
   - `cloud status`

3. **Implement deployment commands:**
   - `cloud deploy`
   - `cloud deploy-stack`
   - `cloud destroy`
   - `cloud destroy-stack`

4. **Implement management commands:**
   - Stack management
   - Environment management
   - Template management

5. **Create unit tests** for each command

### Step 7: Implement Validation (Task 5.7)

1. Create validator classes in `lib/validators/`
2. Implement validation logic per Arch 3.1
3. Create unit tests
4. Integrate with CLI commands

### Step 8: Create Templates (Task 5.8-5.9)

1. **Generate doc templates** (5.8) in `templates/docs/`
2. **Generate Pulumi templates** (5.9) in `templates/stack/`
3. Test templates are usable

---

## Critical Notes

### ⚠️ SCOPE BOUNDARY

**WHAT THIS SESSION DOES:**
- ✅ Create directory structure
- ✅ Migrate all 16 stacks (docs + code)
- ✅ Implement CLI tool (25+ commands)
- ✅ Implement validation tools
- ✅ Create generic templates

**WHAT THIS SESSION DOES NOT DO:**
- ❌ Implement REST API (Session 3)
- ❌ Implement WebSockets (Session 3)
- ❌ Database integration (Session 3)
- ❌ Deploy to AWS (manual testing later)

### 📝 Working Directory

**Start:** `/c/Users/Admin/Documents/Workspace` (Workspace root)
**Source:** `/c/Users/Admin/Documents/Workspace/Pulumi-2` (existing)
**Destination:** `/c/Users/Admin/Documents/Workspace/cloud` (new)

**Both directories will exist** during this session.

### 🔗 Continuity to Session 3

**Handoff Deliverables:**

1. Complete directory structure
2. All 16 stacks migrated and working
3. CLI tool implemented and tested
4. Validation tools working
5. Templates ready for use

**Session 3 Will Add:**
- REST API implementation
- WebSocket monitoring
- Database integration planning
- Deployment documentation

---

## Success Criteria

### Session 2 is complete when:

1. ✅ Directory structure created (verify with ls commands)
2. ✅ All 16 stack docs migrated (check docs/ subdirectories)
3. ✅ All 16 stack code migrated (check src/ subdirectories)
4. ✅ CLI framework implemented (package.json, src/, commands/)
5. ✅ All CLI commands implemented (25+ command files)
6. ✅ Validation tools implemented (lib/validators/)
7. ✅ Doc templates created (templates/docs/)
8. ✅ Pulumi templates created (templates/stack/)
9. ✅ Unit tests created and passing (tests/)
10. ✅ Platform ready for manual testing

### Ready for Session 3 when:

1. ✅ Core platform functional
2. ✅ CLI commands working
3. ✅ Validation passing
4. ✅ No blocking issues

---

## Token Budget Monitoring

**Expected Usage:**
- Task 5.1-5.3 (Setup): ~5-10K tokens
- Task 5.4 (Stack migration): ~20-30K tokens
- Task 5.6 (CLI implementation): ~30-40K tokens
- Task 5.7 (Validation): ~15-20K tokens
- Task 5.8-5.9 (Templates): ~10-15K tokens
- **Total: ~80-115K tokens**

**If approaching 180K tokens:**
- Stop implementation
- Save progress
- Document what remains
- Continue in new session

---

## Emergency Recovery

**If session crashes:**

1. **Check progress:**
   ```bash
   # Check directory created
   ls -la /c/Users/Admin/Documents/Workspace/cloud

   # Check stacks migrated
   ls -la /c/Users/Admin/Documents/Workspace/cloud/stacks/

   # Check CLI progress
   ls -la /c/Users/Admin/Documents/Workspace/cloud/tools/cli/
   ```

2. Resume from last completed task
3. Use this prompt to continue
4. Reference Architecture 3.1 for specifications

---

## Final Checklist

**Before marking Session 2 complete:**

- [ ] Directory structure created
- [ ] All 16 stack docs migrated
- [ ] All 16 stack code migrated
- [ ] CLI framework implemented
- [ ] All CLI commands implemented
- [ ] Validation tools implemented
- [ ] Doc templates created
- [ ] Pulumi templates created
- [ ] Unit tests created and passing
- [ ] Token budget within limits
- [ ] Ready for Session 3

---

## Next Steps

**After Session 2 Completion:**

1. Manual testing of CLI commands
2. Validation of stack implementations
3. User review of implementation
4. If approved: Proceed to Session 3
5. Session 3: REST API, WebSockets, Database planning

---

## Summary of Improvements in This Version

**Fixes from Original Session-2-Prompt.3.1.md:**

1. ✅ Added Prompt-12 deprecation notice
2. ✅ Fixed all source paths to include `/Pulumi-2/` prefix
3. ✅ Fixed template structure: `stacks/` → `config/`, added `stack/`
4. ✅ Fixed document version references: `3.0` → `3.1`
5. ✅ Fixed architecture references: "2.x → 3.0" → "2.x → 3.1"
6. ✅ Added pre-session verification checklist
7. ✅ Added working directory strategy section
8. ✅ Clarified absolute vs relative paths throughout
9. ✅ Fixed mkdir command for templates (line 598 equivalent)
10. ✅ Removed incorrect document copy command (line 611 equivalent)
11. ✅ Added v3.1 stack naming examples and clarifications
12. ✅ Improved clarity on what Session 1 did/didn't do

**Total: 12 critical improvements applied**

---

**Session 2 Status:** Ready to Execute
**Expected Outcome:** Fully functional core platform
**Estimated Duration:** Full session (~80-115K tokens)
**Success Probability:** 95% (with improvements)

---

**Document Version:** 2.0 (IMPROVED)
**Date:** 2025-10-21
**Session:** 2 of 3
**Supersedes:** Session-2-Prompt.3.1.md (v1.0)
