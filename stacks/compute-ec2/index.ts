import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    DNSOutputs,
    isDevelopment,
    isProduction,
    ENVIRONMENT_DEFAULTS,
    COMMON_PORTS
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Get network stack outputs
const networkStackOutputs: NetworkOutputs = {
    vpcId: centralState.getStackOutput<string>("network", "vpcId"),
    vpcCidrBlock: centralState.getStackOutput<string>("network", "vpcCidrBlock"),
    internetGatewayId: centralState.getStackOutput<string>("network", "internetGatewayId"),
    publicSubnetIds: centralState.getStackOutput<string[]>("network", "publicSubnetIds"),
    privateSubnetIds: centralState.getStackOutput<string[]>("network", "privateSubnetIds"),
    databaseSubnetIds: centralState.getStackOutput<string[]>("network", "databaseSubnetIds"),
    availabilityZones: centralState.getStackOutput<string[]>("network", "availabilityZones"),
    natGatewayIds: centralState.getStackOutput<string[]>("network", "natGatewayIds")
};

// Get security stack outputs
const securityStackOutputs: SecurityOutputs = {
    loadBalancerSgId: centralState.getStackOutput<string>("security", "loadBalancerSgId"),
    webApplicationSgId: centralState.getStackOutput<string>("security", "webApplicationSgId"),
    apiApplicationSgId: centralState.getStackOutput<string>("security", "apiApplicationSgId"),
    databaseSgId: centralState.getStackOutput<string>("security", "databaseSgId"),
    ecsExecutionRoleArn: centralState.getStackOutput<string>("security", "ecsExecutionRoleArn"),
    ecsTaskRoleArn: centralState.getStackOutput<string>("security", "ecsTaskRoleArn"),
    eksClusterRoleArn: centralState.getStackOutput<string>("security", "eksClusterRoleArn"),
    eksNodeGroupRoleArn: centralState.getStackOutput<string>("security", "eksNodeGroupRoleArn"),
    applicationKeyId: centralState.getStackOutput<string>("security", "applicationKeyId"),
    applicationKeyArn: centralState.getStackOutput<string>("security", "applicationKeyArn"),
    databaseKeyId: centralState.getStackOutput<string>("security", "databaseKeyId"),
    databaseKeyArn: centralState.getStackOutput<string>("security", "databaseKeyArn")
};

// Get DNS stack outputs
const dnsStackOutputs: DNSOutputs = {
    hostedZoneId: centralState.getStackOutput<string>("dns", "hostedZoneId"),
    domainName: centralState.getStackOutput<string>("dns", "domainName"),
    primaryCertificateArn: centralState.getStackOutput<string>("dns", "primaryCertificateArn"),
    wildcardCertificateArn: centralState.getStackOutput<string>("dns", "wildcardCertificateArn"),
    primaryHealthCheckId: centralState.getStackOutput<string>("dns", "primaryHealthCheckId")
};

// Get storage stack outputs (optional dependency)
const storageStackExists = centralState.stackExists("storage");
const storageStackOutputs = storageStackExists ? {
    primaryBucketArn: centralState.getStackOutput<string>("storage", "primaryBucketArn"),
    staticAssetsBucketArn: centralState.getStackOutput<string>("storage", "staticAssetsBucketArn"),
    logsBucketArn: centralState.getStackOutput<string>("storage", "logsBucketArn"),
    backupBucketArn: centralState.getStackOutput<string>("storage", "backupBucketArn")
} : null;

const STACK_NAME = "compute-ec2";

// Environment-specific configuration
const envConfig = ENVIRONMENT_DEFAULTS[deploymentConfig.environment];
const isDevEnvironment = isDevelopment(deploymentConfig);
const isProdEnvironment = isProduction(deploymentConfig);

// EC2 Compute Stack - Traditional compute infrastructure with Auto Scaling Groups and Load Balancers
console.log(`🚀 Deploying EC2 Compute Stack for environment: ${deploymentConfig.environment}`);

// =============================================================================
// AMI Data Sources
// =============================================================================

// Get latest Amazon Linux 2 AMI
const amazonLinux2Ami = aws.ec2.getAmi({
    mostRecent: true,
    owners: ["amazon"],
    filters: [
        {
            name: "name",
            values: ["amzn2-ami-hvm-*-x86_64-gp2"]
        },
        {
            name: "virtualization-type",
            values: ["hvm"]
        }
    ]
});

// =============================================================================
// Key Pairs for SSH Access
// =============================================================================

const mainKeyPair = new aws.ec2.KeyPair("main-key-pair", {
    keyName: createResourceName(deploymentConfig, "main-key"),
    tags: createResourceTags(deploymentConfig, "key-pair", {
        Name: createResourceName(deploymentConfig, "main-key"),
        Purpose: "SSH access to EC2 instances"
    })
});

// =============================================================================
// IAM Roles and Instance Profiles
// =============================================================================

