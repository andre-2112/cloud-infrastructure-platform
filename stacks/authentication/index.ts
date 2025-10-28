import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    SecurityOutputs,
    SecretsOutputs,
    isDevelopment
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Get dependency stack outputs
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

const STACK_NAME = "authentication";

// Authentication Stack - Creates AWS Cognito infrastructure
console.log(`🚀 Deploying Authentication Stack for environment: ${deploymentConfig.environment}`);

// =============================================================================
// Cognito User Pool
// =============================================================================

// User Pool
const userPool = new aws.cognito.UserPool("user-pool", {
    name: createResourceName(deploymentConfig, "user-pool"),

    // Password policy
    passwordPolicy: {
        minimumLength: 8,
        requireLowercase: true,
        requireNumbers: true,
        requireSymbols: true,
        requireUppercase: true,
        temporaryPasswordValidityDays: 7
    },

    // Account recovery
    accountRecoverySetting: {
        recoveryMechanisms: [
            {
                name: "verified_email",
                priority: 1
            },
            {
                name: "verified_phone_number",
                priority: 2
            }
        ]
    },

    // User attributes
    attributes: ["email", "phone_number", "name", "family_name", "given_name"],
    aliasAttributes: ["email"],
    autoVerifiedAttributes: ["email"],

    // Username configuration
    usernameConfiguration: {
        caseSensitive: false
    },

    // Email verification
    emailVerificationMessage: "Your verification code is {####}",
    emailVerificationSubject: `${deploymentConfig.projectName} - Verify your email`,

    // MFA configuration
    mfaConfiguration: isDevelopment(deploymentConfig) ? "OFF" : "OPTIONAL",

    // Admin create user configuration
    adminCreateUserConfig: {
        allowAdminCreateUserOnly: false,
        inviteMessageAction: "EMAIL",
        temporaryPasswordValidityDays: 7
    },

    // Device configuration
    deviceConfiguration: {
        challengeRequiredOnNewDevice: true,
        deviceOnlyRememberedOnUserPrompt: false
    },

    tags: createResourceTags(deploymentConfig, "user-pool", {
        Name: createResourceName(deploymentConfig, "user-pool"),
        Component: "Authentication"
    })
});

// User Pool Domain
const userPoolDomain = new aws.cognito.UserPoolDomain("user-pool-domain", {
    domain: createResourceName(deploymentConfig, "auth"),
    userPoolId: userPool.id
});

// =============================================================================
// User Pool Clients
// =============================================================================

// Web Application Client
const webClientId = new aws.cognito.UserPoolClient("web-client", {
    name: createResourceName(deploymentConfig, "web-client"),
    userPoolId: userPool.id,

    generateSecret: false, // Public client for web apps
    explicitAuthFlows: [
        "ADMIN_NO_SRP_AUTH",
        "USER_PASSWORD_AUTH",
        "ALLOW_ADMIN_USER_PASSWORD_AUTH",
        "ALLOW_REFRESH_TOKEN_AUTH"
    ],

    // OAuth configuration
    supportedIdentityProviders: ["COGNITO", "Google", "GitHub"],
    callbackUrls: [
        `https://${deploymentConfig.deployDomain}/auth/callback`,
        `https://www.${deploymentConfig.deployDomain}/auth/callback`
    ],
    logoutUrls: [
        `https://${deploymentConfig.deployDomain}/auth/logout`,
        `https://www.${deploymentConfig.deployDomain}/auth/logout`
    ],

    allowedOauthFlows: ["code", "implicit"],
    allowedOauthFlowsUserPoolClient: true,
    allowedOauthScopes: ["email", "openid", "profile"],

    // Token validity
    accessTokenValidity: 1, // 1 hour
    idTokenValidity: 1, // 1 hour
    refreshTokenValidity: 30, // 30 days
    tokenValidityUnits: {
        accessToken: "hours",
        idToken: "hours",
        refreshToken: "days"
    },

    // Prevent user existence errors
    preventUserExistenceErrors: "ENABLED"
});

