import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

/**
 * Network Stack v2.2 - VPC Infrastructure
 *
 * This stack provides foundational network infrastructure including VPC, subnets,
 * Internet Gateway, NAT Gateways, and route tables with multi-AZ support.
 *
 * Architecture Version: v2.2
 * - Pulumi Cloud centralized state management
 * - Deployment ID tagging for all resources
 * - Cross-stack reference patterns using StackReference
 * - Critical Fix: Public subnets properly configured for ECS Fargate with ALB
 */

// ============================================================================
// Configuration Interfaces
// ============================================================================

interface NetworkStackConfig {
  project: string;
  environment: string;
  deploymentId: string;
  pulumiOrg: string;
  region: string;
  vpcCidr?: string;
  enableFlowLogs?: boolean;
  enableVpcEndpoints?: boolean;
  highAvailabilityNat?: boolean;
}

// ============================================================================
// Configuration and Validation
// ============================================================================

const config = new pulumi.Config();

// Required configuration
const project = config.require("project");
const environment = config.require("environment");
const deploymentId = config.require("deploymentId");
const pulumiOrg = config.require("pulumiOrg");
const region = config.require("region");

// Optional configuration
const vpcCidr = config.get("vpcCidr") ?? "10.0.0.0/16";
const enableFlowLogs = config.getBoolean("enableFlowLogs") ?? true;
const enableVpcEndpoints = config.getBoolean("enableVpcEndpoints") ?? true;
const highAvailabilityNat = config.getBoolean("highAvailabilityNat") ?? (environment === "production");

// Validate configuration
const requiredConfigs = ["project", "environment", "deploymentId", "pulumiOrg"];
for (const configKey of requiredConfigs) {
  if (!config.get(configKey)) {
    throw new Error(`Required configuration missing: ${configKey}`);
  }
}

console.log(`🚀 Deploying Network Stack v2.2 for environment: ${environment}`);
console.log(`📋 Deployment ID: ${deploymentId}`);
console.log(`🌍 Region: ${region}`);
console.log(`🔧 VPC CIDR: ${vpcCidr}`);
console.log(`🔧 High Availability NAT: ${highAvailabilityNat}`);

// ============================================================================
// Resource Tagging and Naming
// ============================================================================

const defaultTags = {
  Environment: environment,
  DeploymentId: deploymentId,
  ManagedBy: "pulumi-cloud",
  Stack: "network",
  Project: project,
  Version: "v2.2"
};

function getResourceName(resourceType: string, suffix?: string): string {
  const parts = [project, environment, resourceType];
  if (suffix) parts.push(suffix);
  return parts.join("-");
}

// ============================================================================
// Availability Zones
// ============================================================================

// Fixed AZs for reliable deployment (v4.1 fix)
// Using first 2 AZs in us-east-1 for predictable deployment
const azs = [`${region}a`, `${region}b`];

// ============================================================================
// VPC Creation
// ============================================================================

const vpc = new aws.ec2.Vpc("main-vpc", {
  cidrBlock: vpcCidr,
  enableDnsHostnames: true,
  enableDnsSupport: true,
  tags: {
    ...defaultTags,
    Name: getResourceName("vpc"),
    ResourceType: "VPC",
    CidrBlock: vpcCidr
  }
});

// ============================================================================
// Internet Gateway
// ============================================================================

const internetGateway = new aws.ec2.InternetGateway("internet-gateway", {
  vpcId: vpc.id,
  tags: {
    ...defaultTags,
    Name: getResourceName("igw"),
    ResourceType: "InternetGateway"
  }
});

// ============================================================================
// Public Subnets (For ALBs, NAT Gateways, and ECS Fargate Containers)
// ============================================================================

// CRITICAL: Public subnets MUST be used for ECS Fargate containers with ALB
// This prevents 504 Gateway Timeout errors (from Critical Fixes.1.md)
const publicSubnets: aws.ec2.Subnet[] = [];