// Web Server IAM Role
const webServerRole = new aws.iam.Role("web-server-role", {
    name: createResourceName(deploymentConfig, "web-server-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "ec2.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "web-server-role"),
        Service: "EC2-WebServer"
    })
});

// Web Server Role Policies
const webServerCloudWatchPolicy = new aws.iam.RolePolicy("web-server-cloudwatch-policy", {
    role: webServerRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "cloudwatch:PutMetricData",
                    "ec2:DescribeTags",
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:DescribeLogGroups"
                ],
                Resource: "*"
            }
        ]
    })
});

const webServerS3Policy = storageStackOutputs ? new aws.iam.RolePolicy("web-server-s3-policy", {
    role: webServerRole.id,
    policy: pulumi.all([
        storageStackOutputs.staticAssetsBucketArn,
        storageStackOutputs.logsBucketArn,
        storageStackOutputs.primaryBucketArn
    ]).apply(([staticArn, logsArn, primaryArn]) => JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                Resource: [
                    `${staticArn}/*`,
                    `${logsArn}/*`,
                    `${primaryArn}/uploads/*`
                ]
            },
            {
                Effect: "Allow",
                Action: [
                    "s3:ListBucket"
                ],
                Resource: [staticArn, logsArn, primaryArn]
            }
        ]
    }))
}) : undefined;

const webServerSystemsManagerPolicy = new aws.iam.RolePolicyAttachment("web-server-ssm-policy", {
    role: webServerRole.name,
    policyArn: "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
});

const webServerInstanceProfile = new aws.iam.InstanceProfile("web-server-instance-profile", {
    name: createResourceName(deploymentConfig, "web-server-profile"),
    role: webServerRole.name,
    tags: createResourceTags(deploymentConfig, "instance-profile", {
        Name: createResourceName(deploymentConfig, "web-server-profile")
    })
});

// Worker Server IAM Role
const workerServerRole = new aws.iam.Role("worker-server-role", {
    name: createResourceName(deploymentConfig, "worker-server-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "ec2.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "worker-server-role"),
        Service: "EC2-WorkerServer"
    })
});

// Worker Server Role Policies
const workerServerCloudWatchPolicy = new aws.iam.RolePolicy("worker-server-cloudwatch-policy", {
    role: workerServerRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "cloudwatch:PutMetricData",
                    "ec2:DescribeTags",
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:DescribeLogGroups"
                ],
                Resource: "*"
            }
        ]
    })
});

const workerServerS3Policy = storageStackOutputs ? new aws.iam.RolePolicy("worker-server-s3-policy", {
    role: workerServerRole.id,
    policy: pulumi.all([
        storageStackOutputs.primaryBucketArn,
        storageStackOutputs.logsBucketArn,
        storageStackOutputs.backupBucketArn
    ]).apply(([primaryArn, logsArn, backupArn]) => JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                Resource: [
                    `${primaryArn}/*`,
                    `${logsArn}/*`,
                    `${backupArn}/*`
                ]
            },
            {
                Effect: "Allow",
                Action: [
                    "s3:ListBucket"
                ],
                Resource: [primaryArn, logsArn, backupArn]
            }
        ]
    }))
}) : undefined;

const workerServerSystemsManagerPolicy = new aws.iam.RolePolicyAttachment("worker-server-ssm-policy", {
    role: workerServerRole.name,
    policyArn: "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
});

const workerServerInstanceProfile = new aws.iam.InstanceProfile("worker-server-instance-profile", {
    name: createResourceName(deploymentConfig, "worker-server-profile"),
    role: workerServerRole.name,
    tags: createResourceTags(deploymentConfig, "instance-profile", {
        Name: createResourceName(deploymentConfig, "worker-server-profile")
    })
});

// =============================================================================
// Security Groups for EC2 Instances
// =============================================================================

// Additional security group for EC2 instances (more specific than the shared ones)
const webServerSg = new aws.ec2.SecurityGroup("web-server-sg", {
    name: createResourceName(deploymentConfig, "web-server-sg"),
    description: "Security group for web server EC2 instances",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "SSH from VPC",
            fromPort: COMMON_PORTS.SSH,
            toPort: COMMON_PORTS.SSH,
            protocol: "tcp",
            cidrBlocks: [networkStackOutputs.vpcCidrBlock]
        },
        {
            description: "HTTP from ALB",
            fromPort: COMMON_PORTS.HTTP,
            toPort: COMMON_PORTS.HTTP,
            protocol: "tcp",
            securityGroups: [securityStackOutputs.loadBalancerSgId]
        },
        {
            description: "HTTPS from ALB",
            fromPort: COMMON_PORTS.HTTPS,
            toPort: COMMON_PORTS.HTTPS,
            protocol: "tcp",
            securityGroups: [securityStackOutputs.loadBalancerSgId]
        },
        {
            description: "Application port from ALB",
            fromPort: COMMON_PORTS.APPLICATION,
            toPort: COMMON_PORTS.APPLICATION,
            protocol: "tcp",
            securityGroups: [securityStackOutputs.loadBalancerSgId]
        },
        {
            description: "Node.js port from ALB",
            fromPort: COMMON_PORTS.NODEJS,
            toPort: COMMON_PORTS.NODEJS,
            protocol: "tcp",
            securityGroups: [securityStackOutputs.loadBalancerSgId]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: ["0.0.0.0/0"]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "web-server-sg"),
        Tier: "web-server"
    })
});

