import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    SecurityOutputs,
    isDevelopment
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

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

const STACK_NAME = "secrets";

// Secrets Stack - Creates AWS Secrets Manager secrets for secure storage
console.log(`🚀 Deploying Secrets Stack for environment: ${deploymentConfig.environment}`);

// =============================================================================
// Database Secrets
// =============================================================================

// Database credential management removed - using RDS auto-managed credentials instead
// See database-rds stack for manageUserPassword: true configuration

// =============================================================================
// Application Secrets
// =============================================================================

// JWT signing key
const jwtSigningKey = new aws.secretsmanager.Secret("jwt-signing-key", {
    name: createResourceName(deploymentConfig, "jwt-signing-key"),
    description: "JWT signing key for application authentication",
    kmsKeyId: securityStackOutputs.applicationKeyId,
    tags: createResourceTags(deploymentConfig, "secret", {
        Name: createResourceName(deploymentConfig, "jwt-signing-key"),
        Type: "Authentication",
        Component: "JWT"
    })
});

const jwtSigningKeyValue = new aws.secretsmanager.SecretVersion("jwt-signing-key-value", {
    secretId: jwtSigningKey.id,
    secretString: JSON.stringify({
        algorithm: "RS256",
        privateKey: pulumi.output(aws.secretsmanager.getRandomPassword({
            length: 64,
            excludeCharacters: " \"@/\\",
            excludePunctuation: false
        })).password,
        publicKey: pulumi.output(aws.secretsmanager.getRandomPassword({
            length: 64,
            excludeCharacters: " \"@/\\",
            excludePunctuation: false
        })).password
    })
});

// Session secret
const sessionSecret = new aws.secretsmanager.Secret("session-secret", {
    name: createResourceName(deploymentConfig, "session-secret"),
    description: "Session secret for application session management",
    kmsKeyId: securityStackOutputs.applicationKeyId,
    tags: createResourceTags(deploymentConfig, "secret", {
        Name: createResourceName(deploymentConfig, "session-secret"),
        Type: "Authentication",
        Component: "Session"
    })
});

const sessionSecretValue = new aws.secretsmanager.SecretVersion("session-secret-value", {
    secretId: sessionSecret.id,
    secretString: JSON.stringify({
        secret: pulumi.output(aws.secretsmanager.getRandomPassword({
            length: 64,
            excludeCharacters: " \"@/\\",
            excludePunctuation: false
        })).password
    })
});

// =============================================================================
// External API Keys
// =============================================================================

// External API keys (Stripe, SendGrid, etc.)
const externalApiKeys = new aws.secretsmanager.Secret("external-api-keys", {
    name: createResourceName(deploymentConfig, "external-api-keys"),
    description: "External API keys for third-party services",
    kmsKeyId: securityStackOutputs.applicationKeyId,
    tags: createResourceTags(deploymentConfig, "secret", {
        Name: createResourceName(deploymentConfig, "external-api-keys"),
        Type: "API",
        Component: "External"
    })
});

const externalApiKeysValue = new aws.secretsmanager.SecretVersion("external-api-keys-value", {
    secretId: externalApiKeys.id,
    secretString: JSON.stringify({
        stripePublicKey: "pk_test_placeholder",
        stripeSecretKey: "sk_test_placeholder",
        sendgridApiKey: "SG.placeholder",
        githubClientId: "placeholder_github_client_id",
        githubClientSecret: "placeholder_github_client_secret",
        googleClientId: "placeholder_google_client_id",
        googleClientSecret: "placeholder_google_client_secret"
    })
});

// OAuth secrets
const oauthSecrets = new aws.secretsmanager.Secret("oauth-secrets", {
    name: createResourceName(deploymentConfig, "oauth-secrets"),
    description: "OAuth provider secrets and configuration",
    kmsKeyId: securityStackOutputs.applicationKeyId,
    tags: createResourceTags(deploymentConfig, "secret", {
        Name: createResourceName(deploymentConfig, "oauth-secrets"),
        Type: "Authentication",
        Component: "OAuth"
    })
});

const oauthSecretsValue = new aws.secretsmanager.SecretVersion("oauth-secrets-value", {
    secretId: oauthSecrets.id,
    secretString: JSON.stringify({
        googleOAuth: {
            clientId: "placeholder_google_oauth_client_id",
            clientSecret: "placeholder_google_oauth_client_secret",
            redirectUri: `https://${deploymentConfig.deployDomain}/auth/google/callback`
        },
        githubOAuth: {
            clientId: "placeholder_github_oauth_client_id",
            clientSecret: "placeholder_github_oauth_client_secret",
            redirectUri: `https://${deploymentConfig.deployDomain}/auth/github/callback`
        }
    })
});

// =============================================================================
// Redis Authentication
// =============================================================================

// Redis authentication password
const redisAuthPassword = new aws.secretsmanager.Secret("redis-auth-password", {
    name: createResourceName(deploymentConfig, "redis-auth-password"),
    description: "Redis authentication password",
    kmsKeyId: securityStackOutputs.applicationKeyId,
    tags: createResourceTags(deploymentConfig, "secret", {
        Name: createResourceName(deploymentConfig, "redis-auth-password"),
        Type: "Database",
        Component: "Redis"
    })
});

