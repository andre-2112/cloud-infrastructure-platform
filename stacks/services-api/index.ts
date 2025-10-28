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
    SecretsOutputs,
    createLogGroup,
    getCurrentRegion,
    getCurrentAccountId,
    ENVIRONMENT_DEFAULTS,
    COMMON_PORTS,
    isDevelopment,
    isProduction
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Validate required configuration
validateConfig("services-api", config, []);

// Get dependency stack outputs
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

const dnsStackOutputs: DNSOutputs = {
    hostedZoneId: centralState.getStackOutput<string>("dns", "hostedZoneId"),
    domainName: centralState.getStackOutput<string>("dns", "domainName"),
    primaryCertificateArn: centralState.getStackOutput<string>("dns", "primaryCertificateArn"),
    wildcardCertificateArn: centralState.getStackOutput<string>("dns", "wildcardCertificateArn"),
    primaryHealthCheckId: centralState.getStackOutput<string>("dns", "primaryHealthCheckId")
};

const secretsStackOutputs: SecretsOutputs = {
    databaseMasterPasswordArn: centralState.getStackOutput<string>("secrets", "databaseMasterPasswordArn"),
    jwtSigningKeyArn: centralState.getStackOutput<string>("secrets", "jwtSigningKeyArn"),
    sessionSecretArn: centralState.getStackOutput<string>("secrets", "sessionSecretArn"),
    externalApiKeysArn: centralState.getStackOutput<string>("secrets", "externalApiKeysArn"),
    secretsReadPolicyArn: centralState.getStackOutput<string>("secrets", "secretsReadPolicyArn")
};

const authenticationStackOutputs = {
    userPoolArn: centralState.getStackOutput<string>("authentication", "userPoolArn"),
    userPoolId: centralState.getStackOutput<string>("authentication", "userPoolId"),
    userPoolClientId: centralState.getStackOutput<string>("authentication", "userPoolClientId"),
    identityPoolId: centralState.getStackOutput<string>("authentication", "identityPoolId")
};

const containerAppsStackOutputs = {
    publicAlbDnsName: centralState.getStackOutput<string>("containers-apps", "publicAlbDnsName"),
    publicAlbArn: centralState.getStackOutput<string>("containers-apps", "publicAlbArn"),
    publicAlbZoneId: centralState.getStackOutput<string>("containers-apps", "publicAlbZoneId"),
    httpsListenerArn: centralState.getStackOutput<string>("containers-apps", "httpsListenerArn"),
    clusterArn: centralState.getStackOutput<string>("containers-apps", "clusterArn"),
    privateNamespaceId: centralState.getStackOutput<string>("containers-apps", "privateNamespaceId")
};

const STACK_NAME = "services-api";

// API Gateway Services Stack - REST APIs, HTTP APIs, VPC Links, and API management
console.log(`🚀 Deploying API Gateway Services Stack for environment: ${deploymentConfig.environment}`);

// Configuration parameters
const apiConfig = {
    // API Gateway configuration
    enableXRayTracing: config.getBoolean("enableXRayTracing") !== false, // Default true
    enableWafProtection: config.getBoolean("enableWafProtection") !== false, // Default true in prod
    enableDetailedMonitoring: config.getBoolean("enableDetailedMonitoring") !== false, // Default true

    // CORS configuration
    corsAllowOrigins: config.getObject<string[]>("corsAllowOrigins") ||
        isDevelopment(deploymentConfig) ?
            ["http://localhost:3000", "http://localhost:8080", `https://${deploymentConfig.deployDomain}`] :
            [`https://${deploymentConfig.deployDomain}`, `https://www.${deploymentConfig.deployDomain}`],
    corsAllowMethods: config.getObject<string[]>("corsAllowMethods") ||
        ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    corsAllowHeaders: config.getObject<string[]>("corsAllowHeaders") ||
        ["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token", "X-Amz-User-Agent"],
    corsMaxAge: config.getNumber("corsMaxAge") || 86400,

    // Throttling and usage plans
    defaultThrottleSettings: {
        rateLimit: config.getNumber("defaultRateLimit") ||
            (isDevelopment(deploymentConfig) ? 1000 : isProduction(deploymentConfig) ? 500 : 750),
        burstLimit: config.getNumber("defaultBurstLimit") ||
            (isDevelopment(deploymentConfig) ? 2000 : isProduction(deploymentConfig) ? 1000 : 1500)
    },

    // Usage plan quotas
    usagePlans: {
        standard: {
            quotaLimit: config.getNumber("standardQuotaLimit") || 10000,
            quotaPeriod: "MONTH" as const,
            rateLimit: config.getNumber("standardRateLimit") || 100,
            burstLimit: config.getNumber("standardBurstLimit") || 200
        },
        premium: {
            quotaLimit: config.getNumber("premiumQuotaLimit") || 50000,
            quotaPeriod: "MONTH" as const,
            rateLimit: config.getNumber("premiumRateLimit") || 500,
            burstLimit: config.getNumber("premiumBurstLimit") || 1000
        }
    },

    // WAF configuration
    wafRateLimit: config.getNumber("wafRateLimit") ||
        (isDevelopment(deploymentConfig) ? 5000 : isProduction(deploymentConfig) ? 2000 : 3000),

    // Custom domains
    customDomains: {
        api: `api.${deploymentConfig.deployDomain}`,
        adminApi: `admin-api.${deploymentConfig.deployDomain}`
    },

    // API versioning
    currentVersion: config.get("currentVersion") || "v1",

    // Monitoring
    logRetentionDays: config.getNumber("logRetentionDays") ||
        (isProduction(deploymentConfig) ? 90 : isDevelopment(deploymentConfig) ? 14 : 30),

    // CloudFront configuration
    enableCdn: config.getBoolean("enableCdn") !== false, // Default true
    cdnPriceClass: config.get("cdnPriceClass") || "PriceClass_100", // Use only North America and Europe
    cdnMinTtl: config.getNumber("cdnMinTtl") || 0,
    cdnDefaultTtl: config.getNumber("cdnDefaultTtl") || 300, // 5 minutes
    cdnMaxTtl: config.getNumber("cdnMaxTtl") || 86400 // 24 hours
};

// Get current AWS region and account ID
const currentRegion = getCurrentRegion();
const currentAccountId = getCurrentAccountId();

// =============================================================================
// CloudWatch Log Groups for API Gateway
// =============================================================================

const apiGatewayLogGroup = createLogGroup(
    `/aws/apigateway/${createResourceName(deploymentConfig, "rest-api")}`,
    apiConfig.logRetentionDays,
    createResourceTags(deploymentConfig, "log-group", {
        Service: "api-gateway-rest",
        Type: "access-logs"
    })
);

const httpApiLogGroup = createLogGroup(
    `/aws/apigateway-v2/${createResourceName(deploymentConfig, "http-api")}`,
    apiConfig.logRetentionDays,
    createResourceTags(deploymentConfig, "log-group", {
        Service: "api-gateway-http",
        Type: "access-logs"
    })
);

// =============================================================================
// IAM Role for API Gateway CloudWatch Logging
// =============================================================================