const workerServerSg = new aws.ec2.SecurityGroup("worker-server-sg", {
    name: createResourceName(deploymentConfig, "worker-server-sg"),
    description: "Security group for worker server EC2 instances",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "SSH from VPC",
            fromPort: COMMON_PORTS.SSH,
            toPort: COMMON_PORTS.SSH,
            protocol: "tcp",
            cidrBlocks: [networkStackOutputs.vpcCidrBlock]
        },
        {
            description: "Internal communication from web servers",
            fromPort: 8000,
            toPort: 8999,
            protocol: "tcp",
            securityGroups: [webServerSg.id]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: ["0.0.0.0/0"]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "worker-server-sg"),
        Tier: "worker-server"
    })
});

// =============================================================================
// User Data Scripts
// =============================================================================

const webServerUserData = pulumi.interpolate`#!/bin/bash
yum update -y
yum install -y wget curl git

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Create application directory
mkdir -p /opt/webapp
chown ec2-user:ec2-user /opt/webapp

# Install pm2 globally for process management
npm install -g pm2

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root"
    },
    "metrics": {
        "namespace": "${deploymentConfig.projectName}-${deploymentConfig.deploymentId}-ec2",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/aws/ec2/web-server/${deploymentConfig.deploymentId}",
                        "log_stream_name": "{instance_id}-messages"
                    },
                    {
                        "file_path": "/opt/webapp/logs/*.log",
                        "log_group_name": "/aws/ec2/web-server/${deploymentConfig.deploymentId}",
                        "log_stream_name": "{instance_id}-application"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Create a simple health check endpoint
mkdir -p /opt/webapp/public
cat > /opt/webapp/app.js << 'EOF'
const express = require('express');
const app = express();
const port = ${COMMON_PORTS.NODEJS};

app.use(express.static('public'));

app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        environment: '${deploymentConfig.environment}',
        instance: process.env.HOSTNAME
    });
});

app.get('/', (req, res) => {
    res.json({
        message: 'Web Server Running',
        environment: '${deploymentConfig.environment}',
        deployment: '${deploymentConfig.deploymentId}'
    });
});

app.listen(port, '0.0.0.0', () => {
    console.log('Web server listening on port ' + port);
});
EOF

cd /opt/webapp
npm init -y
npm install express
pm2 start app.js --name "webapp"
pm2 startup
pm2 save

# Configure automatic startup
systemctl enable amazon-cloudwatch-agent
`;

const workerServerUserData = pulumi.interpolate`#!/bin/bash
yum update -y
yum install -y wget curl git python3 python3-pip

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Create application directory
mkdir -p /opt/worker
chown ec2-user:ec2-user /opt/worker

# Install pm2 globally for process management
npm install -g pm2

# Configure CloudWatch agent for worker processes
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root"
    },
    "metrics": {
        "namespace": "${deploymentConfig.projectName}-${deploymentConfig.deploymentId}-worker",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/aws/ec2/worker-server/${deploymentConfig.deploymentId}",
                        "log_stream_name": "{instance_id}-messages"
                    },
                    {
                        "file_path": "/opt/worker/logs/*.log",
                        "log_group_name": "/aws/ec2/worker-server/${deploymentConfig.deploymentId}",
                        "log_stream_name": "{instance_id}-worker"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Create a simple worker application
cat > /opt/worker/worker.js << 'EOF'
const fs = require('fs');
const path = require('path');

// Ensure logs directory exists
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
}

console.log('Worker server starting...');
console.log('Environment:', '${deploymentConfig.environment}');
console.log('Deployment ID:', '${deploymentConfig.deploymentId}');

// Simple job processing simulation
setInterval(() => {
    const timestamp = new Date().toISOString();
    const logMessage = \`[\${timestamp}] Worker processed job - Environment: ${deploymentConfig.environment}\`;
    console.log(logMessage);

    // Write to log file
    fs.appendFileSync(path.join(logsDir, 'worker.log'), logMessage + '\n');
}, 30000);

// Health check endpoint (simple HTTP server)
const express = require('express');
const app = express();
const port = 8080;

app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        environment: '${deploymentConfig.environment}',
        type: 'worker',
        instance: process.env.HOSTNAME
    });
});

app.listen(port, '0.0.0.0', () => {
    console.log('Worker health check listening on port ' + port);
});
EOF

cd /opt/worker
npm init -y
npm install express
pm2 start worker.js --name "worker"
pm2 startup
pm2 save

# Configure automatic startup
systemctl enable amazon-cloudwatch-agent
`;

