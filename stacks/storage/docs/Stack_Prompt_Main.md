# Storage Stack Pulumi Generation Prompt

Create production-ready Pulumi TypeScript code for AWS storage infrastructure including S3 buckets, EFS file systems, backup services, and VPC endpoints for ${PROJECT_NAME}.

## Requirements

### Core Infrastructure
- **S3 Buckets**: Primary storage, static assets, logs, backups, and artifacts with proper versioning, encryption, and lifecycle policies
- **EFS File Systems**: Shared storage with mount targets across all AZs and secure access points
- **VPC Endpoints**: Private S3 access without internet gateway dependency
- **AWS Backup**: Centralized backup vault with automated backup plans for EBS volumes and other resources
- **Lifecycle Management**: Cost optimization through intelligent storage class transitions

### Security and Compliance
- All storage encrypted using KMS keys from security stack
- Public access blocked on all S3 buckets
- Proper IAM policies for cross-service access
- VPC endpoints for secure private access to S3 services

### Dependencies and Integration
- **Network Stack**: VPC ID, private subnets, private route table IDs for VPC endpoints
- **Security Stack**: KMS keys for encryption, security groups for EFS access
- **Centralized State**: Use shared state management for cross-stack communication

### Environment Configuration
- Development: Smaller storage allocations, shorter retention periods
- Production: High availability, longer retention, more robust backup policies
- Cost optimization through appropriate storage classes and lifecycle rules

### Key Outputs Required
```typescript
export const primaryBucketName = primaryStorageBucket.bucket;
export const primaryBucketArn = primaryStorageBucket.arn;
export const staticAssetsBucketName = staticAssetsBucket.bucket;
export const staticAssetsBucketArn = staticAssetsBucket.arn;
export const logsBucketName = logsBucket.bucket;
export const backupBucketName = backupBucket.bucket;
export const artifactsBucketName = artifactsBucket.bucket;
export const sharedEfsId = sharedEfs.id;
export const sharedEfsDnsName = sharedEfs.dnsName;
export const appAccessPointId = appAccessPoint.id;
export const backupVaultArn = backupVault.arn;
export const s3VpcEndpointId = s3VpcEndpoint.id;
```

### Variables to Use
- **${DEPLOYMENT_ID}**: Unique deployment identifier
- **${PROJECT_NAME}**: Project name for resource naming and tagging
- **${DEPLOY_DOMAIN}**: Primary domain for CORS and access policies
- **${AWS_REGION}**: Target AWS region for deployment
- **Environment-specific**: Use centralized state to determine dev/stage/prod configurations

### Integration Notes
- Ensure all resources are properly tagged for cost allocation and management
- Configure S3 bucket notifications for file processing workflows
- Set up proper CORS policies for web application access to static assets
- Implement backup policies that align with RTO/RPO requirements
- Use consistent naming patterns with other stacks in the system

This stack provides the foundational storage layer that will be used by compute instances, Lambda functions, containerized applications, and backup systems throughout the infrastructure.