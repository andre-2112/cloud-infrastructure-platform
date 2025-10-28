# Cloud Infrastructure Orchestration Platform v3.1 - CLI Commands Quick Reference

**Note:** This document will be moved to ./cloud/tools/docs/ when the new directory structure is created in Session 2.

**Version:** 3.1
**Last Updated:** 2025-10-09

---

## Deployment Lifecycle Commands

### Initialize Deployment
Create new deployment with auto-generated ID from template
```bash
cloud init --org <org> --project <project> --template <template> --region <region> --account-dev <account>
```

### Deploy All Stacks
Deploy all stacks in a deployment to specified environment (with layer-based execution and smart skip logic)
```bash
cloud deploy <deployment-id> --environment <env>
```

### Deploy Single Stack
Deploy a single stack within a deployment
```bash
cloud deploy-stack <deployment-id> <stack-name> --environment <env>
```

### Destroy All Stacks
Destroy all stacks in a deployment (reverse dependency order)
```bash
cloud destroy <deployment-id> --environment <env>
```

### Destroy Single Stack
Destroy a single stack within a deployment
```bash
cloud destroy-stack <deployment-id> <stack-name> --environment <env>
```

### Rollback Deployment
Rollback deployment to previous successful state
```bash
cloud rollback <deployment-id> --environment <env>
```

---

## Environment Management Commands

### Enable Environment
Enable an environment for deployment (stage or prod)
```bash
cloud enable-environment <deployment-id> <env-name>
```

### Disable Environment
Disable an environment (prevents deployments)
```bash
cloud disable-environment <deployment-id> <env-name>
```

### List Environments
List all environments for a deployment with their status
```bash
cloud list-environments <deployment-id>
```

---

## Stack Management Commands

### Register Stack
Register a new stack type to the platform (with dependencies)
```bash
cloud register-stack <stack-name> --description <desc> --dependencies <deps> --priority <priority>
```

### Update Stack Definition
Update an existing stack definition
```bash
cloud update-stack <stack-name> --description <desc> --dependencies <deps>
```

### Unregister Stack
Remove a stack type from the platform
```bash
cloud unregister-stack <stack-name>
```

### List Stacks
List all available stack types in the platform
```bash
cloud list-stacks
```

### Validate Stack
Validate a stack definition and configuration
```bash
cloud validate-stack <deployment-id> <stack-name> --environment <env>
```

---

## Template Management Commands

### List Templates
List all available deployment templates
```bash
cloud list-templates
```

### Show Template
Display detailed information about a specific template
```bash
cloud show-template <template-name>
```

### Create Template
Create a new custom deployment template
```bash
cloud create-template <template-name> --stacks <stack-list> --description <desc>
```

### Update Template
Update an existing template definition
```bash
cloud update-template <template-name> --stacks <stack-list>
```

### Validate Template
Validate a template definition and configuration
```bash
cloud validate-template <template-name>
```

---

## Validation Commands

### Validate Deployment
Validate complete deployment configuration before deploying
```bash
cloud validate <deployment-id>
```

### Validate Dependencies
Check stack dependencies for circular references and correctness (from templates)
```bash
cloud validate-dependencies <deployment-id>
```

### Validate AWS Access
Verify AWS credentials and required permissions
```bash
cloud validate-aws --region <region>
```

### Validate Pulumi Setup
Verify Pulumi CLI and authentication
```bash
cloud validate-pulumi
```

### Validate Stack Configuration
Validate specific stack configuration within deployment
```bash
cloud validate-stack <deployment-id> <stack-name> --environment <env>
```

### Validate Template Configuration
Validate template definition and referenced stacks
```bash
cloud validate-template <template-name>
```

---

## Status & Monitoring Commands

### Deployment Status
Show current status of a deployment across all environments (with WebSocket monitoring support)
```bash
cloud status <deployment-id> --all-environments
```

### List Deployments
List all deployments with their current status
```bash
cloud list
```

### View Logs
View deployment and stack operation logs
```bash
cloud logs <deployment-id> --stack <stack-name> --environment <env> --follow
```

### Discover Stacks
Discover available stacks from filesystem
```bash
cloud discover
```

### Discover Resources
Discover and list all AWS resources in a deployment
```bash
cloud discover-resources <deployment-id> --environment <env>
```

---

## Additional Utility Commands

### Export State
Export Pulumi state for backup or migration
```bash
cloud export-state <deployment-id> --environment <env> --output <file>
```

### Import State
Import Pulumi state from backup
```bash
cloud import-state <deployment-id> --environment <env> --input <file>
```

### Generate Config
Generate stack configuration files from manifest
```bash
cloud generate-config <deployment-id> --environment <env>
```

### Refresh State
Refresh Pulumi state to match actual AWS resources
```bash
cloud refresh <deployment-id> --environment <env>
```

### Preview Changes
Preview infrastructure changes without applying (dry-run)
```bash
cloud preview <deployment-id> --environment <env>
```

---

## Global Options

Available for all commands:
```bash
--verbose, -v          Enable verbose output
--quiet, -q            Suppress non-error output
--no-color             Disable colored output
--dry-run              Preview without making changes
--log-level <level>    Set log level (debug|info|warn|error)
--help, -h             Show help for command
--version              Show CLI version
```

---

## Quick Examples

### Complete Deployment Workflow
```bash
# 1. Initialize
cloud init --org "CompanyA" --project "ecommerce" --template default --region us-east-1 --account-dev 111111111111

# 2. Validate
cloud validate D1BRV40

# 3. Deploy to dev
cloud deploy D1BRV40 --environment dev

# 4. Check status
cloud status D1BRV40 --environment dev

# 5. Enable and deploy to stage
cloud enable-environment D1BRV40 stage
cloud deploy D1BRV40 --environment stage

# 6. Enable and deploy to prod
cloud enable-environment D1BRV40 prod
cloud deploy D1BRV40 --environment prod --confirm
```

### Single Stack Deployment
```bash
# Deploy only network stack
cloud deploy-stack D1BRV40 network --environment dev

# Preview changes first
cloud deploy-stack D1BRV40 compute-ec2 --environment dev --preview
```

### Monitoring and Troubleshooting
```bash
# Watch deployment status
cloud status D1BRV40 --environment dev --watch

# Follow logs in real-time
cloud logs D1BRV40 --environment dev --follow

# Discover deployed resources
cloud discover-resources D1BRV40 --environment dev
```

---

**Total Commands:** 33
**Command Categories:** 7

**New in v3.1:**
- Smart skip logic for unchanged stacks
- Layer-based parallel execution
- Template-based dependency management
- WebSocket monitoring support
- Updated environment naming (stage instead of staging)

For detailed documentation, see: CLI_Commands_Reference.3.1.md