// =============================================================================
// Launch Templates
// =============================================================================

// Web Server Launch Template
const webServerLaunchTemplate = new aws.ec2.LaunchTemplate("web-server-launch-template", {
    name: createResourceName(deploymentConfig, "web-server-lt"),
    description: "Launch template for web server instances",
    imageId: amazonLinux2Ami.then(ami => ami.id),
    instanceType: isDevEnvironment ? "t3.small" : isProdEnvironment ? "t3.medium" : "t3.small",
    keyName: mainKeyPair.keyName,

    iamInstanceProfile: {
        name: webServerInstanceProfile.name
    },

    blockDeviceMappings: [
        {
            deviceName: "/dev/xvda",
            ebs: {
                volumeSize: isDevEnvironment ? 20 : 30,
                volumeType: "gp3",
                encrypted: true,
                kmsKeyId: securityStackOutputs.applicationKeyArn,
                deleteOnTermination: true
            }
        }
    ],

    vpcSecurityGroupIds: [webServerSg.id, securityStackOutputs.webApplicationSgId],

    userData: webServerUserData.apply(ud => Buffer.from(ud).toString('base64')),

    instanceInitiatedShutdownBehavior: "terminate",

    monitoring: {
        enabled: true
    },

    tagSpecifications: [
        {
            resourceType: "instance",
            tags: createResourceTags(deploymentConfig, "ec2-instance", {
                Name: createResourceName(deploymentConfig, "web-server"),
                Type: "WebServer",
                Backup: "Required"
            })
        },
        {
            resourceType: "volume",
            tags: createResourceTags(deploymentConfig, "ebs-volume", {
                Name: createResourceName(deploymentConfig, "web-server-volume"),
                Type: "WebServer",
                Backup: "Required"
            })
        }
    ],

    tags: createResourceTags(deploymentConfig, "launch-template", {
        Name: createResourceName(deploymentConfig, "web-server-lt"),
        Purpose: "Web Server Launch Template"
    })
});

// Worker Server Launch Template
const workerServerLaunchTemplate = new aws.ec2.LaunchTemplate("worker-server-launch-template", {
    name: createResourceName(deploymentConfig, "worker-server-lt"),
    description: "Launch template for worker server instances",
    imageId: amazonLinux2Ami.then(ami => ami.id),
    instanceType: isDevEnvironment ? "t3.small" : isProdEnvironment ? "t3.large" : "t3.medium",
    keyName: mainKeyPair.keyName,

    iamInstanceProfile: {
        name: workerServerInstanceProfile.name
    },

    blockDeviceMappings: [
        {
            deviceName: "/dev/xvda",
            ebs: {
                volumeSize: isDevEnvironment ? 30 : 50,
                volumeType: "gp3",
                encrypted: true,
                kmsKeyId: securityStackOutputs.applicationKeyArn,
                deleteOnTermination: true
            }
        }
    ],

    vpcSecurityGroupIds: [workerServerSg.id, securityStackOutputs.apiApplicationSgId],

    userData: workerServerUserData.apply(ud => Buffer.from(ud).toString('base64')),

    instanceInitiatedShutdownBehavior: "terminate",

    monitoring: {
        enabled: true
    },

    tagSpecifications: [
        {
            resourceType: "instance",
            tags: createResourceTags(deploymentConfig, "ec2-instance", {
                Name: createResourceName(deploymentConfig, "worker-server"),
                Type: "WorkerServer",
                Backup: "Required"
            })
        },
        {
            resourceType: "volume",
            tags: createResourceTags(deploymentConfig, "ebs-volume", {
                Name: createResourceName(deploymentConfig, "worker-server-volume"),
                Type: "WorkerServer",
                Backup: "Required"
            })
        }
    ],

    tags: createResourceTags(deploymentConfig, "launch-template", {
        Name: createResourceName(deploymentConfig, "worker-server-lt"),
        Purpose: "Worker Server Launch Template"
    })
});

// =============================================================================
// Application Load Balancer and Target Groups
// =============================================================================

// Application Load Balancer
const applicationLoadBalancer = new aws.lb.LoadBalancer("application-load-balancer", {
    name: createResourceName(deploymentConfig, "alb"),
    loadBalancerType: "application",
    scheme: "internet-facing",
    subnets: networkStackOutputs.publicSubnetIds,
    securityGroups: [securityStackOutputs.loadBalancerSgId],

    enableDeletionProtection: isProdEnvironment,

    accessLogs: storageStackOutputs ? {
        bucket: storageStackOutputs.logsBucketArn.apply(arn => arn.split(":::")[1]),
        prefix: "alb-access-logs",
        enabled: true
    } : undefined,

    tags: createResourceTags(deploymentConfig, "load-balancer", {
        Name: createResourceName(deploymentConfig, "alb"),
        Type: "Application Load Balancer"
    })
});

