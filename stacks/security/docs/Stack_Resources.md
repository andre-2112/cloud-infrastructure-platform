# AWS Resources for Security Stack

## Security Groups
- **aws.ec2.SecurityGroup** - Load balancer security group (ALB public access)
- **aws.ec2.SecurityGroup** - Web application security group (Node.js containers)
- **aws.ec2.SecurityGroup** - API application security group (FastAPI containers)
- **aws.ec2.SecurityGroup** - Database security group (RDS PostgreSQL)
- **aws.ec2.SecurityGroup** - ECS cluster security group (container communication)
- **aws.ec2.SecurityGroup** - EKS cluster security group (Kubernetes control plane)
- **aws.ec2.SecurityGroup** - EKS node group security group (worker nodes)
- **aws.ec2.SecurityGroup** - Bastion host security group (SSH access, optional)
- **aws.ec2.SecurityGroup** - VPC endpoints security group (private AWS service access)
- **aws.ec2.SecurityGroup** - Lambda functions security group (serverless functions)

## IAM Roles and Policies
- **aws.iam.Role** - ECS task execution role (Fargate container management)
- **aws.iam.Role** - ECS task role (application-level permissions)
- **aws.iam.Role** - EKS cluster service role (Kubernetes cluster management)
- **aws.iam.Role** - EKS node group role (worker node permissions)
- **aws.iam.Role** - Lambda execution role (serverless function permissions)
- **aws.iam.Role** - EC2 instance profile role (EC2 service permissions)
- **aws.iam.Role** - CodeBuild service role (CI/CD pipeline permissions)
- **aws.iam.Role** - VPC Flow Logs role (network logging permissions)

## IAM Policies (Custom)
- **aws.iam.Policy** - Secrets Manager access policy (database credentials)
- **aws.iam.Policy** - ECR access policy (container image management)
- **aws.iam.Policy** - S3 bucket access policy (application data storage)
- **aws.iam.Policy** - CloudWatch Logs policy (application logging)
- **aws.iam.Policy** - Parameter Store access policy (configuration management)
- **aws.iam.Policy** - KMS key usage policy (encryption/decryption)

## IAM Policy Attachments
- **aws.iam.RolePolicyAttachment** - ECS execution role managed policies (8x)
- **aws.iam.RolePolicyAttachment** - EKS cluster role managed policies (3x)
- **aws.iam.RolePolicyAttachment** - EKS node group role managed policies (4x)
- **aws.iam.RolePolicyAttachment** - Lambda role managed policies (2x)
- **aws.iam.RolePolicyAttachment** - Custom policy attachments (6x)

## IAM Instance Profiles
- **aws.iam.InstanceProfile** - EC2 instance profile (bastion, worker nodes)
- **aws.iam.InstanceProfile** - EKS node group instance profile

## KMS Resources
- **aws.kms.Key** - Application encryption key (app secrets, logs, S3)
- **aws.kms.Key** - Database encryption key (RDS, backups, snapshots)
- **aws.kms.Key** - Infrastructure encryption key (CloudTrail, Config)
- **aws.kms.Alias** - Application key alias (${PROJECT_NAME}-app-key)
- **aws.kms.Alias** - Database key alias (${PROJECT_NAME}-db-key)
- **aws.kms.Alias** - Infrastructure key alias (${PROJECT_NAME}-infra-key)

## KMS Key Policies
- **aws.kms.KeyPolicy** - Application key usage policy
- **aws.kms.KeyPolicy** - Database key usage policy
- **aws.kms.KeyPolicy** - Infrastructure key usage policy

## Service-Linked Roles (Auto-created)
- **aws.iam.ServiceLinkedRole** - ECS service-linked role
- **aws.iam.ServiceLinkedRole** - EKS service-linked role
- **aws.iam.ServiceLinkedRole** - RDS service-linked role
- **aws.iam.ServiceLinkedRole** - ElastiCache service-linked role

## Estimated Resource Count: 45-50 resources
## Estimated Monthly Cost:
- KMS Keys: $3.00 (3 keys × $1/month each)
- Service-linked roles: Free
- Security groups: Free
- IAM roles/policies: Free
- **Total: ~$3/month**

## Resource Dependencies
- Depends on: Network stack (VPC ID for security groups)
- Required by: Database, ECS, EKS, Lambda, Storage, Monitoring