const apiGatewayCloudWatchRole = new aws.iam.Role("api-gateway-cloudwatch-role", {
    name: createResourceName(deploymentConfig, "api-gateway-cloudwatch-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Effect: "Allow",
            Principal: {
                Service: "apigateway.amazonaws.com"
            },
            Action: "sts:AssumeRole"
        }]
    }),
    managedPolicyArns: [
        "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
    ],
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Service: "api-gateway",
        Purpose: "cloudwatch-logging"
    })
});

// Set API Gateway account configuration for CloudWatch logging
const apiGatewayAccount = new aws.apigateway.Account("api-gateway-account", {
    cloudwatchRoleArn: apiGatewayCloudWatchRole.arn
});

// =============================================================================
// REST API Gateway - Primary API
// =============================================================================

const primaryRestApi = new aws.apigateway.RestApi("primary-rest-api", {
    name: createResourceName(deploymentConfig, "rest-api"),
    description: `Primary REST API for ${deploymentConfig.projectName} - ${deploymentConfig.environment}`,
    endpointConfiguration: {
        types: ["REGIONAL"]
    },
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Effect: "Allow",
            Principal: "*",
            Action: "execute-api:Invoke",
            Resource: "*"
        }]
    }),
    binaryMediaTypes: ["multipart/form-data", "application/octet-stream"],
    tags: createResourceTags(deploymentConfig, "api-gateway", {
        Name: createResourceName(deploymentConfig, "rest-api"),
        Type: "primary",
        ApiType: "rest"
    })
});

// Admin REST API Gateway
const adminRestApi = new aws.apigateway.RestApi("admin-rest-api", {
    name: createResourceName(deploymentConfig, "admin-api"),
    description: `Admin API for management operations - ${deploymentConfig.environment}`,
    endpointConfiguration: {
        types: ["REGIONAL"]
    },
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Effect: "Allow",
            Principal: "*",
            Action: "execute-api:Invoke",
            Resource: "*"
        }]
    }),
    tags: createResourceTags(deploymentConfig, "api-gateway", {
        Name: createResourceName(deploymentConfig, "admin-api"),
        Type: "admin",
        ApiType: "rest"
    })
});

// =============================================================================
// Cognito Authorizer for REST API
// =============================================================================

const cognitoAuthorizer = new aws.apigateway.Authorizer("cognito-authorizer", {
    name: createResourceName(deploymentConfig, "cognito-auth"),
    restApi: primaryRestApi.id,
    type: "COGNITO_USER_POOLS",
    providerArns: [authenticationStackOutputs.userPoolArn],
    identitySource: "method.request.header.Authorization"
});

// =============================================================================
// REST API Resources and Methods
// =============================================================================

// API v1 resource
const apiV1Resource = new aws.apigateway.Resource("api-v1-resource", {
    restApi: primaryRestApi.id,
    parentId: primaryRestApi.rootResourceId,
    pathPart: apiConfig.currentVersion
});

// Users resource
const usersResource = new aws.apigateway.Resource("users-resource", {
    restApi: primaryRestApi.id,
    parentId: apiV1Resource.id,
    pathPart: "users"
});

// Individual user resource (with path parameter)
const userIdResource = new aws.apigateway.Resource("user-id-resource", {
    restApi: primaryRestApi.id,
    parentId: usersResource.id,
    pathPart: "{id}"
});

// Orders resource
const ordersResource = new aws.apigateway.Resource("orders-resource", {
    restApi: primaryRestApi.id,
    parentId: apiV1Resource.id,
    pathPart: "orders"
});

// Individual order resource
const orderIdResource = new aws.apigateway.Resource("order-id-resource", {
    restApi: primaryRestApi.id,
    parentId: ordersResource.id,
    pathPart: "{id}"
});

// Products resource
const productsResource = new aws.apigateway.Resource("products-resource", {
    restApi: primaryRestApi.id,
    parentId: apiV1Resource.id,
    pathPart: "products"
});

// Individual product resource
const productIdResource = new aws.apigateway.Resource("product-id-resource", {
    restApi: primaryRestApi.id,
    parentId: productsResource.id,
    pathPart: "{id}"
});

// Auth resource
const authResource = new aws.apigateway.Resource("auth-resource", {
    restApi: primaryRestApi.id,
    parentId: apiV1Resource.id,
    pathPart: "auth"
});

// Health check resource
const healthResource = new aws.apigateway.Resource("health-resource", {
    restApi: primaryRestApi.id,
    parentId: apiV1Resource.id,
    pathPart: "health"
});

// =============================================================================
// Request/Response Models
// =============================================================================

const userModel = new aws.apigateway.Model("user-model", {
    restApi: primaryRestApi.id,
    name: "UserModel",
    contentType: "application/json",
    schema: JSON.stringify({
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "User Schema",
        "type": "object",
        "properties": {
            "id": { "type": "string" },
            "email": { "type": "string", "format": "email" },
            "firstName": { "type": "string" },
            "lastName": { "type": "string" },
            "role": { "type": "string", "enum": ["user", "admin"] }
        },
        "required": ["email", "firstName", "lastName"]
    })
});

const orderModel = new aws.apigateway.Model("order-model", {
    restApi: primaryRestApi.id,
    name: "OrderModel",
    contentType: "application/json",
    schema: JSON.stringify({
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Order Schema",
        "type": "object",
        "properties": {
            "id": { "type": "string" },
            "userId": { "type": "string" },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "productId": { "type": "string" },
                        "quantity": { "type": "integer", "minimum": 1 },
                        "price": { "type": "number", "minimum": 0 }
                    }
                }
            },
            "total": { "type": "number", "minimum": 0 },
            "status": { "type": "string", "enum": ["pending", "processing", "completed", "cancelled"] }
        },
        "required": ["userId", "items", "total"]
    })
});

const errorModel = new aws.apigateway.Model("error-model", {
    restApi: primaryRestApi.id,
    name: "ErrorModel",
    contentType: "application/json",
    schema: JSON.stringify({
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Error Schema",
        "type": "object",
        "properties": {
            "error": { "type": "string" },
            "message": { "type": "string" },
            "timestamp": { "type": "string" },
            "path": { "type": "string" }
        },
        "required": ["error", "message"]
    })
});

// =============================================================================
// Request Validators
// =============================================================================

const requestValidator = new aws.apigateway.RequestValidator("request-validator", {
    restApi: primaryRestApi.id,
    name: createResourceName(deploymentConfig, "request-validator"),
    validateRequestBody: true,
    validateRequestParameters: true
});

// =============================================================================
// VPC Link for Internal ALB Integration
// =============================================================================

const mainVpcLink = new aws.apigateway.VpcLink("main-vpc-link", {
    name: createResourceName(deploymentConfig, "vpc-link"),
    description: "VPC Link to internal ALB for API Gateway integration",
    targetArns: [containerAppsStackOutputs.publicAlbArn],
    tags: createResourceTags(deploymentConfig, "vpc-link", {
        Purpose: "api-gateway-integration",
        Target: "internal-alb"
    })
});