// Web Target Group
const webTargetGroup = new aws.lb.TargetGroup("web-target-group", {
    name: createResourceName(deploymentConfig, "web-tg"),
    port: COMMON_PORTS.NODEJS,
    protocol: "HTTP",
    vpcId: networkStackOutputs.vpcId,
    targetType: "instance",

    healthCheck: {
        enabled: true,
        healthyThreshold: 2,
        unhealthyThreshold: 3,
        timeout: 5,
        interval: 30,
        path: "/health",
        matcher: "200",
        port: "traffic-port",
        protocol: "HTTP"
    },

    stickiness: {
        enabled: !isDevEnvironment,
        type: "lb_cookie",
        cookieDuration: 86400
    },

    tags: createResourceTags(deploymentConfig, "target-group", {
        Name: createResourceName(deploymentConfig, "web-tg"),
        Purpose: "Web Servers"
    })
});

// API Target Group
const apiTargetGroup = new aws.lb.TargetGroup("api-target-group", {
    name: createResourceName(deploymentConfig, "api-tg"),
    port: COMMON_PORTS.APPLICATION,
    protocol: "HTTP",
    vpcId: networkStackOutputs.vpcId,
    targetType: "instance",

    healthCheck: {
        enabled: true,
        healthyThreshold: 2,
        unhealthyThreshold: 3,
        timeout: 5,
        interval: 30,
        path: "/health",
        matcher: "200",
        port: "traffic-port",
        protocol: "HTTP"
    },

    tags: createResourceTags(deploymentConfig, "target-group", {
        Name: createResourceName(deploymentConfig, "api-tg"),
        Purpose: "API Servers"
    })
});

// HTTPS Listener
const httpsListener = new aws.lb.Listener("https-listener", {
    loadBalancerArn: applicationLoadBalancer.arn,
    port: COMMON_PORTS.HTTPS,
    protocol: "HTTPS",
    sslPolicy: "ELBSecurityPolicy-TLS-1-2-2017-01",
    certificateArn: dnsStackOutputs.wildcardCertificateArn,

    defaultActions: [
        {
            type: "forward",
            targetGroupArn: webTargetGroup.arn
        }
    ],

    tags: createResourceTags(deploymentConfig, "lb-listener", {
        Name: createResourceName(deploymentConfig, "https-listener"),
        Protocol: "HTTPS"
    })
});

// HTTP Listener (redirect to HTTPS)
const httpListener = new aws.lb.Listener("http-listener", {
    loadBalancerArn: applicationLoadBalancer.arn,
    port: COMMON_PORTS.HTTP,
    protocol: "HTTP",

    defaultActions: [
        {
            type: "redirect",
            redirect: {
                port: COMMON_PORTS.HTTPS.toString(),
                protocol: "HTTPS",
                statusCode: "HTTP_301"
            }
        }
    ],

    tags: createResourceTags(deploymentConfig, "lb-listener", {
        Name: createResourceName(deploymentConfig, "http-listener"),
        Protocol: "HTTP"
    })
});

// API Listener Rule
const apiListenerRule = new aws.lb.ListenerRule("api-listener-rule", {
    listenerArn: httpsListener.arn,
    priority: 100,

    actions: [
        {
            type: "forward",
            targetGroupArn: apiTargetGroup.arn
        }
    ],

    conditions: [
        {
            pathPattern: {
                values: ["/api/*"]
            }
        }
    ],

    tags: createResourceTags(deploymentConfig, "lb-listener-rule", {
        Name: createResourceName(deploymentConfig, "api-rule"),
        Purpose: "API Routing"
    })
});

// =============================================================================
// Auto Scaling Groups
// =============================================================================

// Web Server Auto Scaling Group
const webServerAsg = new aws.autoscaling.Group("web-server-asg", {
    name: createResourceName(deploymentConfig, "web-asg"),
    vpcZoneIdentifiers: networkStackOutputs.privateSubnetIds,

    launchTemplate: {
        id: webServerLaunchTemplate.id,
        version: "$Latest"
    },

    minSize: envConfig.autoScaling.minCapacity,
    maxSize: envConfig.autoScaling.maxCapacity,
    desiredCapacity: envConfig.autoScaling.minCapacity,

    targetGroupArns: [webTargetGroup.arn],
    healthCheckType: "ELB",
    healthCheckGracePeriod: 300,

    enabledMetrics: [
        "GroupMinSize",
        "GroupMaxSize",
        "GroupDesiredCapacity",
        "GroupInServiceInstances",
        "GroupTotalInstances"
    ],

    instanceRefresh: {
        strategy: "Rolling",
        preferences: {
            minHealthyPercentage: 50,
            instanceWarmup: 300
        }
    },

    tags: [
        {
            key: "Name",
            value: createResourceName(deploymentConfig, "web-server"),
            propagateAtLaunch: true
        },
        {
            key: "Type",
            value: "WebServer",
            propagateAtLaunch: true
        },
        {
            key: "Environment",
            value: deploymentConfig.environment,
            propagateAtLaunch: true
        },
        {
            key: "Project",
            value: deploymentConfig.projectName,
            propagateAtLaunch: true
        },
        {
            key: "DeploymentID",
            value: deploymentConfig.deploymentId,
            propagateAtLaunch: true
        }
    ]
});

