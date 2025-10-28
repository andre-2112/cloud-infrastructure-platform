# Cloud Architecture v3.0 - Questions & Answers Addendum

**Version:** 3.0
**Last Updated:** 2025-10-09
**Status:** Production Ready

---

## Table of Contents

1. [General Questions](#general-questions)
2. [Architecture Questions](#architecture-questions)
3. [Deployment Questions](#deployment-questions)
4. [Configuration Questions](#configuration-questions)
5. [Troubleshooting Questions](#troubleshooting-questions)
6. [Advanced Topics](#advanced-topics)

---

## General Questions

### Q1: What is Cloud Architecture v3.0?

**A:** Cloud Architecture v3.0 is an enterprise-grade infrastructure orchestration platform that manages complex AWS deployments using Pulumi. It provides:
- Template-based deployment initialization
- Smart partial re-deployment with skip logic
- Layer-based parallel execution
- Real-time progress monitoring via WebSockets
- Comprehensive CLI tool and REST API

**Key Improvements over v2.3:**
- Smart skip logic (70-90% time savings on unchanged stacks)
- Layer-based execution by orchestrator (not Pulumi)
- Template-based dependencies (single source of truth)
- Enhanced runtime placeholder resolution
- Multi-file stack support

---

### Q2: What are the main differences between v2.3 and v3.0?

**A:** Major changes include:

**Naming:**
- CLI tool: `multi-stack` → `cloud`
- Environment: `staging` → `stage`
- Stack naming: `<org>/<stack>/<env>` → `<deployment-id>-<environment>`

**Directory Structure:**
- `./aws/deploy/` → `./cloud/deploy/`
- `./admin/v2/` → `./cloud/tools/`
- `./aws/build/<stack>/v2/resources/` → `./cloud/stacks/<stack>/src/`

**Architecture:**
- Dependencies now in templates (not hardcoded in stack code)
- Smart skip logic for unchanged stacks
- Layer-based parallel execution
- Enhanced placeholder resolution (ENV, RUNTIME, AWS, SECRET)
- Multi-file stack support with explicit imports

See: Addendum_Changes_From_2.3.3.0.md for complete details.

---

### Q3: Who should use Cloud Architecture v3.0?

**A:** The platform is designed for:

1. **Platform Engineers**: Building and maintaining infrastructure
2. **DevOps Teams**: Automating deployment pipelines
3. **Cloud Architects**: Designing multi-environment AWS architectures
4. **Development Teams**: Deploying applications with infrastructure
5. **Enterprise Organizations**: Managing multiple deployments at scale

**Prerequisites:**
- AWS knowledge (VPC, EC2, RDS, IAM, etc.)
- Pulumi experience (or willingness to learn)
- TypeScript/Node.js familiarity
- Infrastructure as Code concepts

---

### Q4: What are the system requirements?

**A:**

**Development Environment:**
- Node.js >= 18.0.0 (20.x LTS recommended)
- npm >= 8.0.0 (10.x recommended)
- TypeScript >= 5.0.0
- Pulumi CLI >= 3.0.0 (3.90+ recommended)
- AWS CLI >= 2.0.0 (2.13+ recommended)
- 8GB RAM minimum (16GB+ recommended)
- 10GB storage minimum (20GB+ recommended)

**AWS Requirements:**
- Valid AWS account(s) with appropriate permissions
- AWS credentials configured (via AWS CLI or environment variables)
- Appropriate IAM roles/policies for resource creation

---

## Architecture Questions

### Q5: How does the dependency resolution work?

**A:** Dependency resolution in v3.0 happens at two levels:

**1. Template-Level (Build Time):**
- Dependencies declared in deployment templates
- Used by orchestrator to create execution layers
- Forms a Directed Acyclic Graph (DAG)
- Validated before deployment

**2. Runtime-Level (Deploy Time):**
- `DependencyResolver` utility handles cross-stack references
- Resolves `{{RUNTIME:stack:output}}` placeholders
- Retrieves outputs from deployed stacks via Pulumi StackReference

**Example:**
```typescript
// In template: database-rds depends on network, security
"dependencies": ["network", "security"]

// In stack code: DependencyResolver gets outputs
const vpcId = resolver.get('network', 'vpcId');
const securityGroupId = resolver.get('security', 'databaseSecurityGroupId');
```

See: Deployment_Manifest_Specification.3.0.md, Section "Runtime Placeholders"

---

### Q6: How does smart skip logic work?

**A:** Smart skip logic analyzes each stack to determine if deployment is needed:

**Detection Method:**
1. Hash stack configuration (manifest + Pulumi config)
2. Compare with previous deployment hash (stored in DynamoDB)
3. If hash unchanged → skip stack
4. If hash changed → deploy stack

**Benefits:**
- 70-90% time savings on typical deployments
- Only deploys what changed
- Automatic detection (no manual intervention)
- Preserves dependency order

**Example:**
```bash
# First deployment: all 12 stacks deployed (20 minutes)
cloud deploy D1BRV40 --environment dev

# Second deployment with no changes: 11 stacks skipped (2 minutes)
cloud deploy D1BRV40 --environment dev
# Output: Smart Skip: 11 stacks unchanged, skipping
```

**Disable:**
```bash
cloud deploy D1BRV40 --environment dev --no-smart-skip
```

---

### Q7: How does layer-based execution work?

**A:** Layer-based execution organizes stacks by dependencies:

**Process:**
1. Orchestrator resolves dependency graph
2. Groups stacks into layers (no dependencies within layer)
3. Executes layers sequentially
4. Executes stacks within layer in parallel (max 3 concurrent by default)

**Example Layers:**
```
Layer 0: network
Layer 1: security, secrets, dns (parallel)
Layer 2: database-rds, storage (parallel)
Layer 3: compute-ec2, containers-apps (parallel)
Layer 4: monitoring
```

**Performance:**
- Sequential: 21.5 minutes
- Parallel (layer-based): 10.5 minutes
- **51% faster**

**Control Parallelism:**
```bash
cloud deploy D1BRV40 --environment dev --parallel 5
```

---

### Q8: What are runtime placeholders?

**A:** Runtime placeholders enable dynamic value resolution at deployment time:

**Types:**

1. **ENV** - Environment configuration:
```json
{"instanceType": "{{ENV:instanceType}}"}
// Resolves to environments.dev.config.instanceType
```

2. **RUNTIME** - Cross-stack outputs:
```json
{"vpcId": "{{RUNTIME:network:vpcId}}"}
// Resolves to output from network stack
```

3. **AWS** - AWS API queries:
```json
{"hostedZoneId": "{{AWS:route53:hostedZone:example.com}}"}
// Queries AWS Route53 for hosted zone
```

4. **SECRET** - AWS Secrets Manager:
```json
{"dbPassword": "{{SECRET:database/prod/password}}"}
// Retrieves secret from Secrets Manager
```

**Resolution Order:** ENV → AWS → SECRET → RUNTIME

See: Deployment_Manifest_Specification.3.0.md, Section "Runtime Placeholders"

---

## Deployment Questions

### Q9: How do I create a new deployment?

**A:**

**Step 1: Initialize deployment**
```bash
cloud init \
  --org "CompanyA" \
  --project "ecommerce" \
  --template default \
  --region us-east-1 \
  --account-dev 111111111111

# Output: Deployment created: D1BRV40
```

**Step 2: Review manifest**
```bash
cat ./cloud/deploy/D1BRV40/manifest.json
```

**Step 3: Validate**
```bash
cloud validate D1BRV40
```

**Step 4: Deploy to dev**
```bash
cloud deploy D1BRV40 --environment dev
```

**Step 5: Enable and deploy to stage/prod**
```bash
cloud enable-environment D1BRV40 stage
cloud deploy D1BRV40 --environment stage
```

See: CLI_Commands_Reference.3.0.md, Section "Deployment Lifecycle Commands"

---

### Q10: How do I deploy a single stack?

**A:**

```bash
# Deploy single stack
cloud deploy-stack D1BRV40 database-rds --environment dev

# Deploy with preview first
cloud deploy-stack D1BRV40 database-rds --environment dev --preview

# Deploy and skip validation
cloud deploy-stack D1BRV40 database-rds --environment dev --skip-validation
```

**Note:** Dependencies must be deployed first. If network and security stacks aren't deployed, database-rds deployment will fail.

**Check dependencies:**
```bash
cloud validate-dependencies D1BRV40
```

---

### Q11: How do I promote from dev to stage?

**A:** Two approaches:

**Approach 1: Manual deployment**
```bash
# Enable stage environment
cloud enable-environment D1BRV40 stage

# Update manifest with stage-specific config (optional)
# Edit ./cloud/deploy/D1BRV40/manifest.json

# Deploy to stage
cloud deploy D1BRV40 --environment stage
```

**Approach 2: Clone deployment**
```bash
# Clone entire dev deployment to stage
cloud clone-deployment D1BRV40 \
  --source-env dev \
  --target-env stage \
  --verify
```

The clone approach copies working dev configuration to stage, ensuring consistency.

See: Addendum_Stack_Cloning.3.0.md for cloning details.

---

### Q12: How do I rollback a failed deployment?

**A:**

**Automatic Rollback (if enabled):**
```bash
# Deploy with auto-rollback
cloud deploy D1BRV40 --environment dev --auto-rollback
# If deployment fails, automatically rolls back to previous state
```

**Manual Rollback:**
```bash
# Rollback to previous successful state
cloud rollback D1BRV40 --environment dev

# Rollback to specific version
cloud rollback D1BRV40 --environment dev --version 5
```

**Rollback Process:**
1. Reads previous deployment state
2. Destroys failed stacks (reverse dependency order)
3. Re-deploys previous working version
4. Verifies rollback success

**Note:** Rollback may not be possible if:
- Previous state doesn't exist (first deployment)
- Resources were manually deleted
- State corruption occurred

---

## Configuration Questions

### Q13: How do I customize stack configuration?

**A:** Configuration can be set at multiple levels:

**1. Global Stack Config (applies to all environments):**
```json
{
  "stacks": {
    "database-rds": {
      "config": {
        "engine": "postgres",
        "engineVersion": "15.3",
        "allocatedStorage": 100
      }
    }
  }
}
```

**2. Environment Config (applies to specific environment):**
```json
{
  "environments": {
    "dev": {
      "config": {
        "instanceType": "t3.micro",
        "enableBackups": false
      }
    }
  }
}
```

**3. Stack Environment Config (stack-specific for environment):**
```json
{
  "stacks": {
    "database-rds": {
      "environments": {
        "prod": {
          "config": {
            "instanceClass": "db.r5.large",
            "multiAz": true
          }
        }
      }
    }
  }
}
```

**Precedence:** Template defaults < Global stack < Environment < Stack environment (last wins)

---

### Q14: How do I add a new stack to existing deployment?

**A:**

**Step 1: Register stack in platform**
```bash
cloud register-stack my-custom-stack \
  --description "Custom application stack" \
  --dependencies network,security \
  --priority 60
```

**Step 2: Add stack to deployment manifest**
```bash
# Edit ./cloud/deploy/D1BRV40/manifest.json
# Add entry in "stacks" section:
{
  "my-custom-stack": {
    "enabled": true,
    "dependencies": ["network", "security"],
    "priority": 60,
    "config": {
      // Stack-specific config
    }
  }
}
```

**Step 3: Deploy new stack**
```bash
cloud deploy-stack D1BRV40 my-custom-stack --environment dev
```

---

### Q15: How do I disable a stack without deleting it?

**A:**

**Globally disable:**
```json
{
  "stacks": {
    "monitoring": {
      "enabled": false  // Disabled in all environments
    }
  }
}
```

**Disable in specific environment:**
```json
{
  "stacks": {
    "monitoring": {
      "enabled": true,  // Enabled globally
      "environments": {
        "dev": {
          "enabled": false  // Disabled only in dev
        }
      }
    }
  }
}
```

**Result:** Disabled stacks are skipped during deployment but remain in manifest for future re-enabling.

To destroy resources:
```bash
cloud destroy-stack D1BRV40 monitoring --environment dev
```

---

## Troubleshooting Questions

### Q16: My deployment failed. How do I troubleshoot?

**A:** Follow this troubleshooting process:

**1. Check deployment logs:**
```bash
cloud logs D1BRV40 --environment dev --follow

# Or check log file directly:
cat ./cloud/deploy/D1BRV40/logs/deploy-dev-<timestamp>.log
```

**2. Check stack status:**
```bash
cloud status D1BRV40 --environment dev
```

**3. Validate configuration:**
```bash
cloud validate D1BRV40
```

**4. Check AWS permissions:**
```bash
cloud validate-aws --region us-east-1
```

**5. Check Pulumi backend:**
```bash
cloud validate-pulumi
```

**Common Issues:**
- **Insufficient IAM permissions**: Grant required AWS permissions
- **Circular dependencies**: Fix dependencies in manifest
- **Missing stack outputs**: Ensure dependency stacks are deployed
- **Configuration errors**: Validate placeholder syntax
- **Pulumi state locked**: Wait or force unlock

See: Addendum_Verification_Architecture.3.0.md, Section "Error Detection & Reporting"

---

### Q17: How do I fix circular dependencies?

**A:**

**Detection:**
```bash
cloud validate-dependencies D1BRV40
# Error: Circular dependency detected: network → security → network
```

**Resolution:**
1. Identify the cycle (shown in error message)
2. Remove one dependency link to break cycle
3. Restructure if needed (create intermediate stack)

**Example Fix:**
```json
// BEFORE (circular):
{
  "network": {
    "dependencies": ["security"]  // ← Remove this
  },
  "security": {
    "dependencies": ["network"]
  }
}

// AFTER (fixed):
{
  "network": {
    "dependencies": []  // ← Fixed
  },
  "security": {
    "dependencies": ["network"]
  }
}
```

**Best Practice:** Keep dependencies unidirectional:
- Foundation stacks (network) have no dependencies
- Security/IAM depend on network
- Application stacks depend on security + infrastructure

---

### Q18: What if a stack deployment hangs?

**A:**

**Diagnosis:**
```bash
# Check Pulumi operation status
pulumi stack --stack D1BRV40-dev --show-urns

# Check AWS CloudFormation (if Pulumi uses it)
aws cloudformation list-stacks --region us-east-1

# Check CloudWatch logs for stack
cloud logs D1BRV40 --stack database-rds --environment dev --follow
```

**Resolution:**

**Option 1: Wait (RDS can take 5-10 minutes)**
- Some resources (RDS, EKS) take time
- Check AWS console for actual resource status

**Option 2: Cancel and retry**
```bash
# Cancel current operation
pulumi cancel --stack D1BRV40-dev

# Retry deployment
cloud deploy-stack D1BRV40 database-rds --environment dev
```

**Option 3: Force unlock (if state is locked)**
```bash
# DANGER: Only if certain no other operation is running
pulumi stack --stack D1BRV40-dev --force-unlock
```

---

### Q19: How do I recover from corrupted state?

**A:**

**If state backup exists:**
```bash
# Export current state (even if corrupted)
pulumi stack export --stack D1BRV40-dev > corrupted-state.json

# Import backup state
pulumi stack import --stack D1BRV40-dev < backup-state.json

# Refresh to sync with AWS
cloud refresh D1BRV40 --environment dev
```

**If no backup:**
```bash
# Option 1: Refresh from AWS (preserves resources)
cloud refresh D1BRV40 --environment dev
# Pulumi queries AWS and updates state

# Option 2: Import existing resources
cloud import-resources D1BRV40 --environment dev
# Imports AWS resources into Pulumi state

# Option 3: Recreate (LAST RESORT - destroys and recreates)
cloud destroy D1BRV40 --environment dev
cloud deploy D1BRV40 --environment dev
```

---

## Advanced Topics

### Q20: How do I implement custom validation?

**A:** Implement custom validation hooks:

**1. Create validation hook:**
```typescript
// .cloud/hooks/validate.ts
export async function validateHook(deployment: Deployment): Promise<ValidationResult> {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Custom validation logic
  if (deployment.environments.prod.enabled) {
    if (!deployment.stacks['monitoring'].enabled) {
      errors.push('Monitoring must be enabled in production');
    }

    if (deployment.stacks['database-rds'].config.multiAz === false) {
      warnings.push('Multi-AZ should be enabled for production databases');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}
```

**2. Register hook:**
```bash
# In manifest.json or global config
{
  "hooks": {
    "validate": ".cloud/hooks/validate.ts"
  }
}
```

**3. Run validation:**
```bash
cloud validate D1BRV40
# Custom validation runs automatically
```

---

### Q21: How do I integrate with CI/CD?

**A:** Example GitHub Actions workflow:

```yaml
name: Deploy Infrastructure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Validate deployment
        run: cloud validate D1BRV40

      - name: Deploy to dev
        run: cloud deploy D1BRV40 --environment dev

      - name: Run tests
        run: cloud test D1BRV40 --environment dev

      - name: Notify success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: 'Deployment D1BRV40-dev completed successfully'
```

---

### Q22: How do I monitor deployments in real-time?

**A:** Use WebSocket connection:

```javascript
const ws = new WebSocket(`ws://api.example.com/ws?token=${authToken}`);

ws.onopen = () => {
  // Subscribe to deployment events
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: `deployments/D1BRV40-dev`
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'deployment_started':
      console.log('Deployment started');
      break;

    case 'stack_deploying':
      console.log(`Deploying: ${message.data.stack}`);
      break;

    case 'stack_deployed':
      console.log(`✓ ${message.data.stack} deployed (${message.data.durationSeconds}s)`);
      break;

    case 'deployment_complete':
      console.log('Deployment complete');
      ws.close();
      break;
  }
};
```

See: Addendum_Progress_Monitoring.3.0.md for complete WebSocket documentation.

---

### Q23: Can I use custom Pulumi backends?

**A:** Yes, Cloud Architecture v3.0 supports all Pulumi backends:

**Pulumi Cloud (default):**
```bash
pulumi login
```

**Self-hosted S3 backend:**
```bash
pulumi login s3://my-pulumi-state-bucket
```

**Self-hosted Azure Blob:**
```bash
pulumi login azblob://my-container
```

**Local filesystem (testing only):**
```bash
pulumi login file://~/.pulumi-local
```

**Configure in manifest:**
```json
{
  "deployment": {
    "pulumi": {
      "backend": "s3://my-pulumi-state-bucket"
    }
  }
}
```

---

### Q24: How do I create custom deployment templates?

**A:**

**Step 1: Create template file**
```json
// ./cloud/tools/templates/my-custom-template.json
{
  "name": "my-custom-template",
  "description": "Custom template for specific use case",
  "stacks": [
    {
      "name": "network",
      "dependencies": [],
      "priority": 100,
      "config": {
        "vpcCidr": "10.0.0.0/16",
        "availabilityZones": 3
      }
    },
    {
      "name": "my-custom-stack",
      "dependencies": ["network"],
      "priority": 80,
      "config": {
        "customParam": "value"
      }
    }
  ]
}
```

**Step 2: Register template**
```bash
cloud create-template my-custom-template \
  --file ./cloud/tools/templates/my-custom-template.json
```

**Step 3: Use template**
```bash
cloud init \
  --org "CompanyA" \
  --project "custom-project" \
  --template my-custom-template \
  --region us-east-1 \
  --account-dev 111111111111
```

---

### Q25: How do I migrate from v2.3 to v3.0?

**A:** Follow the migration process:

**Step 1: Backup v2.3**
```bash
# Backup directory structure
cp -r ./aws ./aws-backup-v2.3

# Export all stacks
for stack in $(pulumi stack ls); do
  pulumi stack export --stack $stack > backup-$stack.json
done
```

**Step 2: Create v3.0 directory structure**
```bash
mkdir -p ./cloud/{deploy,stacks,tools,api}
```

**Step 3: Migrate deployments**
```bash
# For each deployment
cloud migrate-deployment <deployment-id>
# Automatically:
# - Updates manifest (staging → stage)
# - Updates stack naming
# - Adds template dependencies
# - Validates migrated config
```

**Step 4: Migrate stack code**
```bash
# Move and update stacks
mv ./aws/build/* ./cloud/stacks/
# Update imports in each stack
# Update DependencyResolver usage
```

**Step 5: Test migration**
```bash
# Validate migrated deployment
cloud validate <deployment-id>

# Test in dev environment
cloud deploy <deployment-id> --environment dev --dry-run
```

See: Addendum_Changes_From_2.3.3.0.md for complete migration guide.

---

## Conclusion

This Q&A addendum covers common questions about Cloud Architecture v3.0. For additional questions:

1. **Check documentation**: All 15 documents provide comprehensive coverage
2. **Review examples**: Platform Code Addendum contains code examples
3. **Search codebase**: Well-commented code with JSDoc
4. **Community support**: GitHub issues and discussions

For detailed information, see:
- Main Architecture Document (Multi-Stack-Architecture-3.0.md)
- CLI Commands Reference (CLI_Commands_Reference.3.0.md)
- REST API Documentation (REST_API_Documentation.3.0.md)
- All Addendums (comprehensive specialized topics)
