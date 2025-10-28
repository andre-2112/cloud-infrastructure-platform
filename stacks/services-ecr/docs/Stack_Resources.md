# AWS Resources for ECR Services Stack

## ECR Registry Management
- **aws.ecr.RegistryPolicy** - Cross-account registry access policy
- **aws.ecr.RegistryScanningConfiguration** - Registry-wide scanning settings
- **aws.ecr.ReplicationConfiguration** - Cross-region replication rules

## Container Repository Resources
- **aws.ecr.Repository** - Application container repositories
- **aws.ecr.Repository** - Infrastructure tooling repositories
- **aws.ecr.Repository** - Third-party base image mirrors
- **aws.ecr.Repository** - Custom runtime environments

## Repository Security and Policies
- **aws.ecr.RepositoryPolicy** - Fine-grained access control policies
- **aws.ecr.LifecyclePolicy** - Image lifecycle management policies
- **aws.iam.Policy** - ECR access policies for different roles
- **aws.iam.RolePolicyAttachment** - Policy attachments for service roles

## Image Security Scanning
- **aws.ecr.ScanConfiguration** - Enhanced vulnerability scanning
- **aws.inspector.AssessmentTarget** - Container image assessments
- **aws.inspector.AssessmentTemplate** - Security assessment templates
- **aws.config.ConfigRule** - ECR compliance monitoring

## Registry Automation
- **aws.lambda.Function** - Image promotion automation
- **aws.lambda.Function** - Security scan result processing
- **aws.lambda.Function** - Repository cleanup automation
- **aws.events.Rule** - ECR event triggers
- **aws.events.Target** - Lambda function targets

## Cross-Region Replication
- **aws.ecr.ReplicationConfiguration** - Multi-region image replication
- **aws.iam.Role** - Cross-region replication service role
- **aws.iam.Policy** - Replication permissions policy

## Monitoring and Alerting
- **aws.cloudwatch.LogGroup** - ECR API activity logs
- **aws.cloudwatch.Alarm** - Repository storage quota alarms
- **aws.cloudwatch.Alarm** - Image push/pull failure alarms
- **aws.cloudwatch.Alarm** - Security scan failure alarms
- **aws.cloudwatch.Dashboard** - ECR metrics dashboard

## Registry Cache and Performance
- **aws.ecr.PullThroughCacheRule** - Cache rules for external registries
- **aws.cloudfront.Distribution** - ECR content delivery network (optional)

## Backup and Disaster Recovery
- **aws.backup.Plan** - ECR repository backup plan
- **aws.backup.Vault** - Backup storage vault
- **aws.backup.Selection** - Resource selection for backup

## IAM Service Integration
- **aws.iam.Role** - ECR service-linked roles
- **aws.iam.Policy** - ECR resource-based policies
- **aws.iam.ServiceLinkedRole** - AWS service integrations

## Repository Tagging and Organization
- **aws.resourcegroupstaggingapi.Tag** - Repository resource tagging
- **aws.organizations.Policy** - Organization-wide ECR policies (if applicable)

## Cost Management
- **aws.budgets.Budget** - ECR storage cost monitoring
- **aws.ce.CostCategory** - ECR cost categorization

## Estimated Resource Count: 28-35 resources
## Estimated Monthly Cost:
- ECR storage: $0.10 per GB/month
- Data transfer: $0.02-0.09 per GB (region dependent)
- Image scanning: $0.09 per image scan
- Cross-region replication: Additional data transfer costs
- Lambda automation: $0.20 per 1M requests (minimal)
- **Total: ~$2-10/month** (scales with image storage and usage)

## Resource Dependencies
- Depends on: Security stack (IAM roles and policies)
- Required by: Container images stack, ECS services, EKS clusters, CI/CD pipelines