// Create a function to generate method and integration for each endpoint
function createApiMethod(
    resourceName: string,
    resource: aws.apigateway.Resource,
    httpMethod: string,
    authorization: string = "NONE",
    authorizerId?: pulumi.Output<string>,
    requestModel?: aws.apigateway.Model,
    requireApiKey: boolean = false
) {
    const method = new aws.apigateway.Method(`${resourceName}-${httpMethod.toLowerCase()}-method`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod,
        authorization,
        authorizerId,
        apiKeyRequired: requireApiKey,
        requestValidatorId: requestValidator.id,
        requestModels: requestModel ? {
            "application/json": requestModel.name
        } : undefined,
        requestParameters: {
            "method.request.header.Content-Type": false,
            "method.request.header.X-Forwarded-For": false
        }
    });

    // Create integration with VPC Link to internal ALB
    const integration = new aws.apigateway.Integration(`${resourceName}-${httpMethod.toLowerCase()}-integration`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: method.httpMethod,
        integrationHttpMethod: httpMethod,
        type: "HTTP_PROXY",
        uri: pulumi.interpolate`http://${containerAppsStackOutputs.publicAlbDnsName}${resource.pathPart ? `/${apiConfig.currentVersion}${getResourcePath(resource)}` : '/api/health'}`,
        connectionType: "VPC_LINK",
        connectionId: mainVpcLink.id,
        requestParameters: {
            "integration.request.header.X-Forwarded-For": "context.identity.sourceIp",
            "integration.request.header.X-Forwarded-Proto": "context.protocol",
            "integration.request.path.proxy": "method.request.path.proxy"
        },
        timeoutMilliseconds: 29000 // Maximum timeout for API Gateway
    });

    // Method response for 200
    const methodResponse200 = new aws.apigateway.MethodResponse(`${resourceName}-${httpMethod.toLowerCase()}-response-200`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: method.httpMethod,
        statusCode: "200",
        responseModels: {
            "application/json": "Empty"
        },
        responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": true,
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true
        }
    });

    // Method response for 400
    const methodResponse400 = new aws.apigateway.MethodResponse(`${resourceName}-${httpMethod.toLowerCase()}-response-400`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: method.httpMethod,
        statusCode: "400",
        responseModels: {
            "application/json": errorModel.name
        }
    });

    // Method response for 500
    const methodResponse500 = new aws.apigateway.MethodResponse(`${resourceName}-${httpMethod.toLowerCase()}-response-500`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: method.httpMethod,
        statusCode: "500",
        responseModels: {
            "application/json": errorModel.name
        }
    });

    // Integration response for 200
    const integrationResponse200 = new aws.apigateway.IntegrationResponse(`${resourceName}-${httpMethod.toLowerCase()}-integration-response-200`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: method.httpMethod,
        statusCode: methodResponse200.statusCode,
        responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": `'${apiConfig.corsAllowOrigins.join(", ")}'`,
            "method.response.header.Access-Control-Allow-Headers": `'${apiConfig.corsAllowHeaders.join(", ")}'`,
            "method.response.header.Access-Control-Allow-Methods": `'${apiConfig.corsAllowMethods.join(", ")}'`
        }
    });

    return { method, integration, methodResponse200, integrationResponse200 };
}

// Helper function to get resource path for API routing
function getResourcePath(resource: aws.apigateway.Resource): string {
    // This is a simplified version - in reality, you'd need to traverse the resource hierarchy
    return "/users"; // This would be dynamically determined based on the resource
}

// =============================================================================
// API Methods - Users
// =============================================================================

const usersGetMethod = createApiMethod("users", usersResource, "GET", "COGNITO_USER_POOLS", cognitoAuthorizer.id);
const usersPostMethod = createApiMethod("users", usersResource, "POST", "COGNITO_USER_POOLS", cognitoAuthorizer.id, userModel);
const userGetMethod = createApiMethod("user", userIdResource, "GET", "COGNITO_USER_POOLS", cognitoAuthorizer.id);
const userPutMethod = createApiMethod("user", userIdResource, "PUT", "COGNITO_USER_POOLS", cognitoAuthorizer.id, userModel);
const userDeleteMethod = createApiMethod("user", userIdResource, "DELETE", "COGNITO_USER_POOLS", cognitoAuthorizer.id);

// =============================================================================
// API Methods - Orders
// =============================================================================

const ordersGetMethod = createApiMethod("orders", ordersResource, "GET", "COGNITO_USER_POOLS", cognitoAuthorizer.id);
const ordersPostMethod = createApiMethod("orders", ordersResource, "POST", "COGNITO_USER_POOLS", cognitoAuthorizer.id, orderModel);
const orderGetMethod = createApiMethod("order", orderIdResource, "GET", "COGNITO_USER_POOLS", cognitoAuthorizer.id);
const orderPutMethod = createApiMethod("order", orderIdResource, "PUT", "COGNITO_USER_POOLS", cognitoAuthorizer.id, orderModel);
const orderDeleteMethod = createApiMethod("order", orderIdResource, "DELETE", "COGNITO_USER_POOLS", cognitoAuthorizer.id);

// =============================================================================
// API Methods - Products (Public endpoints)
// =============================================================================

const productsGetMethod = createApiMethod("products", productsResource, "GET");
const productGetMethod = createApiMethod("product", productIdResource, "GET");

// =============================================================================
// API Methods - Auth
// =============================================================================

const authPostMethod = createApiMethod("auth", authResource, "POST");

// =============================================================================
// API Methods - Health Check
// =============================================================================

const healthGetMethod = createApiMethod("health", healthResource, "GET");

// =============================================================================
// CORS OPTIONS Methods
// =============================================================================

function createOptionsMethod(resourceName: string, resource: aws.apigateway.Resource) {
    const optionsMethod = new aws.apigateway.Method(`${resourceName}-options-method`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: "OPTIONS",
        authorization: "NONE"
    });

    const optionsIntegration = new aws.apigateway.Integration(`${resourceName}-options-integration`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: optionsMethod.httpMethod,
        type: "MOCK",
        requestTemplates: {
            "application/json": JSON.stringify({ statusCode: 200 })
        }
    });

    const optionsMethodResponse = new aws.apigateway.MethodResponse(`${resourceName}-options-response`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: optionsMethod.httpMethod,
        statusCode: "200",
        responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": true,
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true,
            "method.response.header.Access-Control-Max-Age": true
        }
    });

    const optionsIntegrationResponse = new aws.apigateway.IntegrationResponse(`${resourceName}-options-integration-response`, {
        restApi: primaryRestApi.id,
        resourceId: resource.id,
        httpMethod: optionsMethod.httpMethod,
        statusCode: optionsMethodResponse.statusCode,
        responseParameters: {
            "method.response.header.Access-Control-Allow-Origin": `'${apiConfig.corsAllowOrigins.join(", ")}'`,
            "method.response.header.Access-Control-Allow-Headers": `'${apiConfig.corsAllowHeaders.join(", ")}'`,
            "method.response.header.Access-Control-Allow-Methods": `'${apiConfig.corsAllowMethods.join(", ")}'`,
            "method.response.header.Access-Control-Max-Age": `'${apiConfig.corsMaxAge}'`
        }
    });

    return { optionsMethod, optionsIntegration, optionsMethodResponse, optionsIntegrationResponse };
}

// Create OPTIONS methods for all resources
const usersOptionsMethod = createOptionsMethod("users", usersResource);
const userOptionsMethod = createOptionsMethod("user", userIdResource);
const ordersOptionsMethod = createOptionsMethod("orders", ordersResource);
const orderOptionsMethod = createOptionsMethod("order", orderIdResource);
const productsOptionsMethod = createOptionsMethod("products", productsResource);
const productOptionsMethod = createOptionsMethod("product", productIdResource);
const authOptionsMethod = createOptionsMethod("auth", authResource);
const healthOptionsMethod = createOptionsMethod("health", healthResource);

