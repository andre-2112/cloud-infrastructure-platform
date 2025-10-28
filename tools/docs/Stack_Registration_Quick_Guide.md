# Stack Registration Quick Guide

**Status:** 0 of 16 stacks currently registered
**Priority:** Complete before deployments

---

## Current Situation

- **16 stacks** exist in `cloud/stacks/`
- **0 stacks** registered in `cloud/tools/templates/config/`
- Cannot use `cloud init` until stacks are registered

---

## Manual Registration Commands

```bash
# Network (Layer 1 - No dependencies)
cloud register-stack network --description "Core VPC and networking" --dependencies "" --priority 100

# Security (Layer 2)
cloud register-stack security --description "Security groups and IAM" --dependencies "network" --priority 200

# DNS (Layer 2)
cloud register-stack dns --description "Route53 DNS management" --dependencies "network" --priority 200

# Secrets (Layer 2)
cloud register-stack secrets --description "Secrets Manager" --dependencies "network" --priority 200

# Storage (Layer 2)
cloud register-stack storage --description "S3 buckets" --dependencies "network" --priority 200

# Database-RDS (Layer 3)
cloud register-stack database-rds --description "RDS databases" --dependencies "network,security" --priority 300

# Authentication (Layer 3)
cloud register-stack authentication --description "Cognito authentication" --dependencies "network,security" --priority 300

# Containers-Images (Layer 3)
cloud register-stack containers-images --description "ECR image repositories" --dependencies "network,security" --priority 300

# Compute-EC2 (Layer 3)
cloud register-stack compute-ec2 --description "EC2 instances" --dependencies "network,security" --priority 300

# Compute-Lambda (Layer 3)
cloud register-stack compute-lambda --description "Lambda functions" --dependencies "network,security" --priority 300

# Services-ECR (Layer 3)
cloud register-stack services-ecr --description "ECR service" --dependencies "network,security" --priority 300

# Monitoring (Layer 3)
cloud register-stack monitoring --description "CloudWatch monitoring" --dependencies "network,security" --priority 300

# Services-ECS (Layer 4)
cloud register-stack services-ecs --description "ECS clusters" --dependencies "network,security,containers-images" --priority 400

# Services-EKS (Layer 4)
cloud register-stack services-eks --description "EKS clusters" --dependencies "network,security,containers-images" --priority 400

# Containers-Apps (Layer 5)
cloud register-stack containers-apps --description "Container applications" --dependencies "network,security,services-ecs" --priority 500

# Services-API (Layer 5)
cloud register-stack services-api --description "API Gateway" --dependencies "network,security,compute-lambda" --priority 500
```

---

## Batch Registration Script Option

Create `tools/scripts/register-all-stacks.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")/../.."

declare -A STACKS=(
  ["network"]="Core VPC and networking::"
  ["security"]="Security groups and IAM:network:"
  ["dns"]="Route53 DNS management:network:"
  ["secrets"]="Secrets Manager:network:"
  ["storage"]="S3 buckets:network:"
  ["database-rds"]="RDS databases:network,security:"
  ["authentication"]="Cognito authentication:network,security:"
  ["containers-images"]="ECR image repositories:network,security:"
  ["compute-ec2"]="EC2 instances:network,security:"
  ["compute-lambda"]="Lambda functions:network,security:"
  ["services-ecr"]="ECR service:network,security:"
  ["monitoring"]="CloudWatch monitoring:network,security:"
  ["services-ecs"]="ECS clusters:network,security,containers-images:"
  ["services-eks"]="EKS clusters:network,security,containers-images:"
  ["containers-apps"]="Container applications:network,security,services-ecs:"
  ["services-api"]="API Gateway:network,security,compute-lambda:"
)

for stack_name in "${!STACKS[@]}"; do
  IFS=':' read -r description dependencies <<< "${STACKS[$stack_name]}"

  echo "Registering: $stack_name"
  cloud register-stack "$stack_name" \
    --description "$description" \
    --dependencies "$dependencies"
done

echo "✓ All stacks registered"
cloud list-stacks
```

---

## Future Auto-Discovery Command

**Recommended enhancement:**

```bash
cloud register-all-stacks --auto-discover
```

Would automatically:
1. Scan `stacks/` directory
2. Parse `Pulumi.yaml` for metadata
3. Infer dependencies from import statements
4. Register all stacks with sensible defaults

---

**End of Guide**
