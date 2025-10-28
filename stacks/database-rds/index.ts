import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    SecretsOutputs,
    isDevelopment,
    isProduction,
    ENVIRONMENT_DEFAULTS,
    COMMON_PORTS,
    createLogGroup
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();
const STACK_NAME = "database-rds";

// Get stack outputs from dependencies
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

const secretsStackOutputs: SecretsOutputs = {
    databaseMasterPasswordArn: centralState.getStackOutput<string>("secrets", "databaseMasterPasswordArn"),
    jwtSigningKeyArn: centralState.getStackOutput<string>("secrets", "jwtSigningKeyArn"),
    sessionSecretArn: centralState.getStackOutput<string>("secrets", "sessionSecretArn"),
    externalApiKeysArn: centralState.getStackOutput<string>("secrets", "externalApiKeysArn"),
    secretsReadPolicyArn: centralState.getStackOutput<string>("secrets", "secretsReadPolicyArn")
};

console.log(`🚀 Deploying Database RDS Stack for environment: ${deploymentConfig.environment}`);

// =============================================================================
// Environment-specific Configuration
// =============================================================================

const environmentConfig = ENVIRONMENT_DEFAULTS[deploymentConfig.environment];
const isMultiAZ = isProduction(deploymentConfig);
const enableReadReplica = isProduction(deploymentConfig);

// Database configuration based on environment
const databaseConfig = {
    instanceClass: environmentConfig.instanceSizes.database,
    allocatedStorage: isDevelopment(deploymentConfig) ? 20 : 100,
    maxAllocatedStorage: isDevelopment(deploymentConfig) ? 100 : 1000,
    engineVersion: "15.8", // PostgreSQL 15.8
    backupRetentionPeriod: environmentConfig.backup.retentionDays,
    backupWindow: environmentConfig.backup.backupWindow,
    maintenanceWindow: "sun:04:00-sun:05:00",
    performanceInsightsRetentionPeriod: isDevelopment(deploymentConfig) ? 7 : 731, // 7 days dev, 2 years prod
    enablePerformanceInsights: true,
    enableEnhancedMonitoring: !isDevelopment(deploymentConfig),
    monitoringInterval: isDevelopment(deploymentConfig) ? 0 : 60,
    enableCloudwatchLogsExports: ["postgresql"]
};

// =============================================================================
// Database Subnet Group
// =============================================================================

const databaseSubnetGroup = new aws.rds.SubnetGroup("database-subnet-group", {
    name: createResourceName(deploymentConfig, "db-subnet-group"),
    subnetIds: networkStackOutputs.databaseSubnetIds,
    description: `Database subnet group for ${deploymentConfig.projectName}`,
    tags: createResourceTags(deploymentConfig, "db-subnet-group", {
        Name: createResourceName(deploymentConfig, "db-subnet-group"),
        Component: "Database",
        Type: "SubnetGroup"
    })
});

// =============================================================================
// Database Parameter Group
// =============================================================================

const databaseParameterGroup = new aws.rds.ParameterGroup("database-parameter-group", {
    name: createResourceName(deploymentConfig, "db-param-group"),
    family: "postgres15",
    description: `PostgreSQL parameter group for ${deploymentConfig.projectName}`,
    parameters: [
        {
            name: "shared_preload_libraries",
            value: "pg_stat_statements"
        },
        {
            name: "log_statement",
            value: isDevelopment(deploymentConfig) ? "all" : "ddl"
        },
        {
            name: "log_min_duration_statement",
            value: isDevelopment(deploymentConfig) ? "100" : "1000"
        },
        {
            name: "log_checkpoints",
            value: "1"
        },
        {
            name: "log_connections",
            value: "1"
        },
        {
            name: "log_disconnections",
            value: "1"
        },
        {
            name: "log_lock_waits",
            value: "1"
        },
        {
            name: "log_temp_files",
            value: "0"
        },
        {
            name: "track_activity_query_size",
            value: "2048"
        },
        {
            name: "pg_stat_statements.track",
            value: "all"
        },
        {
            name: "pg_stat_statements.max",
            value: "10000"
        },
        {
            name: "max_connections",
            value: isDevelopment(deploymentConfig) ? "100" : "200"
        },
        {
            name: "effective_cache_size",
            value: isDevelopment(deploymentConfig) ? "128MB" : "1GB"
        }
    ],
    tags: createResourceTags(deploymentConfig, "db-param-group", {
        Name: createResourceName(deploymentConfig, "db-param-group"),
        Component: "Database",
        Type: "ParameterGroup"
    })
});