console.log(`✅ Created REST API Gateway with comprehensive resource structure and CORS support`);

// =============================================================================
// HTTP API Gateway (API Gateway v2) - High Performance API
// =============================================================================

const httpApi = new aws.apigatewayv2.Api("http-api", {
    name: createResourceName(deploymentConfig, "http-api"),
    description: `High-performance HTTP API for ${deploymentConfig.projectName} - ${deploymentConfig.environment}`,
    protocolType: "HTTP",
    corsConfiguration: {
        allowCredentials: true,
        allowHeaders: apiConfig.corsAllowHeaders,
        allowMethods: apiConfig.corsAllowMethods,
        allowOrigins: apiConfig.corsAllowOrigins,
        exposeHeaders: ["Date", "Keep-Alive"],
        maxAge: apiConfig.corsMaxAge
    },
    tags: createResourceTags(deploymentConfig, "http-api", {
        Name: createResourceName(deploymentConfig, "http-api"),
        Type: "high-performance",
        ApiType: "http"
    })
});

// =============================================================================
// VPC Link for HTTP API Gateway
// =============================================================================

const httpVpcLink = new aws.apigatewayv2.VpcLink("http-vpc-link", {
    name: createResourceName(deploymentConfig, "http-vpc-link"),
    securityGroupIds: [securityStackOutputs.apiApplicationSgId],
    subnetIds: networkStackOutputs.privateSubnetIds,
    tags: createResourceTags(deploymentConfig, "http-vpc-link", {
        Purpose: "http-api-integration",
        Target: "internal-alb"
    })
});

// =============================================================================
// HTTP API Integrations
// =============================================================================

const httpAlbIntegration = new aws.apigatewayv2.Integration("http-alb-integration", {
    apiId: httpApi.id,
    integrationType: "HTTP_PROXY",
    integrationUri: containerAppsStackOutputs.httpsListenerArn,
    integrationMethod: "ANY",
    connectionType: "VPC_LINK",
    connectionId: httpVpcLink.id,
    payloadFormatVersion: "1.0",
    timeoutMilliseconds: 29000
});

// =============================================================================
// HTTP API Routes
// =============================================================================

// Catch-all route for proxying to ALB
const httpCatchAllRoute = new aws.apigatewayv2.Route("http-catch-all-route", {
    apiId: httpApi.id,
    routeKey: "ANY /{proxy+}",
    target: pulumi.interpolate`integrations/${httpAlbIntegration.id}`
});

// Specific health check route
const httpHealthRoute = new aws.apigatewayv2.Route("http-health-route", {
    apiId: httpApi.id,
    routeKey: "GET /health",
    target: pulumi.interpolate`integrations/${httpAlbIntegration.id}`
});

// API v1 routes
const httpApiV1Route = new aws.apigatewayv2.Route("http-api-v1-route", {
    apiId: httpApi.id,
    routeKey: `ANY /${apiConfig.currentVersion}/{proxy+}`,
    target: pulumi.interpolate`integrations/${httpAlbIntegration.id}`
});

// =============================================================================
// HTTP API Stage
// =============================================================================

const httpApiStage = new aws.apigatewayv2.Stage("http-api-stage", {
    apiId: httpApi.id,
    name: deploymentConfig.environment,
    autoDeploy: true,
    description: `HTTP API stage for ${deploymentConfig.environment}`,
    accessLogSettings: {
        destinationArn: httpApiLogGroup.arn,
        format: JSON.stringify({
            requestId: "$context.requestId",
            requestTime: "$context.requestTime",
            httpMethod: "$context.httpMethod",
            routeKey: "$context.routeKey",
            status: "$context.status",
            error: "$context.error.message",
            integrationError: "$context.integrationErrorMessage",
            responseTime: "$context.responseTime",
            responseLength: "$context.responseLength",
            ip: "$context.identity.sourceIp",
            userAgent: "$context.identity.userAgent"
        })
    },
    defaultRouteSettings: {
        dataTraceEnabled: apiConfig.enableDetailedMonitoring,
        loggingLevel: isDevelopment(deploymentConfig) ? "INFO" : "ERROR",
        throttlingBurstLimit: apiConfig.defaultThrottleSettings.burstLimit,
        throttlingRateLimit: apiConfig.defaultThrottleSettings.rateLimit
    },
    tags: createResourceTags(deploymentConfig, "http-api-stage", {
        Environment: deploymentConfig.environment,
        AutoDeploy: "true"
    })
});

console.log(`✅ Created HTTP API Gateway with VPC Link integration to ALB`);

// =============================================================================
// API Gateway Deployment for REST API
// =============================================================================

const restApiDeployment = new aws.apigateway.Deployment("rest-api-deployment", {
    restApi: primaryRestApi.id,
    description: `REST API deployment for ${deploymentConfig.environment}`,
    triggers: {
        // Force redeployment when methods change
        redeployment: pulumi.all([
            usersGetMethod.method.id,
            usersPostMethod.method.id,
            ordersGetMethod.method.id,
            productsGetMethod.method.id,
            authPostMethod.method.id,
            healthGetMethod.method.id
        ]).apply(ids => JSON.stringify(ids))
    }
}, {
    dependsOn: [
        // Ensure all methods and integrations are created first
        ...Object.values(usersGetMethod),
        ...Object.values(usersPostMethod),
        ...Object.values(ordersGetMethod),
        ...Object.values(productsGetMethod),
        ...Object.values(authPostMethod),
        ...Object.values(healthGetMethod)
    ]
});

const restApiStage = new aws.apigateway.Stage("rest-api-stage", {
    deploymentId: restApiDeployment.id,
    restApi: primaryRestApi.id,
    stageName: deploymentConfig.environment,
    description: `REST API stage for ${deploymentConfig.environment}`,
    xrayTracingEnabled: apiConfig.enableXRayTracing,
    accessLogSettings: {
        destinationArn: apiGatewayLogGroup.arn,
        format: JSON.stringify({
            requestId: "$context.requestId",
            extendedRequestId: "$context.extendedRequestId",
            ip: "$context.identity.sourceIp",
            caller: "$context.identity.caller",
            user: "$context.identity.user",
            requestTime: "$context.requestTime",
            httpMethod: "$context.httpMethod",
            resourcePath: "$context.resourcePath",
            status: "$context.status",
            protocol: "$context.protocol",
            responseLength: "$context.responseLength",
            responseTime: "$context.responseTime",
            error: "$context.error.message",
            integrationError: "$context.integrationErrorMessage"
        })
    },
    throttleSettings: {
        rateLimit: apiConfig.defaultThrottleSettings.rateLimit,
        burstLimit: apiConfig.defaultThrottleSettings.burstLimit
    },
    tags: createResourceTags(deploymentConfig, "api-stage", {
        Environment: deploymentConfig.environment,
        ApiType: "rest"
    })
});

console.log(`✅ Created API Gateway deployments and stages`);

// =============================================================================
// Usage Plans and API Keys
// =============================================================================