azs.forEach((az, index) => {
  const cidrBlock = `10.0.${index + 1}.0/24`;
  const subnet = new aws.ec2.Subnet(`public-subnet-${index}`, {
    vpcId: vpc.id,
    cidrBlock: cidrBlock,
    availabilityZone: az,
    mapPublicIpOnLaunch: true, // CRITICAL: Enable auto-assign public IP
    tags: {
      ...defaultTags,
      Name: getResourceName("public-subnet", az.slice(-2)),
      Type: "Public",
      Tier: "dmz",
      AvailabilityZone: az,
      CidrBlock: cidrBlock,
      // CRITICAL TAG: Mark as suitable for ECS Fargate
      "kubernetes.io/role/elb": "1",
      Purpose: "ALB and ECS Fargate containers"
    }
  });
  publicSubnets.push(subnet);
});

// ============================================================================
// Private Subnets (For internal resources)
// ============================================================================

const privateSubnets: aws.ec2.Subnet[] = [];

azs.forEach((az, index) => {
  const cidrBlock = `10.0.${index + 10}.0/24`;
  const subnet = new aws.ec2.Subnet(`private-subnet-${index}`, {
    vpcId: vpc.id,
    cidrBlock: cidrBlock,
    availabilityZone: az,
    mapPublicIpOnLaunch: false,
    tags: {
      ...defaultTags,
      Name: getResourceName("private-subnet", az.slice(-2)),
      Type: "Private",
      Tier: "application",
      AvailabilityZone: az,
      CidrBlock: cidrBlock,
      Purpose: "Internal resources and services"
    }
  });
  privateSubnets.push(subnet);
});

// ============================================================================
// Database Subnets (For RDS, ElastiCache)
// ============================================================================

const databaseSubnets: aws.ec2.Subnet[] = [];

azs.forEach((az, index) => {
  const cidrBlock = `10.0.${index + 20}.0/24`;
  const subnet = new aws.ec2.Subnet(`database-subnet-${index}`, {
    vpcId: vpc.id,
    cidrBlock: cidrBlock,
    availabilityZone: az,
    mapPublicIpOnLaunch: false,
    tags: {
      ...defaultTags,
      Name: getResourceName("database-subnet", az.slice(-2)),
      Type: "Database",
      Tier: "data",
      AvailabilityZone: az,
      CidrBlock: cidrBlock,
      Purpose: "RDS and ElastiCache"
    }
  });
  databaseSubnets.push(subnet);
});

// ============================================================================
// NAT Gateways for Private Subnet Internet Access
// ============================================================================

const natEips: aws.ec2.Eip[] = [];
const natGateways: aws.ec2.NatGateway[] = [];

const natCount = highAvailabilityNat ? 2 : 1;

for (let i = 0; i < natCount; i++) {
  const eip = new aws.ec2.Eip(`nat-eip-${i}`, {
    domain: "vpc",
    tags: {
      ...defaultTags,
      Name: getResourceName("nat-eip", `${i}`),
      ResourceType: "ElasticIP",
      Purpose: "NAT Gateway"
    }
  }, { dependsOn: [internetGateway] });
  natEips.push(eip);

  const natGateway = new aws.ec2.NatGateway(`nat-gateway-${i}`, {
    allocationId: eip.id,
    subnetId: publicSubnets[i].id,
    tags: {
      ...defaultTags,
      Name: getResourceName("nat", `${i}`),
      ResourceType: "NatGateway",
      AvailabilityZone: publicSubnets[i].availabilityZone
    }
  }, { dependsOn: [internetGateway] });
  natGateways.push(natGateway);
}

console.log(`✅ Creating ${natCount} NAT Gateway(s) for ${highAvailabilityNat ? 'high availability' : 'cost optimization'}`);

// ============================================================================
// Route Tables - Public
// ============================================================================