// =============================================================================
// Database Option Group (for PostgreSQL extensions)
// =============================================================================

const databaseOptionGroup = new aws.rds.OptionGroup("database-option-group", {
    name: createResourceName(deploymentConfig, "db-option-group"),
    engineName: "postgres",
    majorEngineVersion: "15",
    optionGroupDescription: `PostgreSQL option group for ${deploymentConfig.projectName}`,
    tags: createResourceTags(deploymentConfig, "db-option-group", {
        Name: createResourceName(deploymentConfig, "db-option-group"),
        Component: "Database",
        Type: "OptionGroup"
    })
});

// =============================================================================
// Enhanced Monitoring Role (for production)
// =============================================================================

const enhancedMonitoringRole = !databaseConfig.enableEnhancedMonitoring ? undefined : new aws.iam.Role("rds-enhanced-monitoring-role", {
    name: createResourceName(deploymentConfig, "rds-enhanced-monitoring-role"),
    description: "Role for RDS Enhanced Monitoring",
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: {
                    Service: "monitoring.rds.amazonaws.com"
                },
                Action: "sts:AssumeRole"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "rds-enhanced-monitoring-role"),
        Component: "Database",
        Type: "MonitoringRole"
    })
});

// Attach policy to enhanced monitoring role
const enhancedMonitoringRolePolicyAttachment = !enhancedMonitoringRole ? undefined : new aws.iam.RolePolicyAttachment("rds-enhanced-monitoring-role-policy", {
    role: enhancedMonitoringRole.name,
    policyArn: "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
});

// =============================================================================
// CloudWatch Log Groups
// =============================================================================

const databaseLogGroup = createLogGroup(
    createResourceName(deploymentConfig, "db-postgresql-logs"),
    isDevelopment(deploymentConfig) ? 7 : 30,
    createResourceTags(deploymentConfig, "log-group", {
        Component: "Database",
        Type: "PostgreSQLLogs"
    })
);

// =============================================================================
// Primary RDS Instance
// =============================================================================

const primaryDatabase = new aws.rds.Instance("primary-database", {
    identifier: createResourceName(deploymentConfig, "primary-db"),
    engine: "postgres",
    engineVersion: databaseConfig.engineVersion,
    instanceClass: databaseConfig.instanceClass,
    allocatedStorage: databaseConfig.allocatedStorage,
    maxAllocatedStorage: databaseConfig.maxAllocatedStorage,
    storageType: "gp3",
    storageEncrypted: true,
    kmsKeyId: securityStackOutputs.databaseKeyId,

    // Database configuration
    dbName: deploymentConfig.projectName.replace(/-/g, "_"),
    username: "dbadmin",
    manageUserPassword: true,
    masterUserSecretKmsKeyId: securityStackOutputs.databaseKeyId,

    // Network configuration
    dbSubnetGroupName: databaseSubnetGroup.name,
    vpcSecurityGroupIds: [securityStackOutputs.databaseSgId],
    port: COMMON_PORTS.POSTGRESQL,
    publiclyAccessible: false,
    multiAz: isMultiAZ,

    // Backup configuration
    backupRetentionPeriod: databaseConfig.backupRetentionPeriod,
    backupWindow: databaseConfig.backupWindow,
    copyTagsToSnapshot: true,
    deleteAutomatedBackups: isDevelopment(deploymentConfig),
    deletionProtection: isProduction(deploymentConfig),

    // Maintenance configuration
    maintenanceWindow: databaseConfig.maintenanceWindow,
    autoMinorVersionUpgrade: !isProduction(deploymentConfig),

    // Parameter and option groups
    parameterGroupName: databaseParameterGroup.name,
    optionGroupName: databaseOptionGroup.name,

    // Performance Insights
    performanceInsightsEnabled: databaseConfig.enablePerformanceInsights,
    performanceInsightsKmsKeyId: securityStackOutputs.databaseKeyId,
    performanceInsightsRetentionPeriod: databaseConfig.performanceInsightsRetentionPeriod,

    // Enhanced Monitoring
    monitoringInterval: databaseConfig.monitoringInterval,
    monitoringRoleArn: enhancedMonitoringRole?.arn,

    // CloudWatch Logs
    enabledCloudwatchLogsExports: databaseConfig.enableCloudwatchLogsExports,

    // Maintenance and lifecycle
    skipFinalSnapshot: isDevelopment(deploymentConfig),
    finalSnapshotIdentifier: isDevelopment(deploymentConfig) ? undefined :
        `${createResourceName(deploymentConfig, "primary-db")}-final-snapshot`,

    tags: createResourceTags(deploymentConfig, "rds-instance", {
        Name: createResourceName(deploymentConfig, "primary-db"),
        Component: "Database",
        Type: "Primary",
        Engine: "PostgreSQL"
    })
});