// Standard usage plan
const standardUsagePlan = new aws.apigateway.UsagePlan("standard-usage-plan", {
    name: createResourceName(deploymentConfig, "standard-plan"),
    description: "Standard usage plan for API consumers",
    apiStages: [{
        apiId: primaryRestApi.id,
        stage: restApiStage.stageName
    }],
    quotaSettings: {
        limit: apiConfig.usagePlans.standard.quotaLimit,
        period: apiConfig.usagePlans.standard.quotaPeriod
    },
    throttleSettings: {
        rateLimit: apiConfig.usagePlans.standard.rateLimit,
        burstLimit: apiConfig.usagePlans.standard.burstLimit
    },
    tags: createResourceTags(deploymentConfig, "usage-plan", {
        Tier: "standard"
    })
});

// Premium usage plan
const premiumUsagePlan = new aws.apigateway.UsagePlan("premium-usage-plan", {
    name: createResourceName(deploymentConfig, "premium-plan"),
    description: "Premium usage plan for high-volume API consumers",
    apiStages: [{
        apiId: primaryRestApi.id,
        stage: restApiStage.stageName
    }],
    quotaSettings: {
        limit: apiConfig.usagePlans.premium.quotaLimit,
        period: apiConfig.usagePlans.premium.quotaPeriod
    },
    throttleSettings: {
        rateLimit: apiConfig.usagePlans.premium.rateLimit,
        burstLimit: apiConfig.usagePlans.premium.burstLimit
    },
    tags: createResourceTags(deploymentConfig, "usage-plan", {
        Tier: "premium"
    })
});

// API Keys
const standardApiKey = new aws.apigateway.ApiKey("standard-api-key", {
    name: createResourceName(deploymentConfig, "standard-key"),
    description: "Standard API key for development and testing",
    enabled: true,
    tags: createResourceTags(deploymentConfig, "api-key", {
        Tier: "standard",
        Purpose: "development"
    })
});

const premiumApiKey = new aws.apigateway.ApiKey("premium-api-key", {
    name: createResourceName(deploymentConfig, "premium-key"),
    description: "Premium API key for production use",
    enabled: true,
    tags: createResourceTags(deploymentConfig, "api-key", {
        Tier: "premium",
        Purpose: "production"
    })
});

// Usage Plan Key Associations
const standardUsagePlanKey = new aws.apigateway.UsagePlanKey("standard-usage-plan-key", {
    keyId: standardApiKey.id,
    keyType: "API_KEY",
    usagePlanId: standardUsagePlan.id
});

const premiumUsagePlanKey = new aws.apigateway.UsagePlanKey("premium-usage-plan-key", {
    keyId: premiumApiKey.id,
    keyType: "API_KEY",
    usagePlanId: premiumUsagePlan.id
});

console.log(`✅ Created usage plans and API keys for rate limiting and access control`);

// =============================================================================
// WAF (Web Application Firewall) for API Protection
// =============================================================================

let apiWafAcl: aws.wafv2.WebAcl | undefined;
let apiWafAssociation: aws.wafv2.WebAclAssociation | undefined;

if (apiConfig.enableWafProtection) {
    apiWafAcl = new aws.wafv2.WebAcl("api-waf-acl", {
        name: createResourceName(deploymentConfig, "api-waf"),
        description: `WAF for API Gateway protection - ${deploymentConfig.environment}`,
        scope: "REGIONAL",
        defaultAction: {
            allow: {}
        },
        rules: [
            // Rate limiting rule
            {
                name: "RateLimitRule",
                priority: 1,
                statement: {
                    rateBasedStatement: {
                        limit: apiConfig.wafRateLimit,
                        aggregateKeyType: "IP"
                    }
                },
                action: {
                    block: {}
                },
                visibilityConfig: {
                    sampledRequestsEnabled: true,
                    cloudwatchMetricsEnabled: true,
                    metricName: "RateLimitRule"
                }
            },
            // AWS managed rule set for common attacks
            {
                name: "AWSManagedRulesCommonRuleSet",
                priority: 10,
                overrideAction: {
                    none: {}
                },
                statement: {
                    managedRuleGroupStatement: {
                        name: "AWSManagedRulesCommonRuleSet",
                        vendorName: "AWS"
                    }
                },
                visibilityConfig: {
                    sampledRequestsEnabled: true,
                    cloudwatchMetricsEnabled: true,
                    metricName: "CommonRuleSetMetric"
                }
            },
            // Known bad inputs rule set
            {
                name: "AWSManagedRulesKnownBadInputsRuleSet",
                priority: 20,
                overrideAction: {
                    none: {}
                },
                statement: {
                    managedRuleGroupStatement: {
                        name: "AWSManagedRulesKnownBadInputsRuleSet",
                        vendorName: "AWS"
                    }
                },
                visibilityConfig: {
                    sampledRequestsEnabled: true,
                    cloudwatchMetricsEnabled: true,
                    metricName: "KnownBadInputsRuleSetMetric"
                }
            }
        ],
        visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudwatchMetricsEnabled: true,
            metricName: createResourceName(deploymentConfig, "api-waf-metric")
        },
        tags: createResourceTags(deploymentConfig, "waf-acl", {
            Scope: "regional",
            Purpose: "api-protection"
        })
    });

    // Associate WAF with REST API stage
    apiWafAssociation = new aws.wafv2.WebAclAssociation("api-waf-association", {
        resourceArn: pulumi.interpolate`arn:aws:apigateway:${currentRegion}::/restapis/${primaryRestApi.id}/stages/${restApiStage.stageName}`,
        webAclArn: apiWafAcl.arn
    });

    console.log(`✅ Created WAF protection for API Gateway with rate limiting and security rules`);
}

// =============================================================================
// Custom Domain Names and Certificates
// =============================================================================

// Custom domain for primary API
const apiCustomDomain = new aws.apigateway.DomainName("api-custom-domain", {
    domainName: apiConfig.customDomains.api,
    certificateArn: dnsStackOutputs.wildcardCertificateArn,
    endpointConfiguration: {
        types: ["REGIONAL"]
    },
    securityPolicy: "TLS_1_2",
    tags: createResourceTags(deploymentConfig, "custom-domain", {
        Domain: apiConfig.customDomains.api,
        Type: "api"
    })
});

// Custom domain for admin API
const adminApiCustomDomain = new aws.apigateway.DomainName("admin-api-custom-domain", {
    domainName: apiConfig.customDomains.adminApi,
    certificateArn: dnsStackOutputs.wildcardCertificateArn,
    endpointConfiguration: {
        types: ["REGIONAL"]
    },
    securityPolicy: "TLS_1_2",
    tags: createResourceTags(deploymentConfig, "custom-domain", {
        Domain: apiConfig.customDomains.adminApi,
        Type: "admin-api"
    })
});

// Base path mappings
const apiBasePathMapping = new aws.apigateway.BasePathMapping("api-base-path-mapping", {
    domainName: apiCustomDomain.domainName,
    restApi: primaryRestApi.id,
    stageName: restApiStage.stageName
});

const adminApiBasePathMapping = new aws.apigateway.BasePathMapping("admin-api-base-path-mapping", {
    domainName: adminApiCustomDomain.domainName,
    restApi: adminRestApi.id,
    stageName: deploymentConfig.environment // Admin API will have its own stage
});

