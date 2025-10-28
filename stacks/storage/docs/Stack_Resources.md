# AWS Resources for Storage Stack

## S3 Resources
- **aws.s3.Bucket** - Primary data storage bucket with versioning
- **aws.s3.Bucket** - Static assets storage bucket for web content
- **aws.s3.Bucket** - Logs storage bucket for centralized logging
- **aws.s3.Bucket** - Backup storage bucket for database backups
- **aws.s3.Bucket** - Artifacts storage bucket for CI/CD deployments
- **aws.s3.BucketVersioning** - Versioning configuration for primary bucket
- **aws.s3.BucketEncryption** - Server-side encryption for all buckets
- **aws.s3.BucketPublicAccessBlock** - Public access restrictions
- **aws.s3.BucketLifecycleConfiguration** - Lifecycle policies for cost optimization
- **aws.s3.BucketNotification** - Event notifications for bucket changes
- **aws.s3.BucketCorsConfiguration** - CORS configuration for web access
- **aws.s3.BucketLogging** - Access logging configuration

## EBS Resources
- **aws.ebs.Volume** - Additional storage volumes for EC2 instances
- **aws.ebs.Snapshot** - Automated snapshots for backup
- **aws.ebs.EncryptionByDefault** - Default EBS encryption settings

## EFS Resources
- **aws.efs.FileSystem** - Elastic File System for shared storage
- **aws.efs.MountTarget** - Mount targets in each availability zone
- **aws.efs.AccessPoint** - Access points for secure file system access
- **aws.efs.BackupPolicy** - Automated backup configuration

## FSx Resources (Optional)
- **aws.fsx.LustreFileSystem** - High-performance file system for compute workloads

## Glacier Resources
- **aws.glacier.Vault** - Long-term archival storage
- **aws.glacier.VaultNotification** - Notification configuration for vault operations

## Storage Gateway Resources (Optional)
- **aws.storagegateway.Gateway** - Hybrid cloud storage integration

## Backup Resources
- **aws.backup.Vault** - Centralized backup vault
- **aws.backup.Plan** - Backup plans for different resource types
- **aws.backup.Selection** - Resource selection for backup plans

## Data Sync Resources
- **aws.datasync.LocationS3** - DataSync location for S3
- **aws.datasync.Task** - Data synchronization tasks

## VPC Endpoint Resources
- **aws.ec2.VpcEndpoint** - S3 VPC endpoint for private access
- **aws.ec2.VpcEndpoint** - EFS VPC endpoint for private access

## Estimated Resource Count: 32 resources
## Estimated Monthly Cost: $50-200 (depending on storage usage)

## Resource Dependencies
- Depends on: network (VPC, subnets), security (KMS keys, IAM roles)
- Used by: compute-ec2, compute-lambda, containers-apps, services-api