// =============================================================================
// Read Replica (Production only)
// =============================================================================

const readReplica = !enableReadReplica ? undefined : new aws.rds.Instance("read-replica-database", {
    identifier: createResourceName(deploymentConfig, "replica-db"),
    replicateSourceDb: primaryDatabase.identifier,
    instanceClass: databaseConfig.instanceClass,

    // Network configuration
    publiclyAccessible: false,
    vpcSecurityGroupIds: [securityStackOutputs.databaseSgId],

    // Performance Insights
    performanceInsightsEnabled: databaseConfig.enablePerformanceInsights,
    performanceInsightsKmsKeyId: securityStackOutputs.databaseKeyId,
    performanceInsightsRetentionPeriod: databaseConfig.performanceInsightsRetentionPeriod,

    // Enhanced Monitoring
    monitoringInterval: databaseConfig.monitoringInterval,
    monitoringRoleArn: enhancedMonitoringRole?.arn,

    // Maintenance configuration
    maintenanceWindow: "sun:05:00-sun:06:00", // Different window from primary
    autoMinorVersionUpgrade: false, // Managed separately

    // Lifecycle
    skipFinalSnapshot: false,
    finalSnapshotIdentifier: `${createResourceName(deploymentConfig, "replica-db")}-final-snapshot`,
    deletionProtection: true,

    tags: createResourceTags(deploymentConfig, "rds-instance", {
        Name: createResourceName(deploymentConfig, "replica-db"),
        Component: "Database",
        Type: "ReadReplica",
        Engine: "PostgreSQL"
    })
});

// =============================================================================
// CloudWatch Alarms
// =============================================================================

// High CPU alarm
const highCpuAlarm = new aws.cloudwatch.MetricAlarm("database-high-cpu-alarm", {
    name: createResourceName(deploymentConfig, "db-high-cpu-alarm"),
    description: "Database high CPU utilization alarm",
    metricName: "CPUUtilization",
    namespace: "AWS/RDS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: isDevelopment(deploymentConfig) ? 80 : 70,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        DBInstanceIdentifier: primaryDatabase.identifier
    },
    alarmActions: [], // Would typically include SNS topic ARN
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "db-high-cpu-alarm"),
        Component: "Database",
        Type: "CPUAlarm"
    })
});

// High connections alarm
const highConnectionsAlarm = new aws.cloudwatch.MetricAlarm("database-high-connections-alarm", {
    name: createResourceName(deploymentConfig, "db-high-connections-alarm"),
    description: "Database high connections alarm",
    metricName: "DatabaseConnections",
    namespace: "AWS/RDS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: isDevelopment(deploymentConfig) ? 80 : 150,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        DBInstanceIdentifier: primaryDatabase.identifier
    },
    alarmActions: [], // Would typically include SNS topic ARN
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "db-high-connections-alarm"),
        Component: "Database",
        Type: "ConnectionsAlarm"
    })
});

// Free storage space alarm
const lowStorageAlarm = new aws.cloudwatch.MetricAlarm("database-low-storage-alarm", {
    name: createResourceName(deploymentConfig, "db-low-storage-alarm"),
    description: "Database low free storage space alarm",
    metricName: "FreeStorageSpace",
    namespace: "AWS/RDS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 1,
    threshold: 2000000000, // 2GB in bytes
    comparisonOperator: "LessThanThreshold",
    dimensions: {
        DBInstanceIdentifier: primaryDatabase.identifier
    },
    alarmActions: [], // Would typically include SNS topic ARN
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Name: createResourceName(deploymentConfig, "db-low-storage-alarm"),
        Component: "Database",
        Type: "StorageAlarm"
    })
});

// =============================================================================
// Database Secrets Integration
// =============================================================================

// Create a secret version that stores the RDS master user secret ARN
const databaseCredentialsSecret = new aws.secretsmanager.Secret("database-credentials", {
    name: createResourceName(deploymentConfig, "db-credentials"),
    description: "Database connection credentials and endpoints",
    kmsKeyId: securityStackOutputs.databaseKeyId,
    tags: createResourceTags(deploymentConfig, "secret", {
        Name: createResourceName(deploymentConfig, "db-credentials"),
        Component: "Database",
        Type: "Credentials"
    })
});