// Mobile Application Client
const mobileClient = new aws.cognito.UserPoolClient("mobile-client", {
    name: createResourceName(deploymentConfig, "mobile-client"),
    userPoolId: userPool.id,

    generateSecret: true, // Confidential client for mobile apps
    explicitAuthFlows: [
        "ALLOW_ADMIN_USER_PASSWORD_AUTH",
        "ALLOW_CUSTOM_AUTH",
        "ALLOW_USER_PASSWORD_AUTH",
        "ALLOW_REFRESH_TOKEN_AUTH"
    ],

    // OAuth configuration for mobile
    supportedIdentityProviders: ["COGNITO", "Google", "GitHub"],
    callbackUrls: [
        `https://api.${deploymentConfig.deployDomain}/auth/mobile/callback`
    ],
    logoutUrls: [
        `https://api.${deploymentConfig.deployDomain}/auth/mobile/logout`
    ],

    allowedOauthFlows: ["code"],
    allowedOauthFlowsUserPoolClient: true,
    allowedOauthScopes: ["email", "openid", "profile"],

    // Token validity
    accessTokenValidity: 1, // 1 hour
    idTokenValidity: 1, // 1 hour
    refreshTokenValidity: 30, // 30 days
    tokenValidityUnits: {
        accessToken: "hours",
        idToken: "hours",
        refreshToken: "days"
    },

    preventUserExistenceErrors: "ENABLED"
});

// Administrative Client (for backend operations)
const adminClient = new aws.cognito.UserPoolClient("admin-client", {
    name: createResourceName(deploymentConfig, "admin-client"),
    userPoolId: userPool.id,

    generateSecret: true,
    explicitAuthFlows: [
        "ALLOW_ADMIN_USER_PASSWORD_AUTH",
        "ALLOW_REFRESH_TOKEN_AUTH"
    ],

    // No OAuth for admin client
    supportedIdentityProviders: ["COGNITO"],

    // Longer validity for admin operations
    accessTokenValidity: 8, // 8 hours
    idTokenValidity: 8, // 8 hours
    refreshTokenValidity: 7, // 7 days
    tokenValidityUnits: {
        accessToken: "hours",
        idToken: "hours",
        refreshToken: "days"
    },

    preventUserExistenceErrors: "ENABLED"
});

// =============================================================================
// Identity Pool
// =============================================================================

const identityPool = new aws.cognito.IdentityPool("identity-pool", {
    identityPoolName: createResourceName(deploymentConfig, "identity-pool"),
    allowUnauthenticatedIdentities: false,
    allowClassicFlow: false,

    cognitoIdentityProviders: [
        {
            clientId: webClientId.id,
            providerName: userPool.endpoint,
            serverSideTokenCheck: true
        },
        {
            clientId: mobileClient.id,
            providerName: userPool.endpoint,
            serverSideTokenCheck: true
        }
    ],

    // OAuth providers (to be configured with real values)
    supportedLoginProviders: {
        "accounts.google.com": "placeholder_google_client_id",
        "github.com": "placeholder_github_client_id"
    },

    tags: createResourceTags(deploymentConfig, "identity-pool", {
        Name: createResourceName(deploymentConfig, "identity-pool"),
        Component: "Authentication"
    })
});

// =============================================================================
// IAM Roles for Identity Pool
// =============================================================================

// Authenticated role
const authenticatedRole = new aws.iam.Role("cognito-authenticated-role", {
    name: createResourceName(deploymentConfig, "cognito-authenticated-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: {
                    Federated: "cognito-identity.amazonaws.com"
                },
                Action: "sts:AssumeRoleWithWebIdentity",
                Condition: {
                    StringEquals: {
                        "cognito-identity.amazonaws.com:aud": identityPool.id
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                }
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "cognito-authenticated-role"),
        Component: "Authentication"
    })
});

// Authenticated role policy
const authenticatedRolePolicy = new aws.iam.RolePolicy("cognito-authenticated-role-policy", {
    role: authenticatedRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "mobileanalytics:PutEvents",
                    "cognito-sync:*",
                    "cognito-identity:*"
                ],
                Resource: "*"
            },
            {
                Effect: "Allow",
                Action: [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                Resource: `arn:aws:s3:::${deploymentConfig.projectName}-${deploymentConfig.deploymentId}-user-content/*`
            }
        ]
    })
});

