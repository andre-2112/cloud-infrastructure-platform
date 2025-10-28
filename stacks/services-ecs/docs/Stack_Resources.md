# AWS Resources for ECS Services Stack

## ECS Cluster Resources
- **aws.ecs.Cluster** - Main ECS cluster for containerized applications
- **aws.ecs.ClusterCapacityProvider** - Fargate capacity provider
- **aws.ecs.ClusterCapacityProvider** - EC2 capacity provider (optional)
- **aws.ecs.CapacityProvider** - Custom capacity provider configuration

## ECS Task Definitions
- **aws.ecs.TaskDefinition** - Web application task definition
- **aws.ecs.TaskDefinition** - API service task definition
- **aws.ecs.TaskDefinition** - Background worker task definition
- **aws.ecs.TaskDefinition** - Database migration task definition
- **aws.ecs.TaskDefinition** - Scheduled maintenance task definition

## ECS Services
- **aws.ecs.Service** - Web application service
- **aws.ecs.Service** - API service
- **aws.ecs.Service** - Background worker service
- **aws.ecs.Service** - Long-running daemon service

## Auto Scaling Resources
- **aws.appautoscaling.Target** - Web service scaling target
- **aws.appautoscaling.Target** - API service scaling target
- **aws.appautoscaling.Policy** - CPU-based scaling policy
- **aws.appautoscaling.Policy** - Memory-based scaling policy
- **aws.appautoscaling.Policy** - Custom metrics scaling policy

## Load Balancer Integration
- **aws.lb.TargetGroup** - Web application target group
- **aws.lb.TargetGroup** - API service target group
- **aws.lb.TargetGroup** - Health check target group
- **aws.lb.ListenerRule** - Application routing rules

## Service Discovery
- **aws.servicediscovery.PrivateDnsNamespace** - Private DNS namespace
- **aws.servicediscovery.Service** - Web service discovery
- **aws.servicediscovery.Service** - API service discovery
- **aws.servicediscovery.Service** - Worker service discovery

## IAM Resources for ECS
- **aws.iam.Role** - ECS cluster service role
- **aws.iam.Role** - ECS task execution role
- **aws.iam.Role** - ECS task role (application permissions)
- **aws.iam.Role** - ECS instance role (for EC2 launch type)
- **aws.iam.Policy** - ECS service permissions policy
- **aws.iam.Policy** - Task-specific permissions policy
- **aws.iam.InstanceProfile** - EC2 instance profile (if using EC2 launch type)

## ECS Security Resources
- **aws.ec2.SecurityGroup** - ECS cluster security group
- **aws.ec2.SecurityGroup** - Application container security group
- **aws.ec2.SecurityGroup** - Database connection security group

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - ECS cluster logs
- **aws.cloudwatch.LogGroup** - Web application logs
- **aws.cloudwatch.LogGroup** - API service logs
- **aws.cloudwatch.LogGroup** - Background worker logs
- **aws.cloudwatch.Alarm** - High CPU utilization alarm
- **aws.cloudwatch.Alarm** - High memory utilization alarm
- **aws.cloudwatch.Alarm** - Service health alarm
- **aws.cloudwatch.Alarm** - Task failure alarm

## ECS Task Scheduling
- **aws.events.Rule** - Scheduled task events
- **aws.events.Target** - ECS task targets for scheduled events
- **aws.ecs.TaskSet** - Blue/green deployment task sets

## Container Insights and Monitoring
- **aws.ecs.ClusterSetting** - Container Insights enablement
- **aws.cloudwatch.Dashboard** - ECS cluster dashboard
- **aws.cloudwatch.Dashboard** - Application metrics dashboard

## ECS Exec and Debugging
- **aws.iam.Policy** - ECS Exec permissions policy
- **aws.ssm.Document** - Custom SSM documents for debugging

## Storage and Volumes
- **aws.efs.FileSystem** - Shared file system for containers
- **aws.efs.MountTarget** - EFS mount targets
- **aws.efs.AccessPoint** - EFS access points for applications

## Estimated Resource Count: 42-50 resources
## Estimated Monthly Cost:
- ECS cluster: Free (pay for underlying compute)
- Fargate tasks: $0.04048 per vCPU/hour + $0.004445 per GB/hour
- Application Load Balancer: $16-25/month
- CloudWatch logs: $0.50 per GB ingested
- EFS storage: $0.30 per GB/month (if used)
- **Total: ~$50-200/month** (varies significantly with scale)

## Resource Dependencies
- Depends on: Network stack (VPC, subnets), Security stack (IAM roles, security groups), ECR stack (container images), Load balancer resources
- Required by: Application services, Monitoring stack, Service mesh (if implemented)