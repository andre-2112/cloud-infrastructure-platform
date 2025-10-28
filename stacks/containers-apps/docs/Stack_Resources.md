# AWS Resources for Container Applications Stack

## Application Load Balancer Resources
- **aws.lb.LoadBalancer** - Public application load balancer
- **aws.lb.LoadBalancer** - Internal application load balancer (optional)
- **aws.lb.TargetGroup** - Frontend application target group
- **aws.lb.TargetGroup** - Backend API target group
- **aws.lb.TargetGroup** - Health check target group
- **aws.lb.Listener** - HTTP listener (port 80)
- **aws.lb.Listener** - HTTPS listener (port 443)
- **aws.lb.ListenerRule** - Frontend routing rules
- **aws.lb.ListenerRule** - API routing rules
- **aws.lb.ListenerRule** - Health check routing

## Application Containers
- **aws.ecs.TaskDefinition** - Frontend React application task
- **aws.ecs.TaskDefinition** - Backend FastAPI application task
- **aws.ecs.TaskDefinition** - Background worker task
- **aws.ecs.TaskDefinition** - Database migration task
- **aws.ecs.TaskDefinition** - Nginx reverse proxy task

## ECS Service Resources
- **aws.ecs.Service** - Frontend application service
- **aws.ecs.Service** - Backend API service
- **aws.ecs.Service** - Background worker service
- **aws.ecs.Service** - Scheduled task service (cron jobs)

## Auto Scaling Resources
- **aws.autoscaling.Target** - Frontend service scaling target
- **aws.autoscaling.Target** - Backend service scaling target
- **aws.autoscaling.Policy** - CPU-based scaling policy
- **aws.autoscaling.Policy** - Memory-based scaling policy
- **aws.autoscaling.Policy** - Request count scaling policy

## Service Discovery
- **aws.servicediscovery.PrivateDnsNamespace** - Internal service discovery
- **aws.servicediscovery.Service** - Frontend service registration
- **aws.servicediscovery.Service** - Backend service registration
- **aws.servicediscovery.Service** - Worker service registration

## Container Networking
- **aws.ec2.SecurityGroup** - ALB security group
- **aws.ec2.SecurityGroup** - Frontend container security group
- **aws.ec2.SecurityGroup** - Backend container security group
- **aws.ec2.SecurityGroup** - Worker container security group

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - Frontend application logs
- **aws.cloudwatch.LogGroup** - Backend application logs
- **aws.cloudwatch.LogGroup** - Worker application logs
- **aws.cloudwatch.LogGroup** - Nginx access logs
- **aws.cloudwatch.Alarm** - High CPU utilization alarm
- **aws.cloudwatch.Alarm** - High memory utilization alarm
- **aws.cloudwatch.Alarm** - High error rate alarm
- **aws.cloudwatch.Alarm** - Low healthy host count alarm

## Deployment Pipeline
- **aws.codedeploy.Application** - ECS application deployment
- **aws.codedeploy.DeploymentGroup** - Frontend deployment group
- **aws.codedeploy.DeploymentGroup** - Backend deployment group
- **aws.codedeploy.DeploymentConfig** - Blue/green deployment config

## Secrets and Configuration
- **aws.ssm.Parameter** - Application configuration parameters
- **aws.ssm.Parameter** - Feature flags and toggles
- **aws.ssm.Parameter** - Environment-specific settings

## Health Checks and Monitoring
- **aws.route53.HealthCheck** - Application health monitoring
- **aws.route53.HealthCheck** - API endpoint health monitoring
- **aws.cloudwatch.Dashboard** - Application metrics dashboard

## IAM Resources
- **aws.iam.Role** - ECS task execution role
- **aws.iam.Role** - ECS task role (application permissions)
- **aws.iam.Policy** - ECR image pull policy
- **aws.iam.Policy** - Secrets Manager access policy
- **aws.iam.Policy** - S3 access policy for uploads
- **aws.iam.Policy** - CloudWatch logs policy

## Estimated Resource Count: 45-55 resources
## Estimated Monthly Cost:
- ALB: $16-25/month (2 ALBs)
- ECS Fargate: $30-100/month (depending on CPU/memory)
- CloudWatch logs: $5-15/month
- Route53 health checks: $1-3/month
- Data transfer: $5-20/month
- **Total: ~$60-160/month** (varies with traffic and scale)

## Resource Dependencies
- Depends on: Network stack (subnets, ALB), Security stack (security groups), DNS stack (certificates), Container images stack (ECR repositories)
- Required by: Monitoring stack, Frontend users