const publicRouteTable = new aws.ec2.RouteTable("public-route-table", {
  vpcId: vpc.id,
  tags: {
    ...defaultTags,
    Name: getResourceName("public-rt"),
    Type: "Public",
    ResourceType: "RouteTable"
  }
});

// Route to Internet Gateway
const publicRoute = new aws.ec2.Route("public-route-igw", {
  routeTableId: publicRouteTable.id,
  destinationCidrBlock: "0.0.0.0/0",
  gatewayId: internetGateway.id
});

// Associate public subnets with public route table
publicSubnets.forEach((subnet, index) => {
  new aws.ec2.RouteTableAssociation(`public-rta-${index}`, {
    subnetId: subnet.id,
    routeTableId: publicRouteTable.id
  });
});

// ============================================================================
// Route Tables - Private
// ============================================================================

const privateRouteTables: aws.ec2.RouteTable[] = [];

privateSubnets.forEach((subnet, index) => {
  const natGatewayIndex = highAvailabilityNat ? index : 0;

  const routeTable = new aws.ec2.RouteTable(`private-route-table-${index}`, {
    vpcId: vpc.id,
    tags: {
      ...defaultTags,
      Name: getResourceName("private-rt", `${index}`),
      Type: "Private",
      ResourceType: "RouteTable",
      AvailabilityZone: subnet.availabilityZone
    }
  });
  privateRouteTables.push(routeTable);

  // Route to NAT Gateway
  new aws.ec2.Route(`private-route-nat-${index}`, {
    routeTableId: routeTable.id,
    destinationCidrBlock: "0.0.0.0/0",
    natGatewayId: natGateways[natGatewayIndex].id
  });

  // Associate private subnet with route table
  new aws.ec2.RouteTableAssociation(`private-rta-${index}`, {
    subnetId: subnet.id,
    routeTableId: routeTable.id
  });
});

// ============================================================================
// Route Tables - Database (Isolated)
// ============================================================================

const databaseRouteTables: aws.ec2.RouteTable[] = [];

databaseSubnets.forEach((subnet, index) => {
  const routeTable = new aws.ec2.RouteTable(`database-route-table-${index}`, {
    vpcId: vpc.id,
    tags: {
      ...defaultTags,
      Name: getResourceName("database-rt", `${index}`),
      Type: "Database",
      ResourceType: "RouteTable",
      AvailabilityZone: subnet.availabilityZone,
      Purpose: "Isolated database tier"
    }
  });
  databaseRouteTables.push(routeTable);

  // Associate database subnet with route table
  new aws.ec2.RouteTableAssociation(`database-rta-${index}`, {
    subnetId: subnet.id,
    routeTableId: routeTable.id
  });
});

// ============================================================================
// VPC Flow Logs (Optional)
// ============================================================================

let flowLogsLogGroup: aws.cloudwatch.LogGroup | undefined;
let flowLogsRole: aws.iam.Role | undefined;

if (enableFlowLogs) {
  flowLogsLogGroup = new aws.cloudwatch.LogGroup("vpc-flow-logs", {
    name: `/aws/vpc/flowlogs/${deploymentId}`,
    retentionInDays: 14,
    tags: {
      ...defaultTags,
      Name: getResourceName("vpc-flow-logs"),
      ResourceType: "LogGroup"
    }
  });

  flowLogsRole = new aws.iam.Role("vpc-flow-logs-role", {
    assumeRolePolicy: JSON.stringify({
      Version: "2012-10-17",
      Statement: [{
        Action: "sts:AssumeRole",
        Effect: "Allow",
        Principal: {
          Service: "vpc-flow-logs.amazonaws.com"
        }
      }]
    }),
    tags: {
      ...defaultTags,
      Name: getResourceName("vpc-flow-logs-role"),
      ResourceType: "IAMRole"
    }
  });

  new aws.iam.RolePolicy("vpc-flow-logs-policy", {
    role: flowLogsRole.id,
    policy: JSON.stringify({
      Version: "2012-10-17",
      Statement: [{
        Effect: "Allow",
        Action: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ],
        Resource: "*"
      }]
    })
  });

  new aws.ec2.FlowLog("vpc-flow-logs", {
    iamRoleArn: flowLogsRole.arn,
    logDestination: flowLogsLogGroup.arn,
    trafficType: "ALL",
    vpcId: vpc.id,
    tags: {
      ...defaultTags,
      Name: getResourceName("vpc-flow-logs"),
      ResourceType: "FlowLog"
    }
  });

  console.log("✅ VPC Flow Logs enabled");
}