const redisAuthPasswordValue = new aws.secretsmanager.SecretVersion("redis-auth-password-value", {
    secretId: redisAuthPassword.id,
    secretString: JSON.stringify({
        password: pulumi.output(aws.secretsmanager.getRandomPassword({
            length: 32,
            excludeCharacters: " \"@/\\",
            excludePunctuation: false
        })).password
    })
});

// =============================================================================
// IAM Policies for Secrets Access
// =============================================================================

// Secrets read policy for applications
const secretsReadPolicy = new aws.iam.Policy("secrets-read-policy", {
    name: createResourceName(deploymentConfig, "secrets-read-policy"),
    description: "Policy to read application secrets",
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                Resource: [
                    jwtSigningKey.arn,
                    sessionSecret.arn,
                    externalApiKeys.arn,
                    oauthSecrets.arn,
                    redisAuthPassword.arn
                ]
            },
            {
                Effect: "Allow",
                Action: [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                Resource: [
                    securityStackOutputs.applicationKeyArn
                ]
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Name: createResourceName(deploymentConfig, "secrets-read-policy"),
        Type: "SecretsAccess"
    })
});

// Database secrets read policy
const databaseSecretsReadPolicy = new aws.iam.Policy("database-secrets-read-policy", {
    name: createResourceName(deploymentConfig, "db-secrets-read-policy"),
    description: "Policy to read database secrets",
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                Resource: [
                    // Database credentials now managed by RDS auto-management
                    // No manual secrets to reference
                ]
            },
            {
                Effect: "Allow",
                Action: [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                Resource: [
                    securityStackOutputs.databaseKeyArn
                ]
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Name: createResourceName(deploymentConfig, "db-secrets-read-policy"),
        Type: "DatabaseSecretsAccess"
    })
});

// Attach secrets read policy to ECS task role
const ecsTaskRoleSecretsAttachment = new aws.iam.RolePolicyAttachment("ecs-task-role-secrets-attachment", {
    role: securityStackOutputs.ecsTaskRoleArn.apply(arn => arn.split('/').pop()!),
    policyArn: secretsReadPolicy.arn
});

// =============================================================================
// Secret Rotation (Production only)
// =============================================================================

// Lambda function for secret rotation (production only)
const secretRotationFunction = isDevelopment(deploymentConfig) ? undefined : new aws.lambda.Function("secret-rotation-function", {
    name: createResourceName(deploymentConfig, "secret-rotation-function"),
    runtime: "python3.9",
    handler: "lambda_function.lambda_handler",
    role: securityStackOutputs.ecsExecutionRoleArn, // Reuse existing role for simplicity
    code: new pulumi.asset.AssetArchive({
        "lambda_function.py": new pulumi.asset.StringAsset(`
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to rotate secrets
    """
    logger.info(f"Rotating secret: {event}")

    # Secret rotation logic would go here
    # This is a placeholder implementation

    return {
        'statusCode': 200,
        'body': json.dumps('Secret rotation completed')
    }
        `)
    }),
    timeout: 300,
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Name: createResourceName(deploymentConfig, "secret-rotation-function"),
        Type: "SecretRotation"
    })
});

// CloudWatch log group for Lambda
const secretRotationLogGroup = isDevelopment(deploymentConfig) ? undefined : new aws.cloudwatch.LogGroup("secret-rotation-log-group", {
    name: `/aws/lambda/${secretRotationFunction!.name}`,
    retentionInDays: 14,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Name: createResourceName(deploymentConfig, "secret-rotation-logs"),
        Component: "SecretRotation"
    })
});

// Export all stack outputs
// Database credential exports removed - using RDS auto-managed credentials
export const jwtSigningKeyArn = jwtSigningKey.arn;
export const sessionSecretArn = sessionSecret.arn;
export const externalApiKeysArn = externalApiKeys.arn;
export const oauthSecretsArn = oauthSecrets.arn;
export const redisAuthPasswordArn = redisAuthPassword.arn;

export const secretsReadPolicyArn = secretsReadPolicy.arn;
export const databaseSecretsReadPolicyArn = databaseSecretsReadPolicy.arn;

export const secretRotationFunctionArn = secretRotationFunction?.arn;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information
export const summary = {
    secrets: {
        database: {
            // Database credentials managed by RDS auto-management
            // See database-rds stack outputs for credential ARNs
        },
        application: {
            jwtSigningKey: jwtSigningKeyArn,
            sessionSecret: sessionSecretArn,
            redisAuth: redisAuthPasswordArn
        },
        external: {
            apiKeys: externalApiKeysArn,
            oauthSecrets: oauthSecretsArn
        }
    },
    policies: {
        secretsRead: secretsReadPolicyArn,
        databaseSecretsRead: databaseSecretsReadPolicyArn
    },
    rotation: {
        enabled: !isDevelopment(deploymentConfig),
        functionArn: secretRotationFunctionArn
    }
};