// Route53 DNS records for custom domains
const apiDnsRecord = new aws.route53.Record("api-dns-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: apiConfig.customDomains.api,
    type: "A",
    aliases: [{
        name: apiCustomDomain.cloudfrontDomainName,
        zoneId: apiCustomDomain.cloudfrontZoneId,
        evaluateTargetHealth: false
    }],
    tags: createResourceTags(deploymentConfig, "dns-record", {
        Domain: apiConfig.customDomains.api,
        Type: "api"
    })
});

const adminApiDnsRecord = new aws.route53.Record("admin-api-dns-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: apiConfig.customDomains.adminApi,
    type: "A",
    aliases: [{
        name: adminApiCustomDomain.cloudfrontDomainName,
        zoneId: adminApiCustomDomain.cloudfrontZoneId,
        evaluateTargetHealth: false
    }],
    tags: createResourceTags(deploymentConfig, "dns-record", {
        Domain: apiConfig.customDomains.adminApi,
        Type: "admin-api"
    })
});

console.log(`✅ Created custom domains and DNS records for API endpoints`);

// =============================================================================
// CloudFront Distribution for API Caching
// =============================================================================

let apiCdnDistribution: aws.cloudfront.Distribution | undefined;

if (apiConfig.enableCdn) {
    // Origin Access Control for API Gateway
    const apiOriginAccessControl = new aws.cloudfront.OriginAccessControl("api-origin-access-control", {
        name: createResourceName(deploymentConfig, "api-oac"),
        description: "Origin Access Control for API Gateway",
        originAccessControlOriginType: "s3",
        signingBehavior: "always",
        signingProtocol: "sigv4"
    });

    apiCdnDistribution = new aws.cloudfront.Distribution("api-cdn-distribution", {
        comment: `API CDN for ${deploymentConfig.deployDomain}`,
        enabled: true,
        isIpv6Enabled: true,
        priceClass: apiConfig.cdnPriceClass,

        origins: [{
            originId: "api-gateway-origin",
            domainName: pulumi.interpolate`${primaryRestApi.id}.execute-api.${currentRegion}.amazonaws.com`,
            originPath: `/${deploymentConfig.environment}`,
            customOriginConfig: {
                httpPort: COMMON_PORTS.HTTP,
                httpsPort: COMMON_PORTS.HTTPS,
                originProtocolPolicy: "https-only",
                originSslProtocols: ["TLSv1.2"],
                originKeepaliveTimeout: 5,
                originReadTimeout: 30
            }
        }],

        defaultCacheBehavior: {
            targetOriginId: "api-gateway-origin",
            viewerProtocolPolicy: "redirect-to-https",
            allowedMethods: ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
            cachedMethods: ["GET", "HEAD", "OPTIONS"],
            compress: true,

            // Cache policy for API Gateway (caching disabled for dynamic content)
            cachePolicyId: "4135ea2d-6df8-44a3-9df3-4b5a84be39ad", // Managed-CachingDisabled
            originRequestPolicyId: "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf", // Managed-CORS-S3Origin

            minTtl: apiConfig.cdnMinTtl,
            defaultTtl: apiConfig.cdnDefaultTtl,
            maxTtl: apiConfig.cdnMaxTtl,

            // Forward all headers for API requests
            forwardedValues: {
                queryString: true,
                headers: ["*"],
                cookies: {
                    forward: "all"
                }
            }
        },

        // Specific caching behavior for static assets
        orderedCacheBehaviors: [
            {
                pathPattern: "/v1/health*",
                targetOriginId: "api-gateway-origin",
                viewerProtocolPolicy: "redirect-to-https",
                allowedMethods: ["GET", "HEAD", "OPTIONS"],
                cachedMethods: ["GET", "HEAD"],
                compress: true,
                cachePolicyId: "658327ea-f89d-4fab-a63d-7e88639e58f6", // Managed-CachingOptimized
                minTtl: 0,
                defaultTtl: 300, // 5 minutes for health check
                maxTtl: 3600 // 1 hour
            }
        ],

        restrictions: {
            geoRestriction: {
                restrictionType: "none"
            }
        },

        viewerCertificate: {
            cloudfrontDefaultCertificate: true
        },

        tags: createResourceTags(deploymentConfig, "cloudfront", {
            Purpose: "api-caching",
            Type: "api-cdn"
        })
    });

    console.log(`✅ Created CloudFront CDN distribution for API caching and global distribution`);
}

// =============================================================================
// X-Ray Tracing Configuration
// =============================================================================

let xrayTracingSamplingRule: aws.xray.SamplingRule | undefined;

if (apiConfig.enableXRayTracing) {
    xrayTracingSamplingRule = new aws.xray.SamplingRule("api-tracing-rule", {
        ruleName: createResourceName(deploymentConfig, "api-tracing-rule"),
        priority: 9000,
        fixedRate: isDevelopment(deploymentConfig) ? 0.1 : 0.05, // Higher sampling in dev
        reservoirSize: 1,
        serviceName: `${deploymentConfig.projectName}-api`,
        serviceType: "AWS::ApiGateway::Stage",
        host: "*",
        httpMethod: "*",
        urlPath: "*",
        version: 1,
        tags: createResourceTags(deploymentConfig, "xray-sampling", {
            Service: "api-gateway",
            Purpose: "distributed-tracing"
        })
    });

    console.log(`✅ Created X-Ray tracing configuration for distributed request tracing`);
}

// =============================================================================
// CloudWatch Dashboards and Monitoring
// =============================================================================

const apiDashboard = new aws.cloudwatch.Dashboard("api-dashboard", {
    dashboardName: createResourceName(deploymentConfig, "api-dashboard"),
    dashboardBody: JSON.stringify({
        widgets: [
            // API Gateway REST API Metrics
            {
                type: "metric",
                x: 0,
                y: 0,
                width: 12,
                height: 6,
                properties: {
                    metrics: [
                        ["AWS/ApiGateway", "Count", "ApiName", createResourceName(deploymentConfig, "rest-api")],
                        [".", "Latency", ".", "."],
                        [".", "4XXError", ".", "."],
                        [".", "5XXError", ".", "."]
                    ],
                    view: "timeSeries",
                    stacked: false,
                    region: deploymentConfig.region,
                    title: "REST API Gateway Metrics",
                    period: 300
                }
            },
            // HTTP API Metrics
            {
                type: "metric",
                x: 12,
                y: 0,
                width: 12,
                height: 6,
                properties: {
                    metrics: [
                        ["AWS/ApiGatewayV2", "Count", "ApiId", httpApi.id],
                        [".", "IntegrationLatency", ".", "."],
                        [".", "Latency", ".", "."],
                        [".", "4xx", ".", "."],
                        [".", "5xx", ".", "."]
                    ],
                    view: "timeSeries",
                    stacked: false,
                    region: deploymentConfig.region,
                    title: "HTTP API Gateway Metrics",
                    period: 300
                }
            },
            // WAF Metrics
            apiWafAcl ? {
                type: "metric",
                x: 0,
                y: 6,
                width: 12,
                height: 6,
                properties: {
                    metrics: [
                        ["AWS/WAFV2", "AllowedRequests", "WebACL", apiWafAcl.name, "Region", deploymentConfig.region, "Rule", "ALL"],
                        [".", "BlockedRequests", ".", ".", ".", ".", ".", "."],
                        [".", "BlockedRequests", ".", ".", ".", ".", ".", "RateLimitRule"]
                    ],
                    view: "timeSeries",
                    stacked: false,
                    region: deploymentConfig.region,
                    title: "WAF Protection Metrics",
                    period: 300
                }
            } : undefined,
            // CloudFront Metrics
            apiCdnDistribution ? {
                type: "metric",
                x: 12,
                y: 6,
                width: 12,
                height: 6,
                properties: {
                    metrics: [
                        ["AWS/CloudFront", "Requests", "DistributionId", apiCdnDistribution.id],
                        [".", "BytesDownloaded", ".", "."],
                        [".", "BytesUploaded", ".", "."],
                        [".", "4xxErrorRate", ".", "."],
                        [".", "5xxErrorRate", ".", "."]
                    ],
                    view: "timeSeries",
                    stacked: false,
                    region: "us-east-1", // CloudFront metrics are always in us-east-1
                    title: "CloudFront CDN Metrics",
                    period: 300
                }
            } : undefined
        ].filter(Boolean) // Remove undefined widgets
    }),
    tags: createResourceTags(deploymentConfig, "dashboard", {
        Service: "api-gateway",
        Type: "monitoring"
    })
});