// Identity pool role attachment
const identityPoolRoleAttachment = new aws.cognito.IdentityPoolRoleAttachment("identity-pool-roles", {
    identityPoolId: identityPool.id,
    roles: {
        authenticated: authenticatedRole.arn
    }
});

// =============================================================================
// Lambda Triggers (optional)
// =============================================================================

// Pre-signup Lambda trigger
const preSignupLambda = new aws.lambda.Function("pre-signup-lambda", {
    name: createResourceName(deploymentConfig, "pre-signup-trigger"),
    runtime: "python3.9",
    handler: "lambda_function.lambda_handler",
    role: securityStackOutputs.ecsExecutionRoleArn, // Reuse existing role

    code: new pulumi.asset.AssetArchive({
        "lambda_function.py": new pulumi.asset.StringAsset(`
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Pre-signup Lambda trigger for custom validation
    """
    logger.info(f"Pre-signup trigger: {json.dumps(event, indent=2)}")

    # Auto-confirm user in development
    if event.get('triggerSource') == 'PreSignUp_SignUp':
        event['response']['autoConfirmUser'] = True
        event['response']['autoVerifyEmail'] = True

    return event
        `)
    }),

    timeout: 30,
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Name: createResourceName(deploymentConfig, "pre-signup-trigger"),
        Component: "Authentication"
    })
});

// Lambda permission for Cognito
const preSignupLambdaPermission = new aws.lambda.Permission("pre-signup-lambda-permission", {
    action: "lambda:InvokeFunction",
    function: preSignupLambda.name,
    principal: "cognito-idp.amazonaws.com",
    sourceArn: userPool.arn
});

// Update user pool with Lambda trigger
const userPoolLambdaConfig = new aws.cognito.UserPool("user-pool-with-triggers", {
    name: createResourceName(deploymentConfig, "user-pool"),

    // Inherit all previous configuration
    passwordPolicy: {
        minimumLength: 8,
        requireLowercase: true,
        requireNumbers: true,
        requireSymbols: true,
        requireUppercase: true,
        temporaryPasswordValidityDays: 7
    },

    accountRecoverySetting: {
        recoveryMechanisms: [
            {
                name: "verified_email",
                priority: 1
            }
        ]
    },

    attributes: ["email", "phone_number", "name"],
    aliasAttributes: ["email"],
    autoVerifiedAttributes: ["email"],

    mfaConfiguration: isDevelopment(deploymentConfig) ? "OFF" : "OPTIONAL",

    // Lambda triggers
    lambdaConfig: {
        preSignUp: preSignupLambda.arn
    },

    tags: createResourceTags(deploymentConfig, "user-pool", {
        Name: createResourceName(deploymentConfig, "user-pool"),
        Component: "Authentication"
    })
}, { replaceOnChanges: ["name"] });

// Export all stack outputs
export const userPoolId = userPool.id;
export const userPoolArn = userPool.arn;
export const userPoolEndpoint = userPool.endpoint;
export const userPoolDomainName = userPoolDomain.domain;

export const webClientId = webClientId.id;
export const mobileClientId = mobileClient.id;
export const adminClientId = adminClient.id;

export const identityPoolId = identityPool.id;
export const identityPoolArn = identityPool.arn;

export const authenticatedRoleArn = authenticatedRole.arn;
export const preSignupLambdaArn = preSignupLambda.arn;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information
export const summary = {
    userPool: {
        id: userPoolId,
        arn: userPoolArn,
        endpoint: userPoolEndpoint,
        domain: userPoolDomainName
    },
    clients: {
        web: webClientId,
        mobile: mobileClientId,
        admin: adminClientId
    },
    identityPool: {
        id: identityPoolId,
        arn: identityPoolArn
    },
    roles: {
        authenticated: authenticatedRoleArn
    },
    triggers: {
        preSignup: preSignupLambdaArn
    }
};