// Worker Server Auto Scaling Group
const workerServerAsg = new aws.autoscaling.Group("worker-server-asg", {
    name: createResourceName(deploymentConfig, "worker-asg"),
    vpcZoneIdentifiers: networkStackOutputs.privateSubnetIds,

    launchTemplate: {
        id: workerServerLaunchTemplate.id,
        version: "$Latest"
    },

    minSize: isDevEnvironment ? 1 : 2,
    maxSize: isDevEnvironment ? 3 : 6,
    desiredCapacity: isDevEnvironment ? 1 : 2,

    targetGroupArns: [apiTargetGroup.arn],
    healthCheckType: "EC2",
    healthCheckGracePeriod: 300,

    enabledMetrics: [
        "GroupMinSize",
        "GroupMaxSize",
        "GroupDesiredCapacity",
        "GroupInServiceInstances",
        "GroupTotalInstances"
    ],

    instanceRefresh: {
        strategy: "Rolling",
        preferences: {
            minHealthyPercentage: 50,
            instanceWarmup: 300
        }
    },

    tags: [
        {
            key: "Name",
            value: createResourceName(deploymentConfig, "worker-server"),
            propagateAtLaunch: true
        },
        {
            key: "Type",
            value: "WorkerServer",
            propagateAtLaunch: true
        },
        {
            key: "Environment",
            value: deploymentConfig.environment,
            propagateAtLaunch: true
        },
        {
            key: "Project",
            value: deploymentConfig.projectName,
            propagateAtLaunch: true
        },
        {
            key: "DeploymentID",
            value: deploymentConfig.deploymentId,
            propagateAtLaunch: true
        }
    ]
});

// =============================================================================
// Auto Scaling Policies
// =============================================================================

// Web Server Scale Up Policy
const webServerScaleUpPolicy = new aws.autoscaling.Policy("web-server-scale-up-policy", {
    name: createResourceName(deploymentConfig, "web-scale-up"),
    scalingAdjustment: 1,
    adjustmentType: "ChangeInCapacity",
    cooldown: 300,
    autoscalingGroupName: webServerAsg.name,
    policyType: "SimpleScaling"
});

// Web Server Scale Down Policy
const webServerScaleDownPolicy = new aws.autoscaling.Policy("web-server-scale-down-policy", {
    name: createResourceName(deploymentConfig, "web-scale-down"),
    scalingAdjustment: -1,
    adjustmentType: "ChangeInCapacity",
    cooldown: 300,
    autoscalingGroupName: webServerAsg.name,
    policyType: "SimpleScaling"
});

// Worker Server Scale Up Policy
const workerServerScaleUpPolicy = new aws.autoscaling.Policy("worker-server-scale-up-policy", {
    name: createResourceName(deploymentConfig, "worker-scale-up"),
    scalingAdjustment: 1,
    adjustmentType: "ChangeInCapacity",
    cooldown: 300,
    autoscalingGroupName: workerServerAsg.name,
    policyType: "SimpleScaling"
});

// Worker Server Scale Down Policy
const workerServerScaleDownPolicy = new aws.autoscaling.Policy("worker-server-scale-down-policy", {
    name: createResourceName(deploymentConfig, "worker-scale-down"),
    scalingAdjustment: -1,
    adjustmentType: "ChangeInCapacity",
    cooldown: 300,
    autoscalingGroupName: workerServerAsg.name,
    policyType: "SimpleScaling"
});

// =============================================================================
// CloudWatch Alarms
// =============================================================================

// Web Server High CPU Alarm
const webServerHighCpuAlarm = new aws.cloudwatch.MetricAlarm("web-server-high-cpu-alarm", {
    name: createResourceName(deploymentConfig, "web-high-cpu"),
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 2,
    metricName: "CPUUtilization",
    namespace: "AWS/EC2",
    period: 300,
    statistic: "Average",
    threshold: envConfig.autoScaling.targetCpuUtilization + 10,
    alarmDescription: "This metric monitors web server CPU utilization",

    dimensions: {
        AutoScalingGroupName: webServerAsg.name
    },

    alarmActions: [webServerScaleUpPolicy.arn],

    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "web-high-cpu"),
        Type: "ScaleUp"
    })
});