// ============================================================================
// VPC Endpoints (Optional - for cost optimization)
// ============================================================================

let s3VpcEndpoint: aws.ec2.VpcEndpoint | undefined;
let ecrApiEndpoint: aws.ec2.VpcEndpoint | undefined;
let ecrDkrEndpoint: aws.ec2.VpcEndpoint | undefined;

if (enableVpcEndpoints) {
  // S3 Gateway Endpoint (no cost)
  s3VpcEndpoint = new aws.ec2.VpcEndpoint("s3-vpc-endpoint", {
    vpcId: vpc.id,
    serviceName: `com.amazonaws.${region}.s3`,
    vpcEndpointType: "Gateway",
    routeTableIds: [...privateRouteTables.map(rt => rt.id), ...databaseRouteTables.map(rt => rt.id)],
    tags: {
      ...defaultTags,
      Name: getResourceName("s3-endpoint"),
      Service: "S3",
      ResourceType: "VPCEndpoint"
    }
  });

  // ECR API Endpoint (interface endpoint - has cost)
  ecrApiEndpoint = new aws.ec2.VpcEndpoint("ecr-api-vpc-endpoint", {
    vpcId: vpc.id,
    serviceName: `com.amazonaws.${region}.ecr.api`,
    vpcEndpointType: "Interface",
    subnetIds: privateSubnets.map(s => s.id),
    privateDnsEnabled: true,
    securityGroupIds: [vpc.defaultSecurityGroupId],
    tags: {
      ...defaultTags,
      Name: getResourceName("ecr-api-endpoint"),
      Service: "ECR-API",
      ResourceType: "VPCEndpoint"
    }
  });

  // ECR Docker Endpoint (interface endpoint - has cost)
  ecrDkrEndpoint = new aws.ec2.VpcEndpoint("ecr-dkr-vpc-endpoint", {
    vpcId: vpc.id,
    serviceName: `com.amazonaws.${region}.ecr.dkr`,
    vpcEndpointType: "Interface",
    subnetIds: privateSubnets.map(s => s.id),
    privateDnsEnabled: true,
    securityGroupIds: [vpc.defaultSecurityGroupId],
    tags: {
      ...defaultTags,
      Name: getResourceName("ecr-dkr-endpoint"),
      Service: "ECR-Docker",
      ResourceType: "VPCEndpoint"
    }
  });

  console.log("✅ VPC Endpoints enabled for S3 and ECR");
}

// ============================================================================
// Stack Outputs for Cross-Stack References
// ============================================================================

// VPC Information
export const vpcId = vpc.id;
export const vpcArn = vpc.arn;
export const vpcCidrBlock = vpc.cidrBlock;

// Subnet IDs (CRITICAL for cross-stack references)
export const publicSubnetIds = pulumi.output(publicSubnets.map(s => s.id));
export const privateSubnetIds = pulumi.output(privateSubnets.map(s => s.id));
export const databaseSubnetIds = pulumi.output(databaseSubnets.map(s => s.id));

// Availability Zones
export const availabilityZones = pulumi.output(azs);

// Gateway Information
export const internetGatewayId = internetGateway.id;
export const natGatewayIds = pulumi.output(natGateways.map(ng => ng.id));
export const natGatewayIps = pulumi.output(natEips.map(eip => eip.publicIp));

