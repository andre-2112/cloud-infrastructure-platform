# Compute EC2 Stack Pulumi Generation Prompt

Create robust Pulumi TypeScript code for EC2-based compute infrastructure including instances, Auto Scaling Groups, Application Load Balancers, and supporting services for ${PROJECT_NAME}.

## Requirements

### Compute Infrastructure
- **Launch Templates**: Standardized instance configurations for web servers and background workers
- **Auto Scaling Groups**: Automatic scaling based on CPU/memory utilization with proper health checks
- **Application Load Balancer**: Internet-facing ALB with HTTPS termination and health check routing
- **Target Groups**: Separate target groups for web and API services with appropriate health checks
- **Key Pairs**: SSH key management for secure instance access

### Instance Configuration
- **Web Servers**: Frontend application servers with Node.js runtime and CloudWatch agent
- **Worker Servers**: Background processing instances for async tasks and job queues
- **Security Hardening**: Latest AMIs, encrypted EBS volumes, IAM instance profiles
- **User Data Scripts**: Automated software installation and configuration on boot
- **Monitoring**: CloudWatch agent configuration for system and application metrics

### High Availability and Scaling
- **Multi-AZ Deployment**: Instances distributed across multiple availability zones
- **Auto Scaling Policies**: Scale up/down based on CloudWatch metrics with proper cooldown periods
- **Load Balancer Integration**: Automatic registration/deregistration of instances
- **Health Checks**: ELB and EC2 health checks with appropriate grace periods

### Dependencies and Integration
- **Network Stack**: VPC ID, public/private subnets for proper placement
- **Security Stack**: Security groups for web servers, workers, and ALB
- **Storage Stack**: S3 bucket access for application assets and backups
- **DNS Stack**: SSL certificates for HTTPS termination on ALB
- **Centralized State**: Use shared state management for cross-stack communication

### Security and Access
- **IAM Roles**: Instance profiles with least-privilege access to required AWS services
- **Security Groups**: Proper ingress/egress rules for web traffic and internal communication
- **Encryption**: EBS volumes encrypted with KMS keys from security stack
- **SSH Access**: Controlled SSH access via key pairs and security group rules

### Environment Configuration
- **Development**: Smaller instance types (t3.small), minimal scaling, cost optimization
- **Production**: Larger instances (t3.medium/large), robust scaling, high availability
- **Stage**: Balanced configuration for testing and validation

### Key Outputs Required
```typescript
export const webAsgName = webServerAsg.name;
export const workerAsgName = workerServerAsg.name;
export const albDnsName = applicationLoadBalancer.dnsName;
export const albArn = applicationLoadBalancer.arn;
export const albZoneId = applicationLoadBalancer.zoneId;
export const webTargetGroupArn = webTargetGroup.arn;
export const webServerRoleArn = webServerRole.arn;
export const workerServerRoleArn = workerServerRole.arn;
export const keyPairName = mainKeyPair.keyName;
```

### Monitoring and Observability
- **CloudWatch Metrics**: CPU, memory, disk utilization with custom namespaces
- **CloudWatch Alarms**: Auto scaling triggers and health monitoring
- **CloudWatch Logs**: System logs and application logs centralization
- **Systems Manager**: Patch management and maintenance window configuration
- **Backup Integration**: EBS snapshot policies and backup tagging

### Load Balancer Configuration
- **HTTPS Listener**: Port 443 with SSL certificate from DNS stack
- **HTTP Redirect**: Port 80 traffic redirected to HTTPS
- **Health Checks**: Application-specific health check endpoints (/health)
- **Routing Rules**: Path-based routing to different target groups

### Variables to Use
- **${DEPLOYMENT_ID}**: Unique deployment identifier
- **${PROJECT_NAME}**: Project name for resource naming and tagging
- **${DEPLOY_DOMAIN}**: Domain for SSL certificate configuration
- **${AWS_REGION}**: Target AWS region for deployment
- **Environment-specific**: Use centralized state to determine dev/stage/prod configurations

### Integration Notes
- Configure proper CloudWatch agent with custom metrics collection
- Implement blue/green deployment capabilities through launch template versioning
- Set up proper log rotation and cleanup to manage disk space
- Configure Systems Manager for automated patching and maintenance
- Implement proper startup scripts for application deployment
- Ensure graceful shutdown handling for Auto Scaling Group terminations
- Configure proper EBS optimization for instance types used
- Set up appropriate placement groups for performance-critical workloads

This stack provides traditional compute infrastructure that can run alongside containerized workloads, offering flexibility for applications that require persistent storage, specific OS configurations, or legacy application support.