// Web Server Low CPU Alarm
const webServerLowCpuAlarm = new aws.cloudwatch.MetricAlarm("web-server-low-cpu-alarm", {
    name: createResourceName(deploymentConfig, "web-low-cpu"),
    comparisonOperator: "LessThanThreshold",
    evaluationPeriods: 2,
    metricName: "CPUUtilization",
    namespace: "AWS/EC2",
    period: 300,
    statistic: "Average",
    threshold: envConfig.autoScaling.targetCpuUtilization - 20,
    alarmDescription: "This metric monitors web server CPU utilization for scale down",

    dimensions: {
        AutoScalingGroupName: webServerAsg.name
    },

    alarmActions: [webServerScaleDownPolicy.arn],

    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "web-low-cpu"),
        Type: "ScaleDown"
    })
});

// Worker Server High CPU Alarm
const workerServerHighCpuAlarm = new aws.cloudwatch.MetricAlarm("worker-server-high-cpu-alarm", {
    name: createResourceName(deploymentConfig, "worker-high-cpu"),
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 2,
    metricName: "CPUUtilization",
    namespace: "AWS/EC2",
    period: 300,
    statistic: "Average",
    threshold: 70,
    alarmDescription: "This metric monitors worker server CPU utilization",

    dimensions: {
        AutoScalingGroupName: workerServerAsg.name
    },

    alarmActions: [workerServerScaleUpPolicy.arn],

    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "worker-high-cpu"),
        Type: "ScaleUp"
    })
});

// Worker Server Low CPU Alarm
const workerServerLowCpuAlarm = new aws.cloudwatch.MetricAlarm("worker-server-low-cpu-alarm", {
    name: createResourceName(deploymentConfig, "worker-low-cpu"),
    comparisonOperator: "LessThanThreshold",
    evaluationPeriods: 2,
    metricName: "CPUUtilization",
    namespace: "AWS/EC2",
    period: 300,
    statistic: "Average",
    threshold: 30,
    alarmDescription: "This metric monitors worker server CPU utilization for scale down",

    dimensions: {
        AutoScalingGroupName: workerServerAsg.name
    },

    alarmActions: [workerServerScaleDownPolicy.arn],

    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "worker-low-cpu"),
        Type: "ScaleDown"
    })
});

// ALB Health Alarm
const albHealthyTargetsAlarm = new aws.cloudwatch.MetricAlarm("alb-healthy-targets-alarm", {
    name: createResourceName(deploymentConfig, "alb-healthy-targets"),
    comparisonOperator: "LessThanThreshold",
    evaluationPeriods: 2,
    metricName: "HealthyHostCount",
    namespace: "AWS/ApplicationELB",
    period: 300,
    statistic: "Average",
    threshold: 1,
    alarmDescription: "This metric monitors healthy targets behind the ALB",
    treatMissingData: "breaching",

    dimensions: {
        TargetGroup: webTargetGroup.arnSuffix,
        LoadBalancer: applicationLoadBalancer.arnSuffix
    },

    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "alb-healthy-targets"),
        Type: "Health"
    })
});

// =============================================================================
// CloudWatch Log Groups
// =============================================================================

const webServerLogGroup = new aws.cloudwatch.LogGroup("web-server-log-group", {
    name: `/aws/ec2/web-server/${deploymentConfig.deploymentId}`,
    retentionInDays: isDevEnvironment ? 7 : 30,
    kmsKeyId: securityStackOutputs.applicationKeyArn,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Name: createResourceName(deploymentConfig, "web-server-logs"),
        Purpose: "Web Server Logs"
    })
});

const workerServerLogGroup = new aws.cloudwatch.LogGroup("worker-server-log-group", {
    name: `/aws/ec2/worker-server/${deploymentConfig.deploymentId}`,
    retentionInDays: isDevEnvironment ? 7 : 30,
    kmsKeyId: securityStackOutputs.applicationKeyArn,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Name: createResourceName(deploymentConfig, "worker-server-logs"),
        Purpose: "Worker Server Logs"
    })
});

// =============================================================================
// DNS Records for Load Balancer
// =============================================================================

// Primary domain A record
const primaryDomainRecord = new aws.route53.Record("primary-domain-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: dnsStackOutputs.domainName,
    type: "A",

    aliases: [{
        name: applicationLoadBalancer.dnsName,
        zoneId: applicationLoadBalancer.zoneId,
        evaluateTargetHealth: true
    }]
});

// WWW subdomain A record
const wwwDomainRecord = new aws.route53.Record("www-domain-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: pulumi.interpolate`www.${dnsStackOutputs.domainName}`,
    type: "A",

    aliases: [{
        name: applicationLoadBalancer.dnsName,
        zoneId: applicationLoadBalancer.zoneId,
        evaluateTargetHealth: true
    }]
});

