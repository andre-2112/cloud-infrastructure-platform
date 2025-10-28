# AWS Resources for Compute EC2 Stack

## EC2 Instance Resources
- **aws.ec2.Instance** - Web application servers
- **aws.ec2.Instance** - Database servers (if not using RDS)
- **aws.ec2.Instance** - Background processing servers
- **aws.ec2.Instance** - Monitoring and logging servers
- **aws.ec2.Instance** - Development and testing servers

## Auto Scaling Resources
- **aws.autoscaling.Group** - Auto Scaling Group for web servers
- **aws.autoscaling.Group** - Auto Scaling Group for worker servers
- **aws.autoscaling.Policy** - Scale up policies
- **aws.autoscaling.Policy** - Scale down policies
- **aws.autoscaling.Notification** - Scaling notifications

## Launch Template Resources
- **aws.ec2.LaunchTemplate** - Launch template for web servers
- **aws.ec2.LaunchTemplate** - Launch template for worker servers

## Load Balancer Resources
- **aws.lb.LoadBalancer** - Application Load Balancer for EC2 instances
- **aws.lb.TargetGroup** - Target group for web servers
- **aws.lb.TargetGroup** - Target group for API servers
- **aws.lb.Listener** - HTTPS listener
- **aws.lb.Listener** - HTTP redirect listener
- **aws.lb.ListenerRule** - Routing rules for different paths

## EBS Volume Resources
- **aws.ebs.Volume** - Additional storage volumes
- **aws.ebs.VolumeAttachment** - Volume attachments to instances

## Elastic IP Resources
- **aws.ec2.Eip** - Elastic IPs for NAT instances (if not using NAT Gateway)
- **aws.ec2.EipAssociation** - EIP associations

## Placement Group Resources
- **aws.ec2.PlacementGroup** - Placement groups for high-performance instances

## Key Pair Resources
- **aws.ec2.KeyPair** - SSH key pairs for instance access

## Instance Profile Resources
- **aws.iam.InstanceProfile** - EC2 instance profiles
- **aws.iam.RolePolicyAttachment** - Policy attachments for instance roles

## CloudWatch Resources
- **aws.cloudwatch.MetricAlarm** - CPU utilization alarms
- **aws.cloudwatch.MetricAlarm** - Memory utilization alarms
- **aws.cloudwatch.MetricAlarm** - Disk utilization alarms
- **aws.cloudwatch.Dashboard** - EC2 monitoring dashboard

## Systems Manager Resources
- **aws.ssm.Association** - SSM document associations
- **aws.ssm.MaintenanceWindow** - Maintenance windows
- **aws.ssm.MaintenanceWindowTarget** - Maintenance window targets
- **aws.ssm.MaintenanceWindowTask** - Maintenance window tasks

## Backup Resources
- **aws.dlm.LifecyclePolicy** - EBS snapshot lifecycle policies

## Spot Fleet Resources (Optional)
- **aws.ec2.SpotFleetRequest** - Spot fleet for cost optimization

## Network Interface Resources
- **aws.ec2.NetworkInterface** - Additional network interfaces
- **aws.ec2.NetworkInterfaceAttachment** - Network interface attachments

## Estimated Resource Count: 45 resources
## Estimated Monthly Cost: $200-800 (depending on instance types and usage)

## Resource Dependencies
- Depends on: network, security, storage
- Used by: services-api, services-webapp, monitoring