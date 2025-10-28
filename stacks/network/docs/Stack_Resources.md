# AWS Resources for Network Stack

## VPC Resources
- **aws.ec2.Vpc** - Main VPC for the infrastructure (10.0.0.0/16)
- **aws.ec2.InternetGateway** - Internet gateway for public access
- **aws.ec2.VpcGatewayAttachment** - Attach internet gateway to VPC
- **aws.ec2.DhcpOptions** - Custom DHCP options for the VPC
- **aws.ec2.VpcDhcpOptionsAssociation** - Associate DHCP options with VPC

## Subnet Resources
- **aws.ec2.Subnet** - Public subnet AZ-a (10.0.1.0/24)
- **aws.ec2.Subnet** - Public subnet AZ-b (10.0.2.0/24)
- **aws.ec2.Subnet** - Private subnet AZ-a (10.0.10.0/24)
- **aws.ec2.Subnet** - Private subnet AZ-b (10.0.11.0/24)
- **aws.ec2.Subnet** - Database subnet AZ-a (10.0.20.0/24)
- **aws.ec2.Subnet** - Database subnet AZ-b (10.0.21.0/24)

## NAT Gateway Resources
- **aws.ec2.Eip** - Elastic IP for NAT Gateway AZ-a
- **aws.ec2.Eip** - Elastic IP for NAT Gateway AZ-b (production)
- **aws.ec2.NatGateway** - NAT Gateway AZ-a for private subnet internet access
- **aws.ec2.NatGateway** - NAT Gateway AZ-b for high availability (production)

## Routing Resources
- **aws.ec2.RouteTable** - Public route table
- **aws.ec2.RouteTable** - Private route table AZ-a
- **aws.ec2.RouteTable** - Private route table AZ-b (production)
- **aws.ec2.RouteTable** - Database route table
- **aws.ec2.Route** - Public internet route (0.0.0.0/0 → IGW)
- **aws.ec2.Route** - Private NAT route AZ-a (0.0.0.0/0 → NAT-a)
- **aws.ec2.Route** - Private NAT route AZ-b (0.0.0.0/0 → NAT-b)
- **aws.ec2.RouteTableAssociation** - Public subnet AZ-a association
- **aws.ec2.RouteTableAssociation** - Public subnet AZ-b association
- **aws.ec2.RouteTableAssociation** - Private subnet AZ-a association
- **aws.ec2.RouteTableAssociation** - Private subnet AZ-b association
- **aws.ec2.RouteTableAssociation** - Database subnet AZ-a association
- **aws.ec2.RouteTableAssociation** - Database subnet AZ-b association

## Network ACL Resources
- **aws.ec2.NetworkAcl** - Custom network ACL for additional security
- **aws.ec2.NetworkAclRule** - Allow HTTP inbound (port 80)
- **aws.ec2.NetworkAclRule** - Allow HTTPS inbound (port 443)
- **aws.ec2.NetworkAclRule** - Allow SSH inbound (port 22)
- **aws.ec2.NetworkAclRule** - Allow all outbound traffic
- **aws.ec2.NetworkAclAssociation** - Associate ACL with public subnets
- **aws.ec2.NetworkAclAssociation** - Associate ACL with private subnets

## VPC Flow Logs
- **aws.ec2.FlowLog** - VPC flow logs for network monitoring
- **aws.cloudwatch.LogGroup** - Log group for VPC flow logs
- **aws.iam.Role** - Flow logs IAM role
- **aws.iam.RolePolicy** - Flow logs policy

## VPC Endpoints (Optional)
- **aws.ec2.VpcEndpoint** - S3 VPC endpoint (gateway type)
- **aws.ec2.VpcEndpoint** - DynamoDB VPC endpoint (gateway type)
- **aws.ec2.VpcEndpoint** - ECR API VPC endpoint (interface type)
- **aws.ec2.VpcEndpoint** - ECR DKR VPC endpoint (interface type)
- **aws.ec2.VpcEndpoint** - Secrets Manager VPC endpoint (interface type)
- **aws.ec2.VpcEndpoint** - Systems Manager VPC endpoint (interface type)

## Estimated Resource Count: 42-45 resources
## Estimated Monthly Cost:
- Development: $50-70 (1 NAT Gateway)
- Production: $90-120 (2 NAT Gateways for HA)
- VPC Endpoints: +$7-15 per endpoint

## Resource Dependencies
- Depends on: None (foundation stack)
- Required by: Security groups, RDS, ECS, EKS, Load Balancers