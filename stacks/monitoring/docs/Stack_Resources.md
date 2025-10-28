# AWS Resources for Monitoring Stack

## CloudWatch Dashboards
- **aws.cloudwatch.Dashboard** - Infrastructure overview dashboard
- **aws.cloudwatch.Dashboard** - Application performance dashboard
- **aws.cloudwatch.Dashboard** - Database performance dashboard
- **aws.cloudwatch.Dashboard** - Security and compliance dashboard
- **aws.cloudwatch.Dashboard** - Cost and billing dashboard

## CloudWatch Alarms
- **aws.cloudwatch.Alarm** - High CPU utilization alarms
- **aws.cloudwatch.Alarm** - High memory utilization alarms
- **aws.cloudwatch.Alarm** - High disk utilization alarms
- **aws.cloudwatch.Alarm** - Network performance alarms
- **aws.cloudwatch.Alarm** - Application error rate alarms
- **aws.cloudwatch.Alarm** - Database connection alarms
- **aws.cloudwatch.Alarm** - Load balancer health alarms
- **aws.cloudwatch.Alarm** - SSL certificate expiration alarms

## CloudWatch Metrics and Custom Metrics
- **aws.cloudwatch.MetricFilter** - Application log metric filters
- **aws.cloudwatch.MetricFilter** - Error log metric filters
- **aws.cloudwatch.MetricFilter** - Security event metric filters
- **aws.logs.MetricFilter** - Custom business metrics

## Log Management
- **aws.cloudwatch.LogGroup** - Application logs aggregation
- **aws.cloudwatch.LogGroup** - Infrastructure logs
- **aws.cloudwatch.LogGroup** - Security audit logs
- **aws.cloudwatch.LogGroup** - Performance logs
- **aws.logs.LogStream** - Application-specific log streams

## SNS Notification Resources
- **aws.sns.Topic** - Critical alerts topic
- **aws.sns.Topic** - Warning alerts topic
- **aws.sns.Topic** - Info notifications topic
- **aws.sns.Subscription** - Email notifications for critical alerts
- **aws.sns.Subscription** - SMS notifications for critical alerts
- **aws.sns.Subscription** - Slack webhook notifications

## EventBridge Integration
- **aws.events.Rule** - Infrastructure event rules
- **aws.events.Rule** - Application event rules
- **aws.events.Rule** - Security event rules
- **aws.events.Target** - SNS targets for event rules
- **aws.events.Target** - Lambda targets for event processing

## X-Ray Tracing (Optional)
- **aws.xray.SamplingRule** - Application tracing sampling rules
- **aws.xray.EncryptionConfig** - X-Ray data encryption configuration

## Systems Manager Integration
- **aws.ssm.MaintenanceWindow** - Infrastructure maintenance windows
- **aws.ssm.MaintenanceWindowTarget** - Target resources for maintenance
- **aws.ssm.MaintenanceWindowTask** - Maintenance tasks

## CloudTrail Integration
- **aws.cloudtrail.Trail** - API activity monitoring trail
- **aws.cloudtrail.EventDataStore** - Advanced event analytics
- **aws.s3.Bucket** - CloudTrail logs storage bucket
- **aws.s3.BucketPolicy** - CloudTrail bucket access policy

## Config Rules and Compliance
- **aws.config.ConfigurationRecorder** - Resource configuration tracking
- **aws.config.DeliveryChannel** - Config data delivery
- **aws.config.ConfigRule** - Security compliance rules
- **aws.config.ConfigRule** - Cost optimization rules
- **aws.config.ConfigRule** - Operational excellence rules

## Performance Monitoring
- **aws.applicationinsights.Application** - Application performance insights
- **aws.synthetics.Canary** - Website uptime monitoring canary
- **aws.synthetics.Canary** - API endpoint monitoring canary
- **aws.synthetics.Canary** - User journey monitoring canary

## Lambda Functions for Automation
- **aws.lambda.Function** - Alert processing and routing
- **aws.lambda.Function** - Automated remediation actions
- **aws.lambda.Function** - Custom metric collection
- **aws.lambda.Function** - Report generation and distribution

## IAM Resources for Monitoring
- **aws.iam.Role** - CloudWatch agent role
- **aws.iam.Role** - Lambda automation role
- **aws.iam.Role** - Config service role
- **aws.iam.Role** - CloudTrail service role
- **aws.iam.Policy** - Monitoring permissions policy
- **aws.iam.Policy** - Alert processing policy

## Cost and Billing Monitoring
- **aws.budgets.Budget** - Monthly cost budget
- **aws.budgets.Budget** - Service-specific budgets
- **aws.ce.AnomalyDetector** - Cost anomaly detection
- **aws.ce.AnomalyMonitor** - Cost anomaly monitoring

## Backup Monitoring
- **aws.backup.Plan** - Backup plan for critical resources
- **aws.backup.Vault** - Backup storage vault
- **aws.backup.Selection** - Resource backup selection

## Estimated Resource Count: 55-70 resources
## Estimated Monthly Cost:
- CloudWatch metrics: $0.30 per metric/month
- CloudWatch logs: $0.50 per GB ingested
- CloudWatch alarms: $0.10 per alarm/month
- SNS notifications: $0.50 per 1M requests
- X-Ray tracing: $5.00 per 1M traces (if used)
- Synthetics canaries: $0.0012 per canary run
- **Total: ~$20-100/month** (scales with metrics and log volume)

## Resource Dependencies
- Depends on: All other stacks (monitors their resources)
- Required by: DevOps teams, SRE processes, Compliance reporting