# CLI Commands Reference v3.0

**Note:** This document will be moved to ./cloud/tools/docs/ when the new directory structure is created in Session 2.

**Version:** 3.0
**Date:** 2025-10-09
**Platform:** Cloud Infrastructure Orchestration Platform (cloud-0.7)
**Status:** Complete Command Specification

---

## Table of Contents

1. [Command Overview](#command-overview)
2. [Installation and Setup](#installation-and-setup)
3. [Global Options](#global-options)
4. [Deployment Lifecycle Commands](#deployment-lifecycle-commands)
5. [Environment Management Commands](#environment-management-commands)
6. [Stack Management Commands](#stack-management-commands)
7. [Template Management Commands](#template-management-commands)
8. [Validation Commands](#validation-commands)
9. [Status and Monitoring Commands](#status-and-monitoring-commands)
10. [Discovery Commands](#discovery-commands)
11. [Utility Commands](#utility-commands)
12. [Common Workflows](#common-workflows)
13. [Troubleshooting](#troubleshooting)

---

## Command Overview

### Command Categories

The CLI provides 25+ commands organized into logical categories:

**Deployment Lifecycle** (6 commands)
- Initialize, deploy, destroy, and rollback deployments

**Environment Management** (3 commands)
- Enable, disable, and list environments

**Stack Management** (5 commands)
- Register, update, unregister, list, and validate stacks

**Template Management** (5 commands)
- List, show, create, update, and validate templates

**Validation** (6 commands)
- Validate manifests, stacks, dependencies, AWS, and Pulumi setup

**Status & Monitoring** (4 commands)
- View status, logs, and list deployments

**Discovery** (2 commands)
- Discover stacks and resources

### Command Naming Conventions

All commands follow consistent naming patterns:

- **Verbs:** `init`, `deploy`, `destroy`, `enable`, `disable`, `list`, `show`, `create`, `update`, `validate`
- **Nouns:** `deployment`, `stack`, `environment`, `template`, `manifest`
- **Format:** `verb-noun` or just `verb` for single-noun operations
- **Examples:** `deploy`, `deploy-stack`, `enable-environment`, `list-templates`

---

## Installation and Setup

### Installation

```bash
# Clone repository
git clone <repository-url>
cd infrastructure-platform

# Install CLI globally
cd ./cloud/tools/cli
npm install
npm run build
npm link

# Verify installation
cloud --version
# Output: 0.7.0

# Show help
cloud --help
```

### Prerequisites

**Required:**
- Node.js >= 18.0.0
- NPM >= 9.0.0
- Pulumi CLI >= 3.0.0
- AWS CLI >= 2.0.0

**Optional:**
- Git (for version control)
- Docker (for local testing)

### Configuration

```bash
# Configure AWS credentials
aws configure

# Configure Pulumi
pulumi login

# Verify setup
cloud validate-aws
cloud validate-pulumi
```

---

## Global Options

These options are available for all commands:

```
Options:
  -h, --help                 Show help
  -v, --version              Show version number
  --verbose                  Enable verbose output
  --quiet                    Suppress non-error output
  --no-color                 Disable colored output
  --log-level <level>        Set log level (debug|info|warn|error)
  --config <file>            Use custom config file
  --dry-run                  Show what would happen without making changes
```

**Examples:**
```bash
# Verbose output
cloud deploy D1BRV40 --environment dev --verbose

# Dry run (preview without execution)
cloud deploy D1BRV40 --environment dev --dry-run

# Custom log level
cloud deploy D1BRV40 --environment dev --log-level debug
```

---

## Deployment Lifecycle Commands

### `init` - Initialize New Deployment

Initialize a new deployment from a template with template-based dependency resolution.

**Syntax:**
```bash
cloud init [deployment-id] [options]
```

**Options:**
```
Required:
  --org <name>               Organization name
  --project <name>           Project name
  --domain <domain>          Primary domain
  --template <name>          Template name (default|minimal|microservices|data-platform)
  --region <region>          Primary AWS region
  --account-dev <account>    Dev AWS account ID

Optional:
  --region-secondary <region>     Secondary AWS region (default: same as primary)
  --account-stage <account>       Stage AWS account ID (default: same as dev)
  --account-prod <account>        Prod AWS account ID (default: same as dev)
  --stacks-enabled <list>         Comma-separated list of stacks to enable
  --stacks-disabled <list>        Comma-separated list of stacks to disable
  --from-file <file>              Load configuration from file
  --interactive, -i               Interactive mode (prompts for all inputs)
  --description <text>            Deployment description
```

**Examples:**

**Basic initialization (auto-generate ID):**
```bash
cloud init \
  --org "Company-A" \
  --project "ecommerce" \
  --domain "ecommerce.companyA.com" \
  --template default \
  --region us-east-1 \
  --account-dev 111111111111 \
  --account-stage 222222222222 \
  --account-prod 333333333333

# Output:
# Generated deployment ID: D1BRV40
# Created: ./cloud/deploy/D1BRV40-CompanyA-ecommerce/
# Generated manifest from template: default
# Template-based dependencies configured automatically
# Created 48 config files (16 stacks × 3 environments)
```

**With explicit deployment ID:**
```bash
cloud init D1CUSTOM \
  --org "Company-A" \
  --project "ecommerce" \
  --domain "ecommerce.companyA.com" \
  --template default \
  --region us-east-1 \
  --account-dev 111111111111
```

**Interactive mode:**
```bash
cloud init --interactive

# CLI prompts:
# Deployment ID (leave blank for auto-generate): [enter for auto]
# Organization name: Company-A
# Project name: ecommerce
# Domain: ecommerce.companyA.com
# Template (default/minimal/microservices/data-platform): default
# Primary region [us-east-1]: [enter]
# ...
```

**From configuration file:**
```bash
cloud init --from-file ./deployments/companyA-ecommerce.yaml
```

**With custom stack selection:**
```bash
cloud init \
  --org "Company-A" \
  --project "minimal-setup" \
  --domain "test.companyA.com" \
  --template minimal \
  --region us-east-1 \
  --account-dev 111111111111 \
  --stacks-enabled dns,network,security
```

---

### `deploy` - Deploy All Stacks

Deploy all enabled stacks in a deployment with layer-based execution and smart skip logic.

**Syntax:**
```bash
cloud deploy <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Environment to deploy (dev|stage|prod) [default: dev]
  --preview                  Preview changes without deploying
  --parallel <number>        Max parallel stack deployments [default: 3]
  --skip-validation          Skip pre-deployment validation
  --auto-approve             Skip approval prompts
  --rollback-on-error        Auto-rollback on deployment failure [default: true]
  --no-smart-skip            Disable smart skip logic for unchanged stacks
```

**Examples:**

**Deploy to dev environment:**
```bash
cloud deploy D1BRV40 --environment dev

# Output:
# Validating deployment...
# Validation passed
# Execution plan: 12 stacks in 6 layers
#
# Layer 1: dns, network (parallel)
# Layer 2: security
# Layer 3: secrets, storage (parallel)
# ...
#
# Starting layer-based deployment...
# Layer 1 complete (2/12 stacks)
# Layer 2 complete (3/12 stacks)
# Smart skip: 4 stacks unchanged, skipping
# ...
# Deployment complete! (12/12 stacks)
#
# Elapsed time: 41 minutes
# Resources created: 247
# WebSocket monitoring available at: ws://localhost:3000/deployments/D1BRV40-dev
```

**Preview without deploying:**
```bash
cloud deploy D1BRV40 --environment dev --preview

# Shows what would be deployed without making changes
```

**Deploy with auto-approval:**
```bash
cloud deploy D1BRV40 --environment stage --auto-approve
```

**Deploy with custom parallelization:**
```bash
cloud deploy D1BRV40 --environment dev --parallel 5
```

**Deploy without smart skip:**
```bash
cloud deploy D1BRV40 --environment dev --no-smart-skip
```

---

### `deploy-stack` - Deploy Single Stack

Deploy a single stack within a deployment.

**Syntax:**
```bash
cloud deploy-stack <deployment-id> <stack-name> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID
  <stack-name>               Stack name (e.g., network, database-rds)

Optional:
  --environment <env>        Environment to deploy [default: dev]
  --preview                  Preview changes without deploying
  --skip-dependencies        Don't check if dependencies are deployed
  --force                    Force deployment even if validation fails
```

**Examples:**

**Deploy single stack:**
```bash
cloud deploy-stack D1BRV40 network --environment dev

# Output:
# Validating stack 'network'...
# Dependencies satisfied: none
# Deploying network stack to dev environment...
#
# Pulumi Output:
# Updating (D1BRV40-dev)
#      Type                     Name              Status
#  +   pulumi:pulumi:Stack      network-dev       created
#  +   ├─ aws:ec2:Vpc           network-vpc       created
#  +   ├─ aws:ec2:Subnet        public-subnet-1   created
#  ...
#
# Resources: + 28 created
# Duration: 7m 42s
#
# Stack 'network' deployed successfully
```

**Preview single stack:**
```bash
cloud deploy-stack D1BRV40 compute-ec2 --environment dev --preview
```

**Force deployment (skip validation):**
```bash
cloud deploy-stack D1BRV40 monitoring --environment dev --force
```

---

### `destroy` - Destroy All Stacks

Destroy all stacks in a deployment (in reverse dependency order).

**Syntax:**
```bash
cloud destroy <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Environment to destroy [default: dev]
  --preview                  Preview what would be destroyed
  --parallel <number>        Max parallel stack destroys [default: 2]
  --skip-validation          Skip pre-destroy validation
  --confirm                  Require explicit confirmation (recommended for prod)
```

**Examples:**

**Destroy dev environment:**
```bash
cloud destroy D1BRV40 --environment dev

# Output:
# WARNING: This will destroy all resources in dev environment
# Stacks to destroy: 12 stacks
# Resources to delete: ~247 resources
#
# Are you sure? (yes/no): yes
#
# Destroying stacks in reverse order...
# Layer 6: monitoring destroyed
# Layer 5: compute-ec2, compute-lambda, services-ecs destroyed
# ...
# All stacks destroyed
```

**Preview destruction:**
```bash
cloud destroy D1BRV40 --environment dev --preview
```

**Destroy production (with confirmation):**
```bash
cloud destroy D1BRV40 --environment prod --confirm

# Requires typing full deployment ID for confirmation
```

---

### `destroy-stack` - Destroy Single Stack

Destroy a single stack within a deployment.

**Syntax:**
```bash
cloud destroy-stack <deployment-id> <stack-name> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID
  <stack-name>               Stack name

Optional:
  --environment <env>        Environment [default: dev]
  --preview                  Preview destruction
  --force                    Force destroy even if other stacks depend on it
  --confirm                  Require explicit confirmation
```

**Examples:**

**Destroy single stack:**
```bash
cloud destroy-stack D1BRV40 monitoring --environment dev

# Output:
# WARNING: This will destroy stack 'monitoring'
# Checking dependencies...
# No other stacks depend on 'monitoring'
#
# Are you sure? (yes/no): yes
#
# Destroying stack 'monitoring'...
# Stack destroyed successfully
```

**Preview destruction:**
```bash
cloud destroy-stack D1BRV40 compute-ec2 --environment dev --preview
```

---

### `rollback` - Rollback Deployment

Rollback a deployment to a previous state.

**Syntax:**
```bash
cloud rollback <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Environment [default: dev]
  --to-version <number>      Specific state version to rollback to
  --stack <name>             Rollback specific stack only
  --confirm                  Require confirmation
```

**Examples:**

**Rollback to previous version:**
```bash
cloud rollback D1BRV40 --environment dev

# Output:
# Current state version: 5
# Previous state version: 4
#
# Rolling back to version 4...
# Rollback complete
```

**Rollback to specific version:**
```bash
cloud rollback D1BRV40 --environment dev --to-version 3
```

**Rollback single stack:**
```bash
cloud rollback D1BRV40 --environment dev --stack network
```

---

## Environment Management Commands

### `enable-environment` - Enable Environment

Enable an environment in the deployment manifest.

**Syntax:**
```bash
cloud enable-environment <deployment-id> <environment> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID
  <environment>              Environment name (stage|prod)
```

**Examples:**

**Enable stage environment:**
```bash
cloud enable-environment D1BRV40 stage

# Output:
# Environment 'stage' enabled in manifest
# Updated: ./cloud/deploy/D1BRV40-.../src/Deployment_Manifest.yaml
#
# Next steps:
#   1. Review manifest changes
#   2. Deploy to stage: cloud deploy D1BRV40 --environment stage
```

**Enable production:**
```bash
cloud enable-environment D1BRV40 prod
```

---

### `disable-environment` - Disable Environment

Disable an environment in the deployment manifest.

**Syntax:**
```bash
cloud disable-environment <deployment-id> <environment> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID
  <environment>              Environment name (stage|prod)

Optional:
  --destroy                  Also destroy resources in environment
```

**Examples:**

**Disable environment:**
```bash
cloud disable-environment D1BRV40 stage

# Output:
# Environment 'stage' disabled in manifest
# Resources still exist. Run with --destroy to remove them.
```

**Disable and destroy:**
```bash
cloud disable-environment D1BRV40 stage --destroy

# Disables environment and destroys all resources
```

---

### `list-environments` - List Environments

List all environments and their status.

**Syntax:**
```bash
cloud list-environments <deployment-id> [options]
```

**Examples:**

**List environments:**
```bash
cloud list-environments D1BRV40

# Output:
# Deployment: D1BRV40-CompanyA-ecommerce
#
# Environment  Status    Region      Account         Deployed
# -----------  --------  ----------  --------------  --------
# dev          enabled   us-east-1   111111111111    Yes
# stage        disabled  us-east-1   111111111111    No
# prod         disabled  us-west-2   222222222222    No
```

---

## Stack Management Commands

### `register-stack` - Register New Stack

Register a new stack with the template system.

**Syntax:**
```bash
cloud register-stack <stack-name> [options]
```

**Options:**
```
Required:
  <stack-name>               Stack name (must exist in ./cloud/stacks/<stack-name>/)

Optional:
  --description <text>       Stack description
  --dependencies <list>      Comma-separated list of dependencies
  --defaults-file <file>     File with default configuration values
  --priority <number>        Default priority (1-999)
```

**Examples:**

**Register new stack:**
```bash
cloud register-stack my-new-stack \
  --description "Custom application stack" \
  --dependencies network,security \
  --priority 110

# Output:
# Validating stack directory...
# Found: ./cloud/stacks/my-new-stack/src/
# Parsing Pulumi.yaml...
# Stack validated
#
# Creating stack template...
# Template created: ./cloud/tools/templates/stacks/my-new-stack.yaml
#
# Stack 'my-new-stack' registered successfully
#
# The stack is now available for use in deployment templates.
```

**With defaults file:**
```bash
cloud register-stack my-new-stack \
  --description "Custom stack" \
  --defaults-file ./stack-defaults.yaml
```

---

### `update-stack` - Update Stack Template

Update an existing stack template.

**Syntax:**
```bash
cloud update-stack <stack-name> [options]
```

**Options:**
```
Required:
  <stack-name>               Stack name

Optional:
  --description <text>       Update description
  --dependencies <list>      Update dependencies
  --add-param <name:type:default>    Add parameter
  --remove-param <name>      Remove parameter
  --priority <number>        Update priority
```

**Examples:**

**Update stack description:**
```bash
cloud update-stack network \
  --description "Updated network stack with IPv6 support"
```

**Add parameter:**
```bash
cloud update-stack network \
  --add-param "enableIpv6:boolean:false"
```

**Update dependencies:**
```bash
cloud update-stack compute-ec2 \
  --dependencies network,security,database-rds
```

---

### `unregister-stack` - Remove Stack

Remove a stack from the template system.

**Syntax:**
```bash
cloud unregister-stack <stack-name> [options]
```

**Options:**
```
Required:
  <stack-name>               Stack name

Optional:
  --force                    Force removal even if used in deployments
```

**Examples:**

**Unregister stack:**
```bash
cloud unregister-stack deprecated-stack

# Output:
# WARNING: This will remove the stack from all templates
# Checking if stack is used in existing deployments...
# Stack not used in any active deployments
#
# Are you sure? (yes/no): yes
#
# Removing stack template...
# Stack 'deprecated-stack' unregistered
```

---

### `list-stacks` - List Registered Stacks

List all registered stacks.

**Syntax:**
```bash
cloud list-stacks [options]
```

**Options:**
```
Optional:
  --verbose, -v              Show detailed information
  --filter <pattern>         Filter by name pattern
```

**Examples:**

**List all stacks:**
```bash
cloud list-stacks

# Output:
# Registered Stacks (16 total)
#
# Name              Priority  Dependencies
# ----------------  --------  ---------------------------
# dns               10        none
# network           20        none
# security          30        network
# secrets           40        security
# authentication    50        security, secrets
# storage           60        network, security
# database-rds      70        network, security, secrets
# containers-images 80        security
# containers-apps   85        network, security, dns, containers-images
# services-ecr      90        security
# services-ecs      90        network, security
# services-eks      90        network, security
# services-api      95        network, security
# compute-ec2       100       network, security
# compute-lambda    100       network, security
# monitoring        120       ALL
```

**Verbose listing:**
```bash
cloud list-stacks --verbose

# Shows full details including description, parameters, etc.
```

---

### `validate-stack` - Validate Stack

Validate a stack configuration and readiness.

**Syntax:**
```bash
cloud validate-stack <deployment-id> <stack-name> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID
  <stack-name>               Stack name

Optional:
  --environment <env>        Environment [default: dev]
```

**Examples:**

**Validate stack:**
```bash
cloud validate-stack D1BRV40 network --environment dev

# Output:
# Validating stack 'network'...
#
# Stack code exists
# Pulumi.yaml valid
# Configuration complete
# Dependencies satisfied
# Runtime placeholders valid
#
# Stack 'network' is ready for deployment
```

---

## Template Management Commands

### `list-templates` - List Available Templates

List all available deployment templates.

**Syntax:**
```bash
cloud list-templates [options]
```

**Examples:**

**List templates:**
```bash
cloud list-templates

# Output:
# Available Templates
#
# Name           Stacks  Environments  Description
# -------------  ------  ------------  -----------------------------------------
# default        16      3             Full platform with all stacks
# minimal        3       1             Basic infrastructure only (dns, network, security)
# microservices  8       3             Container-focused platform
# data-platform  7       3             Data processing and analytics
#
# Custom Templates:
# companyA-std   12      3             Company A standard deployment
```

---

### `show-template` - Show Template Contents

Display the contents of a template.

**Syntax:**
```bash
cloud show-template <template-name> [options]
```

**Examples:**

**Show template:**
```bash
cloud show-template default

# Output:
# Template: default
# Description: Full platform with all stacks
# Location: ./cloud/tools/templates/manifest/default.yaml
#
# Stacks (16):
#   - dns (priority: 10)
#   - network (priority: 20)
#   - security (priority: 30)
#   ...
#
# Environments: dev, stage, prod
#
# [Full template contents displayed]
```

---

### `create-template` - Create Custom Template

Create a custom template from an existing deployment or from scratch.

**Syntax:**
```bash
cloud create-template <template-name> [options]
```

**Options:**
```
Required:
  <template-name>            Template name

Optional:
  --from-deployment <id>     Create from existing deployment
  --description <text>       Template description
  --stacks <list>            Comma-separated list of stacks to include
```

**Examples:**

**Create from existing deployment:**
```bash
cloud create-template companyA-standard \
  --from-deployment D1BRV40 \
  --description "Company A standard deployment template"

# Output:
# Loading deployment D1BRV40...
# Extracting configuration...
# Template created: ./cloud/tools/templates/manifest/custom/companyA-standard.yaml
#
# Template 'companyA-standard' is now available for new deployments.
```

**Create with custom stacks:**
```bash
cloud create-template minimal-compute \
  --description "Minimal compute infrastructure" \
  --stacks dns,network,security,compute-ec2
```

---

### `validate-template` - Validate Template

Validate a template's syntax and structure.

**Syntax:**
```bash
cloud validate-template <template-name> [options]
```

**Examples:**

**Validate template:**
```bash
cloud validate-template default

# Output:
# Validating template 'default'...
#
# YAML syntax valid
# Required fields present
# Variable references valid
# All referenced stacks exist
# Dependencies valid
#
# Template 'default' is valid
```

---

## Validation Commands

### `validate` - Validate Deployment Manifest

Validate a deployment manifest.

**Syntax:**
```bash
cloud validate <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Validate specific environment
  --fix                      Attempt to fix issues automatically
```

**Examples:**

**Validate deployment:**
```bash
cloud validate D1BRV40

# Output:
# Validating deployment D1BRV40...
#
# Manifest:
#   YAML syntax valid
#   Schema compliant
#   Required fields present
#
# Dependencies:
#   No circular dependencies
#   All dependencies exist
#   All dependencies enabled
#
# Configuration:
#   All required parameters present
#   Parameter types valid
#   Value ranges valid
#   Runtime placeholders syntax valid
#
# Environments:
#   dev: Valid
#   stage: Disabled (not validated)
#   prod: Disabled (not validated)
#
# Deployment D1BRV40 is valid
```

**Validate and fix:**
```bash
cloud validate D1BRV40 --fix

# Attempts to automatically fix validation issues
```

---

### `validate-dependencies` - Validate Dependencies

Validate stack dependencies for a deployment.

**Syntax:**
```bash
cloud validate-dependencies <deployment-id> [options]
```

**Examples:**

**Validate dependencies:**
```bash
cloud validate-dependencies D1BRV40

# Output:
# Analyzing dependencies...
#
# Dependency Graph:
#   dns           → (none)
#   network       → (none)
#   security      → network
#   secrets       → security
#   database-rds  → network, security, secrets
#   compute-ec2   → network, security
#   monitoring    → ALL
#
# No circular dependencies detected
# All dependencies exist
# All dependencies enabled
#
# Execution Layers:
#   Layer 1: dns, network
#   Layer 2: security
#   Layer 3: secrets
#   Layer 4: database-rds, compute-ec2
#   Layer 5: monitoring
```

---

### `validate-aws` - Validate AWS Access

Validate AWS credentials and permissions.

**Syntax:**
```bash
cloud validate-aws [options]
```

**Options:**
```
Optional:
  --region <region>          AWS region to validate
  --account <account>        AWS account ID to validate
  --profile <profile>        AWS profile to use
```

**Examples:**

**Validate AWS:**
```bash
cloud validate-aws --region us-east-1

# Output:
# Validating AWS access...
#
# Credentials:
#   AWS credentials found
#   Profile: default
#   Account ID: 111111111111
#   Region: us-east-1
#
# Permissions:
#   EC2 access
#   VPC access
#   RDS access
#   IAM access
#   S3 access
#
# AWS access validated
```

---

### `validate-pulumi` - Validate Pulumi Setup

Validate Pulumi CLI and authentication.

**Syntax:**
```bash
cloud validate-pulumi [options]
```

**Examples:**

**Validate Pulumi:**
```bash
cloud validate-pulumi

# Output:
# Validating Pulumi setup...
#
# CLI:
#   Pulumi CLI installed
#   Version: 3.92.0
#   Minimum version met (3.0.0)
#
# Authentication:
#   Logged in to Pulumi Cloud
#   Organization: companyA
#   User: admin@companyA.com
#
# Access:
#   Can create stacks
#   Can read state
#   Can write state
#
# Pulumi setup validated
```

---

## Status and Monitoring Commands

### `status` - Show Deployment Status

Show the current status of a deployment with WebSocket monitoring support.

**Syntax:**
```bash
cloud status <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Show specific environment
  --all-environments         Show all environments
  --stack <name>             Show specific stack only
  --watch                    Continuously update status
  --refresh-interval <sec>   Update interval for watch mode [default: 5]
```

**Examples:**

**Show deployment status:**
```bash
cloud status D1BRV40 --environment dev

# Output:
# Deployment: D1BRV40-CompanyA-ecommerce
# Environment: dev
# Region: us-east-1
# Account: 111111111111
#
# Overall Status: Healthy
# Last Deployment: 2025-10-09 14:30:00
# Resources: 247 total
# WebSocket monitoring: ws://localhost:3000/deployments/D1BRV40-dev
#
# Stack Status:
# Name              Status    Resources  Last Updated
# ----------------  --------  ---------  --------------------
# dns               Active    12         2025-10-09 14:31:00
# network           Active    28         2025-10-09 14:38:00
# security          Active    18         2025-10-09 14:43:00
# secrets           Active    8          2025-10-09 14:45:00
# storage           Active    14         2025-10-09 14:48:00
# database-rds      Active    22         2025-10-09 15:00:00
# compute-ec2       Active    35         2025-10-09 15:08:00
# compute-lambda    Active    18         2025-10-09 15:12:00
# services-ecs      Active    42         2025-10-09 15:20:00
# monitoring        Active    50         2025-10-09 15:25:00
```

**Show all environments:**
```bash
cloud status D1BRV40 --all-environments

# Shows status for dev, stage, and prod
```

**Watch mode (continuous updates):**
```bash
cloud status D1BRV40 --environment dev --watch

# Updates every 5 seconds, Ctrl+C to exit
```

---

### `list` - List All Deployments

List all deployments.

**Syntax:**
```bash
cloud list [options]
```

**Options:**
```
Optional:
  --org <name>               Filter by organization
  --project <name>           Filter by project
  --environment <env>        Filter by environment
  --status <status>          Filter by status (active|inactive|failed)
  --sort <field>             Sort by field (id|created|updated)
```

**Examples:**

**List all deployments:**
```bash
cloud list

# Output:
# Deployments (5 total)
#
# ID      Organization  Project      Environments    Status    Created
# ------  ------------  -----------  --------------  --------  ----------
# D1BRV40 Company-A     ecommerce    dev             Active    2025-10-09
# D1BRV45 Company-B     mobile       dev,stage       Active    2025-10-09
# D1BRV48 Company-A     analytics    dev             Active    2025-10-09
# D1BRV50 Company-C     portal       dev             Active    2025-10-09
# D1BRV52 Company-A     cms          dev,stage       Active    2025-10-09
```

**Filter by organization:**
```bash
cloud list --org "Company-A"

# Shows only Company-A deployments
```

---

### `logs` - View Deployment Logs

View deployment logs.

**Syntax:**
```bash
cloud logs <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Environment logs
  --stack <name>             Stack-specific logs
  --type <type>              Log type (init|deploy|destroy)
  --follow, -f               Follow log output (tail -f)
  --lines <number>           Number of lines to show [default: 100]
  --since <time>             Show logs since time (e.g., "1h", "30m")
```

**Examples:**

**View recent deployment logs:**
```bash
cloud logs D1BRV40 --environment dev

# Shows last 100 lines of most recent deployment log
```

**Follow logs in real-time:**
```bash
cloud logs D1BRV40 --environment dev --follow

# Continuously streams log output
```

**View stack-specific logs:**
```bash
cloud logs D1BRV40 --environment dev --stack network
```

**View initialization logs:**
```bash
cloud logs D1BRV40 --type init
```

---

## Discovery Commands

### `discover` - Discover Available Stacks

Discover all available stacks from the filesystem.

**Syntax:**
```bash
cloud discover [options]
```

**Options:**
```
Optional:
  --path <path>              Custom path to search [default: ./cloud/stacks/]
  --verbose, -v              Show detailed information
```

**Examples:**

**Discover stacks:**
```bash
cloud discover

# Output:
# Scanning ./cloud/stacks/ for stacks...
#
# Discovered Stacks (16 total):
#
# Name              Path                                Registered
# ----------------  ---------------------------------   ----------
# dns               ./cloud/stacks/dns/src/             Yes
# network           ./cloud/stacks/network/src/         Yes
# security          ./cloud/stacks/security/src/        Yes
# secrets           ./cloud/stacks/secrets/src/         Yes
# ...
#
# Discovery complete
#
# Not registered (0 stacks)
#
# To register a stack:
#   cloud register-stack <stack-name>
```

---

### `discover-resources` - Discover Deployed Resources

Discover all deployed AWS resources for a deployment.

**Syntax:**
```bash
cloud discover-resources <deployment-id> [options]
```

**Options:**
```
Required:
  <deployment-id>            Deployment ID

Optional:
  --environment <env>        Environment [default: dev]
  --output <format>          Output format (table|json|yaml) [default: table]
  --export <file>            Export to file
```

**Examples:**

**Discover resources:**
```bash
cloud discover-resources D1BRV40 --environment dev

# Output:
# Discovering resources for D1BRV40 (dev)...
#
# Resource Inventory (247 resources):
#
# Type            Count  Stack
# --------------  -----  ----------------
# aws:ec2:Vpc     1      network
# aws:ec2:Subnet  6      network
# aws:ec2:RouteTable 3   network
# aws:ec2:NatGateway 2   network
# aws:iam:Role    12     security
# aws:rds:Instance 1     database-rds
# aws:s3:Bucket   5      storage
# ...
#
# Total Cost (estimated): $1,247/month
```

**Export to JSON:**
```bash
cloud discover-resources D1BRV40 --environment dev \
  --output json \
  --export ./resources.json
```

---

## Utility Commands

### `version` - Show Version

Display CLI version information.

**Syntax:**
```bash
cloud version
```

**Example:**
```bash
cloud version

# Output:
# Cloud CLI v0.7.0
# Pulumi: v3.92.0
# Node.js: v18.17.0
# Platform: darwin-arm64
```

---

### `help` - Show Help

Display help information.

**Syntax:**
```bash
cloud help [command]
```

**Examples:**

**General help:**
```bash
cloud help
```

**Command-specific help:**
```bash
cloud help deploy
cloud help init
```

---

## Common Workflows

### Workflow 1: Create New Deployment

```bash
# Step 1: Initialize deployment
cloud init \
  --org "Company-A" \
  --project "ecommerce" \
  --domain "ecommerce.companyA.com" \
  --template default \
  --region us-east-1 \
  --account-dev 111111111111

# Output: Deployment ID: D1BRV40

# Step 2: Review manifest (optional)
cat ./cloud/deploy/D1BRV40-CompanyA-ecommerce/src/Deployment_Manifest.yaml

# Step 3: Validate
cloud validate D1BRV40

# Step 4: Deploy to dev
cloud deploy D1BRV40 --environment dev

# Step 5: Check status
cloud status D1BRV40 --environment dev
```

### Workflow 2: Promote to Production

```bash
# Step 1: Deploy and validate dev
cloud deploy D1BRV40 --environment dev
cloud status D1BRV40 --environment dev

# Step 2: Enable and deploy stage
cloud enable-environment D1BRV40 stage
cloud deploy D1BRV40 --environment stage
cloud status D1BRV40 --environment stage

# Step 3: Enable and deploy production
cloud enable-environment D1BRV40 prod
cloud deploy D1BRV40 --environment prod --confirm
cloud status D1BRV40 --environment prod
```

### Workflow 3: Deploy Single Stack

```bash
# Step 1: Validate stack
cloud validate-stack D1BRV40 compute-ec2 --environment dev

# Step 2: Preview deployment
cloud deploy-stack D1BRV40 compute-ec2 --environment dev --preview

# Step 3: Deploy
cloud deploy-stack D1BRV40 compute-ec2 --environment dev

# Step 4: Verify
cloud status D1BRV40 --environment dev --stack compute-ec2
```

### Workflow 4: Register and Use New Stack

```bash
# Step 1: Create stack code in ./cloud/stacks/my-stack/src/

# Step 2: Register stack
cloud register-stack my-stack \
  --description "My custom stack" \
  --dependencies network,security

# Step 3: Verify registration
cloud list-stacks | grep my-stack

# Step 4: Create new deployment with custom stack
# (Edit template or create custom template including my-stack)

# Step 5: Deploy
cloud init --template custom --org "Company-A" ...
cloud deploy D1BRV60 --environment dev
```

### Workflow 5: Troubleshoot Deployment Failure

```bash
# Step 1: Check deployment status
cloud status D1BRV40 --environment dev

# Step 2: View logs
cloud logs D1BRV40 --environment dev

# Step 3: View stack-specific logs
cloud logs D1BRV40 --environment dev --stack network

# Step 4: Validate configuration
cloud validate D1BRV40

# Step 5: Fix issues and retry
# (Edit manifest or config as needed)
cloud deploy D1BRV40 --environment dev

# Step 6: If needed, rollback
cloud rollback D1BRV40 --environment dev
```

---

## Troubleshooting

### Common Errors and Solutions

**Error: Deployment ID not found**
```
Error: Deployment 'D1BRV40' not found

Solution:
1. Check deployment ID: cloud list
2. Verify deployment directory exists: ls ./cloud/deploy/
```

**Error: Circular dependency detected**
```
Error: Circular dependency: stack-a → stack-b → stack-a

Solution:
1. Review manifest dependencies
2. Run: cloud validate-dependencies D1BRV40
3. Edit manifest to break circular dependency
```

**Error: AWS credentials not configured**
```
Error: AWS credentials not found

Solution:
1. Configure AWS: aws configure
2. Verify: cloud validate-aws
```

**Error: Pulumi not authenticated**
```
Error: Not logged in to Pulumi Cloud

Solution:
1. Login: pulumi login
2. Verify: cloud validate-pulumi
```

**Error: Runtime placeholder unresolved**
```
Error: Unable to resolve {{RUNTIME:network:vpcId}}

Solution:
1. Check network stack is deployed: cloud status D1BRV40 --stack network
2. Verify network stack exports vpcId output
3. Deploy network stack first: cloud deploy-stack D1BRV40 network
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Set debug log level
cloud deploy D1BRV40 --environment dev --log-level debug --verbose

# Check verbose logs
cloud logs D1BRV40 --environment dev --lines 1000
```

### Getting Help

```bash
# Command-specific help
cloud help <command>

# General help
cloud --help

# Version information
cloud version
```

---

## Conclusion

This CLI provides comprehensive commands for managing the entire lifecycle of infrastructure deployments. For additional information:

- **Architecture Documentation:** `Multi-Stack-Architecture-3.0.md`
- **REST API Documentation:** `REST_API_Documentation.3.0.md`
- **Verification Guide:** `Addendum_Verification_Architecture.3.0.md`

For issues or feature requests, please contact the platform team or submit a GitHub issue.

---

**Document Version:** 3.0.0
**Last Updated:** 2025-10-09
**Status:** Complete Reference