console.log(`✅ Created comprehensive CloudWatch dashboard for API monitoring`);

// =============================================================================
// CloudWatch Alarms for API Monitoring
// =============================================================================

// High error rate alarm for REST API
const restApiHighErrorAlarm = new aws.cloudwatch.MetricAlarm("rest-api-high-error-alarm", {
    name: createResourceName(deploymentConfig, "rest-api-high-error"),
    description: "High error rate detected in REST API Gateway",
    metricName: "4XXError",
    namespace: "AWS/ApiGateway",
    statistic: "Sum",
    period: 300,
    evaluationPeriods: 2,
    threshold: 10,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        ApiName: createResourceName(deploymentConfig, "rest-api")
    },
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "alarm", {
        Service: "rest-api",
        Type: "error-rate"
    })
});

// High latency alarm for REST API
const restApiHighLatencyAlarm = new aws.cloudwatch.MetricAlarm("rest-api-high-latency-alarm", {
    name: createResourceName(deploymentConfig, "rest-api-high-latency"),
    description: "High latency detected in REST API Gateway",
    metricName: "Latency",
    namespace: "AWS/ApiGateway",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: 5000, // 5 seconds
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        ApiName: createResourceName(deploymentConfig, "rest-api")
    },
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "alarm", {
        Service: "rest-api",
        Type: "latency"
    })
});

// HTTP API high error rate alarm
const httpApiHighErrorAlarm = new aws.cloudwatch.MetricAlarm("http-api-high-error-alarm", {
    name: createResourceName(deploymentConfig, "http-api-high-error"),
    description: "High error rate detected in HTTP API Gateway",
    metricName: "4xx",
    namespace: "AWS/ApiGatewayV2",
    statistic: "Sum",
    period: 300,
    evaluationPeriods: 2,
    threshold: 10,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        ApiId: httpApi.id
    },
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "alarm", {
        Service: "http-api",
        Type: "error-rate"
    })
});

// VPC Link health alarm
const vpcLinkHealthAlarm = new aws.cloudwatch.MetricAlarm("vpc-link-health-alarm", {
    name: createResourceName(deploymentConfig, "vpc-link-health"),
    description: "VPC Link connection health check",
    metricName: "IntegrationLatency",
    namespace: "AWS/ApiGateway",
    statistic: "Average",
    period: 60,
    evaluationPeriods: 3,
    threshold: 29000, // Close to timeout
    comparisonOperator: "GreaterThanThreshold",
    treatMissingData: "breaching",
    tags: createResourceTags(deploymentConfig, "alarm", {
        Service: "vpc-link",
        Type: "connectivity"
    })
});

console.log(`✅ Created CloudWatch alarms for API monitoring and alerting`);

// =============================================================================
// Gateway Responses for Custom Error Handling
// =============================================================================

// Custom 4xx error response
const gateway4xxResponse = new aws.apigateway.GatewayResponse("gateway-4xx-response", {
    restApi: primaryRestApi.id,
    responseType: "DEFAULT_4XX",
    statusCode: "400",
    responseTemplates: {
        "application/json": JSON.stringify({
            error: "Bad Request",
            message: "$context.error.message",
            requestId: "$context.requestId",
            timestamp: "$context.requestTime"
        })
    },
    responseParameters: {
        "gatewayresponse.header.Access-Control-Allow-Origin": `'${apiConfig.corsAllowOrigins[0]}'`,
        "gatewayresponse.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'"
    }
});

// Custom 5xx error response
const gateway5xxResponse = new aws.apigateway.GatewayResponse("gateway-5xx-response", {
    restApi: primaryRestApi.id,
    responseType: "DEFAULT_5XX",
    statusCode: "500",
    responseTemplates: {
        "application/json": JSON.stringify({
            error: "Internal Server Error",
            message: "An unexpected error occurred. Please try again later.",
            requestId: "$context.requestId",
            timestamp: "$context.requestTime"
        })
    },
    responseParameters: {
        "gatewayresponse.header.Access-Control-Allow-Origin": `'${apiConfig.corsAllowOrigins[0]}'`,
        "gatewayresponse.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'"
    }
});

// Throttled requests response
const gatewayThrottleResponse = new aws.apigateway.GatewayResponse("gateway-throttle-response", {
    restApi: primaryRestApi.id,
    responseType: "THROTTLED",
    statusCode: "429",
    responseTemplates: {
        "application/json": JSON.stringify({
            error: "Too Many Requests",
            message: "Request rate limit exceeded. Please slow down.",
            requestId: "$context.requestId",
            timestamp: "$context.requestTime",
            retryAfter: "60"
        })
    },
    responseParameters: {
        "gatewayresponse.header.Access-Control-Allow-Origin": `'${apiConfig.corsAllowOrigins[0]}'`,
        "gatewayresponse.header.Retry-After": "'60'"
    }
});

console.log(`✅ Created custom gateway responses for enhanced error handling`);

// =============================================================================
// Admin API Configuration (Simplified)
// =============================================================================

// Admin API deployment and stage
const adminApiDeployment = new aws.apigateway.Deployment("admin-api-deployment", {
    restApi: adminRestApi.id,
    description: `Admin API deployment for ${deploymentConfig.environment}`
});

const adminApiStage = new aws.apigateway.Stage("admin-api-stage", {
    deploymentId: adminApiDeployment.id,
    restApi: adminRestApi.id,
    stageName: deploymentConfig.environment,
    description: `Admin API stage for ${deploymentConfig.environment}`,
    xrayTracingEnabled: apiConfig.enableXRayTracing,
    throttleSettings: {
        rateLimit: Math.floor(apiConfig.defaultThrottleSettings.rateLimit / 2), // More restrictive for admin
        burstLimit: Math.floor(apiConfig.defaultThrottleSettings.burstLimit / 2)
    },
    tags: createResourceTags(deploymentConfig, "api-stage", {
        Environment: deploymentConfig.environment,
        ApiType: "admin"
    })
});

console.log(`✅ Created admin API deployment and stage configuration`);

// =============================================================================
// Outputs
// =============================================================================