const databaseCredentialsSecretVersion = new aws.secretsmanager.SecretVersion("database-credentials-version", {
    secretId: databaseCredentialsSecret.id,
    secretString: pulumi.all([
        primaryDatabase.endpoint,
        primaryDatabase.port,
        primaryDatabase.dbName,
        primaryDatabase.masterUserSecret.apply(secret => secret?.secretArn || ""),
        readReplica?.endpoint || pulumi.output("")
    ]).apply(([primaryEndpoint, port, dbName, masterUserSecretArn, replicaEndpoint]) =>
        JSON.stringify({
            primary: {
                endpoint: primaryEndpoint,
                port: port,
                database: dbName,
                masterUserSecretArn: masterUserSecretArn
            },
            replica: enableReadReplica ? {
                endpoint: replicaEndpoint,
                port: port,
                database: dbName
            } : null,
            connection: {
                maxConnections: isDevelopment(deploymentConfig) ? 20 : 50,
                poolSize: isDevelopment(deploymentConfig) ? 5 : 10,
                timeout: 30000
            }
        })
    )
});

// =============================================================================
// Outputs
// =============================================================================

// Primary database outputs
export const primaryEndpoint = primaryDatabase.endpoint;
export const primaryPort = primaryDatabase.port;
export const primaryDatabaseName = primaryDatabase.dbName;
export const primaryInstanceId = primaryDatabase.identifier;
export const primaryMasterUserSecretArn = primaryDatabase.masterUserSecret.apply(secret => secret?.secretArn || "");

// Read replica outputs (if enabled)
export const replicaEndpoint = readReplica?.endpoint;
export const replicaInstanceId = readReplica?.identifier;

// Subnet and parameter groups
export const subnetGroupName = databaseSubnetGroup.name;
export const parameterGroupName = databaseParameterGroup.name;
export const optionGroupName = databaseOptionGroup.name;

// Master user secret ARN (for compatibility with requirements)
export const masterUserSecretArn = primaryDatabase.masterUserSecret.apply(secret => secret?.secretArn || "");

// Database credentials secret
export const databaseCredentialsSecretArn = databaseCredentialsSecret.arn;

// Performance and monitoring
export const performanceInsightsEnabled = databaseConfig.enablePerformanceInsights;
export const enhancedMonitoringEnabled = databaseConfig.enableEnhancedMonitoring;

// CloudWatch alarms
export const cpuAlarmArn = highCpuAlarm.arn;
export const connectionsAlarmArn = highConnectionsAlarm.arn;
export const storageAlarmArn = lowStorageAlarm.arn;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information
export const summary = {
    database: {
        engine: "PostgreSQL",
        version: databaseConfig.engineVersion,
        instanceClass: databaseConfig.instanceClass,
        multiAZ: isMultiAZ,
        encrypted: true,
        performanceInsights: databaseConfig.enablePerformanceInsights,
        enhancedMonitoring: databaseConfig.enableEnhancedMonitoring
    },
    replica: {
        enabled: enableReadReplica,
        instanceId: replicaInstanceId
    },
    backup: {
        retentionPeriod: databaseConfig.backupRetentionPeriod,
        window: databaseConfig.backupWindow,
        deletionProtection: isProduction(deploymentConfig)
    },
    networking: {
        subnetGroup: subnetGroupName,
        securityGroup: securityStackOutputs.databaseSgId,
        port: COMMON_PORTS.POSTGRESQL
    },
    credentials: {
        masterUserSecret: masterUserSecretArn,
        databaseCredentialsSecret: databaseCredentialsSecretArn
    },
    monitoring: {
        cloudwatchLogs: databaseConfig.enableCloudwatchLogsExports,
        alarms: {
            cpu: cpuAlarmArn,
            connections: connectionsAlarmArn,
            storage: storageAlarmArn
        }
    }
};

console.log(`✅ Database RDS Stack deployment completed for environment: ${deploymentConfig.environment}`);
console.log(`📊 Primary Database: ${primaryDatabase.identifier}`);
if (enableReadReplica) {
    console.log(`📖 Read Replica: ${readReplica?.identifier}`);
}
console.log(`🔐 Encryption: Enabled with KMS`);
console.log(`📈 Performance Insights: ${databaseConfig.enablePerformanceInsights ? 'Enabled' : 'Disabled'}`);
console.log(`📋 Enhanced Monitoring: ${databaseConfig.enableEnhancedMonitoring ? 'Enabled' : 'Disabled'}`);