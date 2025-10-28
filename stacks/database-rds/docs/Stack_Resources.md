# AWS Resources for Database RDS Stack

## RDS Instance Resources
- **aws.rds.Instance** - Primary PostgreSQL database instance
- **aws.rds.Instance** - Read replica instance (production)
- **aws.rds.ClusterParameterGroup** - Custom parameter group for performance tuning
- **aws.rds.ParameterGroup** - Instance-level parameter group
- **aws.rds.OptionGroup** - Database options and features

## RDS Subnet Group
- **aws.rds.SubnetGroup** - Database subnet group (private subnets)

## RDS Security and Backup
- **aws.rds.Snapshot** - Manual snapshots for backup
- **aws.rds.ClusterSnapshot** - Cluster-level snapshots
- **aws.db.EventSubscription** - Database event notifications

## Database Users and Permissions
- **aws.rds.RoleAssociation** - IAM database authentication roles
- **aws.rds.Certificate** - SSL certificate for encrypted connections

## Monitoring and Performance
- **aws.rds.PerformanceInsightsEnabled** - Performance monitoring
- **aws.cloudwatch.LogGroup** - PostgreSQL log group
- **aws.cloudwatch.LogGroup** - Slow query log group
- **aws.cloudwatch.Alarm** - CPU utilization alarm
- **aws.cloudwatch.Alarm** - Database connections alarm
- **aws.cloudwatch.Alarm** - Free storage space alarm
- **aws.cloudwatch.Alarm** - Read/write latency alarms

## Database Proxy (Optional)
- **aws.rds.Proxy** - RDS Proxy for connection pooling
- **aws.rds.ProxyDefaultTargetGroup** - Target group configuration
- **aws.rds.ProxyEndpoint** - Proxy endpoint configuration

## Backup and Maintenance
- **aws.rds.AutomaticBackup** - Automated backup configuration
- **aws.rds.MaintenanceWindow** - Maintenance window scheduling
- **aws.rds.BackupRetentionPeriod** - Backup retention settings

## ElastiCache (Redis) - Optional
- **aws.elasticache.SubnetGroup** - Cache subnet group
- **aws.elasticache.ReplicationGroup** - Redis cluster for caching
- **aws.elasticache.ParameterGroup** - Redis configuration parameters
- **aws.elasticache.User** - Redis user for authentication
- **aws.elasticache.UserGroup** - Redis user group management

## Database Migration (Optional)
- **aws.dms.ReplicationInstance** - Data migration instance
- **aws.dms.ReplicationTask** - Migration task configuration
- **aws.dms.Endpoint** - Source and target endpoints

## Secrets Integration
- **aws.secretsmanager.SecretTargetAttachment** - Link secrets to RDS instance

## Estimated Resource Count: 25-35 resources
## Estimated Monthly Cost:
- RDS instance (db.t3.medium): $70-90/month
- Read replica: $70-90/month (production only)
- ElastiCache (cache.t3.micro): $15-20/month
- Storage (100GB): $10-15/month
- Backup storage: $5-10/month
- **Total: ~$100-200/month** (depending on environment)

## Resource Dependencies
- Depends on: Network stack (subnets), Security stack (security groups, KMS), Secrets stack (passwords)
- Required by: Application services, ECS tasks, Lambda functions