// Route Table Information
export const publicRouteTableId = publicRouteTable.id;
export const privateRouteTableIds = pulumi.output(privateRouteTables.map(rt => rt.id));
export const databaseRouteTableIds = pulumi.output(databaseRouteTables.map(rt => rt.id));

// Flow Logs Information
export const flowLogsLogGroupName = flowLogsLogGroup ? flowLogsLogGroup.name : undefined;

// VPC Endpoints Information
export const s3VpcEndpointId = s3VpcEndpoint ? s3VpcEndpoint.id : undefined;
export const ecrApiVpcEndpointId = ecrApiEndpoint ? ecrApiEndpoint.id : undefined;
export const ecrDkrVpcEndpointId = ecrDkrEndpoint ? ecrDkrEndpoint.id : undefined;

// Stack Metadata
export const stackName = "network";
export const stackEnvironment = environment;
export const stackDeploymentId = deploymentId;
export const stackVersion = "v2.2";

// Existence marker for stack verification
export const __exists = true;

// Summary object for comprehensive output
export const summary = pulumi.output({
  vpc: {
    id: vpcId,
    cidrBlock: vpcCidrBlock,
    region: region
  },
  subnets: {
    public: {
      count: publicSubnets.length,
      ids: publicSubnets.map(s => s.id),
      cidrs: publicSubnets.map(s => s.cidrBlock),
      purpose: "ALB and ECS Fargate containers (CRITICAL FIX APPLIED)"
    },
    private: {
      count: privateSubnets.length,
      ids: privateSubnets.map(s => s.id),
      cidrs: privateSubnets.map(s => s.cidrBlock)
    },
    database: {
      count: databaseSubnets.length,
      ids: databaseSubnets.map(s => s.id),
      cidrs: databaseSubnets.map(s => s.cidrBlock)
    }
  },
  networking: {
    natGatewayCount: natGateways.length,
    highAvailability: highAvailabilityNat,
    flowLogsEnabled: enableFlowLogs,
    vpcEndpointsEnabled: enableVpcEndpoints
  },
  deployment: {
    project: project,
    environment: environment,
    deploymentId: deploymentId,
    version: "v2.2"
  }
});

// ============================================================================
// Post-Deployment Instructions
// ============================================================================

pulumi.log.info("=".repeat(80));
pulumi.log.info("Network Stack v2.2 Deployment Complete");
pulumi.log.info("=".repeat(80));
pulumi.log.info("");
pulumi.log.info("✅ CRITICAL FIX APPLIED: Public subnets configured for ECS Fargate with ALB");
pulumi.log.info("   This prevents 504 Gateway Timeout errors with load balancers");
pulumi.log.info("");
pulumi.log.info("📋 Network Architecture:");
pulumi.log.info(`   VPC CIDR: ${vpcCidr}`);
pulumi.log.info(`   Public Subnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)`);
pulumi.log.info(`   Private Subnets: 10.0.10.0/24, 10.0.11.0/24 (2 AZs)`);
pulumi.log.info(`   Database Subnets: 10.0.20.0/24, 10.0.21.0/24 (2 AZs)`);
pulumi.log.info(`   NAT Gateways: ${natCount} (${highAvailabilityNat ? 'HA mode' : 'Cost-optimized'})`);
pulumi.log.info("");
pulumi.log.info("🔗 Other stacks can reference this stack using:");
pulumi.log.info(`   const networkStack = // v4.1 format: ${pulumiOrg}/network/${deploymentId}-network-${environment}
    new pulumi.StackReference("${pulumiOrg}/network/${deploymentId}-network-${environment}");`);
pulumi.log.info(`   const vpcId = networkStack.getOutput("vpcId");`);
pulumi.log.info(`   const publicSubnetIds = networkStack.getOutput("publicSubnetIds");`);
pulumi.log.info("");
pulumi.log.info("=".repeat(80));
