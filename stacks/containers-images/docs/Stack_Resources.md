# AWS Resources for Container Images Stack

## Docker Image Build Resources
- **aws.codebuild.Project** - Frontend React application build
- **aws.codebuild.Project** - Backend API application build
- **aws.codebuild.Project** - Background worker application build
- **aws.codebuild.Project** - Database migration scripts build
- **aws.codebuild.Project** - Nginx reverse proxy build

## Container Registry Resources
- **aws.ecr.Repository** - Frontend application image repository
- **aws.ecr.Repository** - Backend API image repository
- **aws.ecr.Repository** - Background worker image repository
- **aws.ecr.Repository** - Database utilities image repository
- **aws.ecr.Repository** - Nginx/proxy image repository
- **aws.ecr.Repository** - Base images repository (custom base)

## ECR Lifecycle Policies
- **aws.ecr.LifecyclePolicy** - Frontend image cleanup policy
- **aws.ecr.LifecyclePolicy** - Backend image cleanup policy
- **aws.ecr.LifecyclePolicy** - Worker image cleanup policy
- **aws.ecr.LifecyclePolicy** - Utilities image cleanup policy
- **aws.ecr.LifecyclePolicy** - Base image cleanup policy

## ECR Repository Policies
- **aws.ecr.RepositoryPolicy** - Frontend repository access policy
- **aws.ecr.RepositoryPolicy** - Backend repository access policy
- **aws.ecr.RepositoryPolicy** - Worker repository access policy
- **aws.ecr.RepositoryPolicy** - Cross-account access policy (if needed)

## CodeBuild IAM Resources
- **aws.iam.Role** - CodeBuild service role for image builds
- **aws.iam.Policy** - ECR push/pull permissions policy
- **aws.iam.Policy** - S3 access policy for build artifacts
- **aws.iam.Policy** - Secrets Manager access for build secrets
- **aws.iam.RolePolicyAttachment** - Attach ECR policy to build role
- **aws.iam.RolePolicyAttachment** - Attach S3 policy to build role
- **aws.iam.RolePolicyAttachment** - Attach Secrets policy to build role

## Build Triggers and Webhooks
- **aws.codebuild.Webhook** - GitHub webhook for frontend builds
- **aws.codebuild.Webhook** - GitHub webhook for backend builds
- **aws.codebuild.Webhook** - GitHub webhook for worker builds

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - Frontend build logs
- **aws.cloudwatch.LogGroup** - Backend build logs
- **aws.cloudwatch.LogGroup** - Worker build logs
- **aws.cloudwatch.LogGroup** - Migration build logs
- **aws.cloudwatch.Alarm** - Build failure alarm
- **aws.cloudwatch.Alarm** - Image scanning failure alarm

## Image Scanning and Security
- **aws.ecr.ScanConfiguration** - Image vulnerability scanning
- **aws.inspector.AssessmentTarget** - Container security assessment
- **aws.inspector.AssessmentTemplate** - Security assessment rules

## S3 Resources for Build Artifacts
- **aws.s3.Bucket** - Build artifacts and cache storage
- **aws.s3.BucketPolicy** - CodeBuild access to artifacts bucket
- **aws.s3.BucketVersioning** - Versioning for build artifacts
- **aws.s3.BucketLifecycleConfiguration** - Cleanup old build artifacts

## Image Deployment Automation
- **aws.lambda.Function** - Image deployment trigger
- **aws.lambda.Function** - Image tag promotion (dev → stage → prod)
- **aws.events.Rule** - ECR push event trigger
- **aws.events.Target** - Lambda target for ECR events

## Estimated Resource Count: 38-45 resources
## Estimated Monthly Cost:
- ECR storage: $0.10 per GB/month (estimated 5-10 GB)
- CodeBuild minutes: $0.005 per minute (estimated 500 build minutes/month)
- S3 artifacts storage: $0.023 per GB/month (estimated 2-5 GB)
- Lambda executions: $0.20 per 1M requests (minimal cost)
- Image scanning: $0.09 per image scan
- **Total: ~$5-15/month**

## Resource Dependencies
- Depends on: Security stack (IAM roles, KMS keys), Secrets stack (build secrets)
- Required by: ECS services, EKS deployments, Container applications