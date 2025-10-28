# Security Stack Pulumi Generation Prompt

## Context
You are creating Pulumi TypeScript infrastructure code for security infrastructure with IAM roles, security groups, and KMS keys for the ${PROJECT_NAME} application. This stack provides the security foundation for all other services.

## Stack Requirements

### Primary Objectives
1. **Security Groups**: Create security groups for different tiers (web, app, database)
2. **IAM Roles**: Set up service roles for ECS, EKS, Lambda, and other AWS services
3. **KMS Keys**: Create encryption keys for applications, databases, and infrastructure
4. **Access Control**: Implement least-privilege access patterns
5. **State Integration**: Work with centralized cloud deployment system

### Dependencies
- **network**: Requires VPC ID for security group creation

### Required Outputs
```typescript
// Security Groups
- loadBalancerSgId: Load balancer security group ID
- webApplicationSgId: Web application security group ID
- apiApplicationSgId: API application security group ID
- databaseSgId: Database security group ID
// IAM Roles
- ecsExecutionRoleArn: ECS task execution role ARN
- ecsTaskRoleArn: ECS task role ARN
- eksClusterRoleArn: EKS cluster role ARN
// KMS Keys
- applicationKeyId: Application KMS key ID
- applicationKeyArn: Application KMS key ARN
- databaseKeyId: Database KMS key ID
- databaseKeyArn: Database KMS key ARN
```

### State Integration Requirements
- Use deployment variables: `${DEPLOYMENT_ID}`, `${ORG_NAME}`, `${PROJECT_NAME}`
- Tag all resources with deployment metadata
- Reference network stack outputs through centralized state
- Export outputs for dependent stacks (database, containers, etc.)

## Success Criteria
- [ ] Security groups created for all tiers with proper ingress/egress rules
- [ ] IAM roles created with appropriate trust policies and permissions
- [ ] KMS keys created with proper key policies and aliases
- [ ] All outputs properly exported for dependent stacks
- [ ] Resources tagged for centralized management