// API subdomain A record
const apiDomainRecord = new aws.route53.Record("api-domain-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: pulumi.interpolate`api.${dnsStackOutputs.domainName}`,
    type: "A",

    aliases: [{
        name: applicationLoadBalancer.dnsName,
        zoneId: applicationLoadBalancer.zoneId,
        evaluateTargetHealth: true
    }]
});

// =============================================================================
// Exports - All required outputs for other stacks to consume
// =============================================================================

export const webAsgName = webServerAsg.name;
export const webAsgArn = webServerAsg.arn;
export const workerAsgName = workerServerAsg.name;
export const workerAsgArn = workerServerAsg.arn;

export const albDnsName = applicationLoadBalancer.dnsName;
export const albArn = applicationLoadBalancer.arn;
export const albZoneId = applicationLoadBalancer.zoneId;
export const albHostedZoneId = applicationLoadBalancer.zoneId;

export const webTargetGroupArn = webTargetGroup.arn;
export const apiTargetGroupArn = apiTargetGroup.arn;

export const webServerRoleArn = webServerRole.arn;
export const webServerRoleName = webServerRole.name;
export const workerServerRoleArn = workerServerRole.arn;
export const workerServerRoleName = workerServerRole.name;

export const keyPairName = mainKeyPair.keyName;
export const keyPairId = mainKeyPair.keyPairId;

export const webServerSgId = webServerSg.id;
export const workerServerSgId = workerServerSg.id;

export const webServerLaunchTemplateId = webServerLaunchTemplate.id;
export const workerServerLaunchTemplateId = workerServerLaunchTemplate.id;

export const webServerLogGroupName = webServerLogGroup.name;
export const workerServerLogGroupName = workerServerLogGroup.name;

// DNS Records
export const primaryDomainRecordName = primaryDomainRecord.name;
export const wwwDomainRecordName = wwwDomainRecord.name;
export const apiDomainRecordName = apiDomainRecord.name;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information for monitoring and management
export const summary = {
    loadBalancer: {
        dnsName: albDnsName,
        arn: albArn,
        type: "Application Load Balancer",
        scheme: "internet-facing",
        targetGroups: {
            web: webTargetGroupArn,
            api: apiTargetGroupArn
        }
    },
    autoScaling: {
        webServers: {
            asgName: webAsgName,
            minSize: envConfig.autoScaling.minCapacity,
            maxSize: envConfig.autoScaling.maxCapacity,
            instanceType: isDevEnvironment ? "t3.small" : isProdEnvironment ? "t3.medium" : "t3.small"
        },
        workerServers: {
            asgName: workerAsgName,
            minSize: isDevEnvironment ? 1 : 2,
            maxSize: isDevEnvironment ? 3 : 6,
            instanceType: isDevEnvironment ? "t3.small" : isProdEnvironment ? "t3.large" : "t3.medium"
        }
    },
    security: {
        keyPair: keyPairName,
        webServerSg: webServerSgId,
        workerServerSg: workerServerSgId
    },
    iam: {
        webServerRole: webServerRoleArn,
        workerServerRole: workerServerRoleArn
    },
    monitoring: {
        webServerLogs: webServerLogGroupName,
        workerServerLogs: workerServerLogGroupName,
        alarms: {
            webCpu: {
                high: webServerHighCpuAlarm.name,
                low: webServerLowCpuAlarm.name
            },
            workerCpu: {
                high: workerServerHighCpuAlarm.name,
                low: workerServerLowCpuAlarm.name
            },
            albHealth: albHealthyTargetsAlarm.name
        }
    },
    dns: {
        primary: primaryDomainRecordName,
        www: wwwDomainRecordName,
        api: apiDomainRecordName
    }
};

// Environment-specific compute configurations
export const computeConfig = {
    environment: deploymentConfig.environment,
    instances: {
        webServer: {
            type: isDevEnvironment ? "t3.small" : isProdEnvironment ? "t3.medium" : "t3.small",
            ebsSize: isDevEnvironment ? 20 : 30,
            monitoring: true,
            encryption: true
        },
        workerServer: {
            type: isDevEnvironment ? "t3.small" : isProdEnvironment ? "t3.large" : "t3.medium",
            ebsSize: isDevEnvironment ? 30 : 50,
            monitoring: true,
            encryption: true
        }
    },
    autoScaling: {
        enabled: true,
        cpuTarget: envConfig.autoScaling.targetCpuUtilization,
        cooldownPeriod: 300,
        healthCheckGracePeriod: 300
    },
    loadBalancer: {
        type: "application",
        scheme: "internet-facing",
        deletionProtection: isProdEnvironment,
        accessLogs: !!storageStackOutputs,
        sslPolicy: "ELBSecurityPolicy-TLS-1-2-2017-01"
    },
    monitoring: {
        cloudWatch: true,
        detailedMonitoring: true,
        logRetentionDays: isDevEnvironment ? 7 : 30,
        metricsNamespace: `${deploymentConfig.projectName}-${deploymentConfig.deploymentId}`
    }
};