# AWS Resources for EKS Services Stack

## EKS Cluster Resources
- **aws.eks.Cluster** - Kubernetes control plane cluster
- **aws.eks.ClusterAuth** - Cluster authentication configuration
- **aws.eks.ClusterEncryption** - Envelope encryption configuration
- **aws.eks.ClusterLogging** - Control plane logging configuration

## EKS Node Groups
- **aws.eks.NodeGroup** - Primary node group (general workloads)
- **aws.eks.NodeGroup** - Spot instance node group (cost optimization)
- **aws.eks.NodeGroup** - GPU node group (if needed for ML workloads)
- **aws.launch.Template** - Node group launch template
- **aws.launch.Template** - Spot instance launch template

## EKS Add-ons
- **aws.eks.Addon** - VPC CNI addon
- **aws.eks.Addon** - CoreDNS addon
- **aws.eks.Addon** - kube-proxy addon
- **aws.eks.Addon** - EBS CSI driver addon
- **aws.eks.Addon** - EFS CSI driver addon (optional)

## IAM Resources for EKS
- **aws.iam.Role** - EKS cluster service role
- **aws.iam.Role** - EKS node group role
- **aws.iam.Role** - EKS Fargate profile role
- **aws.iam.Role** - AWS Load Balancer Controller role
- **aws.iam.Role** - EBS CSI controller role
- **aws.iam.Policy** - Custom EKS permissions policy
- **aws.iam.RolePolicyAttachment** - EKS cluster policy attachments
- **aws.iam.RolePolicyAttachment** - Node group policy attachments
- **aws.iam.OpenIdConnectProvider** - OIDC provider for service accounts

## EKS Security
- **aws.ec2.SecurityGroup** - EKS cluster security group
- **aws.ec2.SecurityGroup** - Node group security group
- **aws.ec2.SecurityGroup** - Control plane security group
- **aws.ec2.SecurityGroupRule** - Custom ingress/egress rules

## EKS Fargate (Optional)
- **aws.eks.FargateProfile** - Fargate profile for serverless pods
- **aws.iam.Role** - Fargate pod execution role

## Kubernetes Service Accounts
- **kubernetes.ServiceAccount** - AWS Load Balancer Controller service account
- **kubernetes.ServiceAccount** - EBS CSI driver service account
- **kubernetes.ServiceAccount** - Cluster autoscaler service account
- **kubernetes.ServiceAccount** - External DNS service account

## Auto Scaling Resources
- **aws.autoscaling.Group** - Node group auto scaling group
- **aws.autoscaling.Policy** - Scale-up policy
- **aws.autoscaling.Policy** - Scale-down policy
- **kubernetes.Deployment** - Cluster autoscaler deployment

## Load Balancer Resources
- **kubernetes.Service** - LoadBalancer type services
- **kubernetes.Ingress** - Application ingress resources
- **aws.lb.LoadBalancer** - Network Load Balancer (created by service)
- **aws.lb.LoadBalancer** - Application Load Balancer (created by ingress)

## Storage Resources
- **kubernetes.StorageClass** - EBS storage class
- **kubernetes.StorageClass** - EFS storage class
- **kubernetes.PersistentVolume** - Application persistent volumes
- **kubernetes.PersistentVolumeClaim** - Application volume claims

## Monitoring and Logging
- **aws.cloudwatch.LogGroup** - EKS control plane logs
- **aws.cloudwatch.LogGroup** - Application pod logs (Fluent Bit)
- **kubernetes.DaemonSet** - CloudWatch agent DaemonSet
- **kubernetes.ConfigMap** - Fluent Bit configuration
- **kubernetes.ServiceAccount** - CloudWatch agent service account

## Networking and DNS
- **kubernetes.ConfigMap** - CoreDNS configuration
- **kubernetes.Deployment** - External DNS deployment
- **aws.route53.Record** - DNS records created by External DNS

## Application Deployments
- **kubernetes.Deployment** - Application deployments
- **kubernetes.Service** - Application services
- **kubernetes.ConfigMap** - Application configuration
- **kubernetes.Secret** - Application secrets (linked to AWS Secrets Manager)

## Estimated Resource Count: 45-60 resources
## Estimated Monthly Cost:
- EKS control plane: $72/month (24/7)
- EC2 node groups: $50-300/month (depends on instance types and count)
- EBS storage: $0.10 per GB/month
- Load balancers: $16-25/month per ALB/NLB
- Data transfer: Variable based on traffic
- **Total: ~$150-400/month** (highly variable based on workload)

## Resource Dependencies
- Depends on: Network stack (VPC, subnets), Security stack (IAM roles, security groups), ECR stack (container images)
- Required by: Kubernetes applications, Service mesh, Advanced monitoring