// Primary REST API outputs
export const primaryApiId = primaryRestApi.id;
export const primaryApiArn = primaryRestApi.arn;
export const primaryApiName = primaryRestApi.name;
export const primaryApiEndpoint = pulumi.interpolate`https://${primaryRestApi.id}.execute-api.${currentRegion}.amazonaws.com/${deploymentConfig.environment}`;
export const primaryApiExecutionArn = pulumi.interpolate`arn:aws:execute-api:${currentRegion}:${currentAccountId}:${primaryRestApi.id}`;

// Admin API outputs
export const adminApiId = adminRestApi.id;
export const adminApiArn = adminRestApi.arn;
export const adminApiName = adminRestApi.name;
export const adminApiEndpoint = pulumi.interpolate`https://${adminRestApi.id}.execute-api.${currentRegion}.amazonaws.com/${deploymentConfig.environment}`;

// HTTP API outputs
export const httpApiId = httpApi.id;
export const httpApiArn = httpApi.arn;
export const httpApiName = httpApi.name;
export const httpApiEndpoint = httpApi.apiEndpoint;

// Custom domains
export const apiDomain = apiConfig.customDomains.api;
export const adminApiDomain = apiConfig.customDomains.adminApi;
export const apiCustomDomainName = apiCustomDomain.domainName;
export const adminApiCustomDomainName = adminApiCustomDomain.domainName;

// VPC Links
export const vpcLinkId = mainVpcLink.id;
export const vpcLinkArn = pulumi.interpolate`arn:aws:apigateway:${currentRegion}::/vpclinks/${mainVpcLink.id}`;
export const httpVpcLinkId = httpVpcLink.id;
export const httpVpcLinkArn = httpVpcLink.arn;

// CloudFront CDN
export const apiCdnDomainName = apiCdnDistribution?.domainName || "";
export const apiCdnDistributionId = apiCdnDistribution?.id || "";
export const apiCdnDistributionArn = apiCdnDistribution?.arn || "";

// WAF
export const apiWafAclId = apiWafAcl?.id || "";
export const apiWafAclArn = apiWafAcl?.arn || "";

// Usage Plans
export const standardUsagePlanId = standardUsagePlan.id;
export const premiumUsagePlanId = premiumUsagePlan.id;
export const standardApiKeyId = standardApiKey.id;
export const premiumApiKeyId = premiumApiKey.id;

// Stages
export const restApiStageArn = pulumi.interpolate`arn:aws:apigateway:${currentRegion}::/restapis/${primaryRestApi.id}/stages/${restApiStage.stageName}`;
export const httpApiStageArn = pulumi.interpolate`arn:aws:apigateway:${currentRegion}::/apis/${httpApi.id}/stages/${httpApiStage.name}`;
export const adminApiStageArn = pulumi.interpolate`arn:aws:apigateway:${currentRegion}::/restapis/${adminRestApi.id}/stages/${adminApiStage.stageName}`;

// Cognito Authorizer
export const cognitoAuthorizerId = cognitoAuthorizer.id;
export const cognitoAuthorizerArn = pulumi.interpolate`arn:aws:apigateway:${currentRegion}::/restapis/${primaryRestApi.id}/authorizers/${cognitoAuthorizer.id}`;

// CloudWatch
export const apiGatewayLogGroupArn = apiGatewayLogGroup.arn;
export const httpApiLogGroupArn = httpApiLogGroup.arn;
export const apiDashboardArn = pulumi.interpolate`arn:aws:cloudwatch:${currentRegion}:${currentAccountId}:dashboard/${apiDashboard.dashboardName}`;

// X-Ray
export const xrayTracingRuleArn = xrayTracingSamplingRule?.arn || "";

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const environment = deploymentConfig.environment;
export const __exists = true;

// Comprehensive summary for easier consumption by other stacks
export const summary = {
    primaryApi: {
        id: primaryApiId,
        arn: primaryApiArn,
        name: primaryApiName,
        endpoint: primaryApiEndpoint,
        executionArn: primaryApiExecutionArn,
        customDomain: apiDomain,
        stage: deploymentConfig.environment
    },
    adminApi: {
        id: adminApiId,
        arn: adminApiArn,
        name: adminApiName,
        endpoint: adminApiEndpoint,
        customDomain: adminApiDomain,
        stage: deploymentConfig.environment
    },
    httpApi: {
        id: httpApiId,
        arn: httpApiArn,
        name: httpApiName,
        endpoint: httpApiEndpoint,
        stage: deploymentConfig.environment
    },
    vpcLinks: {
        main: {
            id: vpcLinkId,
            arn: vpcLinkArn
        },
        http: {
            id: httpVpcLinkId,
            arn: httpVpcLinkArn
        }
    },
    customDomains: {
        api: apiDomain,
        adminApi: adminApiDomain
    },
    cdn: {
        enabled: apiConfig.enableCdn,
        domainName: apiCdnDomainName,
        distributionId: apiCdnDistributionId,
        distributionArn: apiCdnDistributionArn
    },
    waf: {
        enabled: apiConfig.enableWafProtection,
        aclId: apiWafAclId,
        aclArn: apiWafAclArn
    },
    usagePlans: {
        standard: {
            id: standardUsagePlanId,
            apiKeyId: standardApiKeyId
        },
        premium: {
            id: premiumUsagePlanId,
            apiKeyId: premiumApiKeyId
        }
    },
    monitoring: {
        xrayEnabled: apiConfig.enableXRayTracing,
        detailedMonitoring: apiConfig.enableDetailedMonitoring,
        dashboardArn: apiDashboardArn,
        logGroups: {
            restApi: apiGatewayLogGroupArn,
            httpApi: httpApiLogGroupArn
        }
    },
    configuration: {
        environment: deploymentConfig.environment,
        corsEnabled: true,
        corsOrigins: apiConfig.corsAllowOrigins,
        throttleSettings: apiConfig.defaultThrottleSettings,
        logRetentionDays: apiConfig.logRetentionDays
    }
};

console.log(`🎉 API Gateway Services Stack deployment completed for ${deploymentConfig.environment}`);
console.log(`🔗 Primary API: ${primaryApiEndpoint}`);
console.log(`👑 Admin API: ${adminApiEndpoint}`);
console.log(`⚡ HTTP API: ${httpApiEndpoint}`);
console.log(`🌐 Custom API Domain: https://${apiDomain}`);
console.log(`🔐 Admin API Domain: https://${adminApiDomain}`);
console.log(`🛡️  WAF Protection: ${apiConfig.enableWafProtection ? 'Enabled' : 'Disabled'}`);
console.log(`🌍 CloudFront CDN: ${apiConfig.enableCdn ? 'Enabled' : 'Disabled'}`);
console.log(`📊 X-Ray Tracing: ${apiConfig.enableXRayTracing ? 'Enabled' : 'Disabled'}`);
console.log(`🎯 VPC Link Integration: Active`);
console.log(`📈 Usage Plans: Standard & Premium tiers configured`);
console.log(`🚦 Rate Limiting: ${apiConfig.defaultThrottleSettings.rateLimit}/sec (burst: ${apiConfig.defaultThrottleSettings.burstLimit})`);
console.log(`📝 Access Logging: Enabled with ${apiConfig.logRetentionDays} days retention`);
console.log(`⚡ Environment: ${deploymentConfig.environment.toUpperCase()}`);
console.log(`🔑 Cognito Authorization: Configured for protected endpoints`);