# AWS Resources for Secrets Stack

## Secrets Manager Resources
- **aws.secretsmanager.Secret** - Database master password (postgres user)
- **aws.secretsmanager.Secret** - Database read-only user password
- **aws.secretsmanager.Secret** - Database connection string (write)
- **aws.secretsmanager.Secret** - Database connection string (read)
- **aws.secretsmanager.Secret** - JWT signing key for authentication
- **aws.secretsmanager.Secret** - Session secret key for web sessions
- **aws.secretsmanager.Secret** - API keys for external services (Stripe, SendGrid, etc.)
- **aws.secretsmanager.Secret** - OAuth client secrets (Google, GitHub, etc.)
- **aws.secretsmanager.Secret** - Application configuration secrets
- **aws.secretsmanager.Secret** - Redis password (if using ElastiCache)
- **aws.secretsmanager.Secret** - Encryption keys for application data

## Secret Versions
- **aws.secretsmanager.SecretVersion** - Database master password version
- **aws.secretsmanager.SecretVersion** - Database read-only password version
- **aws.secretsmanager.SecretVersion** - JWT signing key version
- **aws.secretsmanager.SecretVersion** - Session secret version
- **aws.secretsmanager.SecretVersion** - API keys version
- **aws.secretsmanager.SecretVersion** - OAuth secrets version
- **aws.secretsmanager.SecretVersion** - Application config version
- **aws.secretsmanager.SecretVersion** - Redis password version
- **aws.secretsmanager.SecretVersion** - Encryption keys version

## Secret Rotation (Lambda-based)
- **aws.secretsmanager.SecretRotation** - Database master password rotation
- **aws.secretsmanager.SecretRotation** - Database read-only password rotation
- **aws.lambda.Function** - Database password rotation Lambda
- **aws.lambda.Function** - Generic secret rotation Lambda
- **aws.iam.Role** - Lambda rotation execution role

## IAM Resources for Secrets Access
- **aws.iam.Policy** - Secrets Manager read access policy (application level)
- **aws.iam.Policy** - Secrets Manager write access policy (rotation level)
- **aws.iam.Policy** - Secrets Manager admin access policy (management level)
- **aws.iam.RolePolicyAttachment** - Attach read policy to ECS task role
- **aws.iam.RolePolicyAttachment** - Attach read policy to Lambda execution role
- **aws.iam.RolePolicyAttachment** - Attach rotation policy to rotation Lambda role

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - Secret rotation Lambda logs
- **aws.cloudwatch.LogGroup** - Secret access audit logs
- **aws.cloudwatch.Alarm** - Failed secret retrieval alarm
- **aws.cloudwatch.Alarm** - Secret rotation failure alarm

## VPC Endpoint (Optional)
- **aws.ec2.VpcEndpoint** - Secrets Manager VPC endpoint (if using private access)

## Estimated Resource Count: 32-35 resources
## Estimated Monthly Cost:
- Secrets (11 secrets): $4.40 ($0.40 each)
- API calls: $0.05 per 10,000 requests
- Lambda rotation: $0.10-0.50 (minimal usage)
- CloudWatch logs: $0.50-2.00
- **Total: ~$5-7/month**

## Resource Dependencies
- Depends on: Security stack (KMS keys for encryption)
- Required by: Database, ECS services, Lambda functions, Authentication