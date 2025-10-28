# AWS Resources for Services API Stack

## API Gateway Resources
- **aws.apigateway.RestApi** - Primary REST API for application
- **aws.apigateway.RestApi** - Admin API for management operations
- **aws.apigateway.Resource** - API resources for different endpoints
- **aws.apigateway.Method** - HTTP methods (GET, POST, PUT, DELETE)
- **aws.apigateway.Integration** - Lambda integrations for API methods
- **aws.apigateway.Integration** - ALB integrations for containerized services
- **aws.apigateway.Deployment** - API deployments for different stages
- **aws.apigateway.Stage** - Development and production stages
- **aws.apigateway.RequestValidator** - Request validation configuration
- **aws.apigateway.Model** - Data models for request/response validation
- **aws.apigateway.GatewayResponse** - Custom error responses
- **aws.apigateway.UsagePlan** - API usage plans for rate limiting
- **aws.apigateway.UsagePlanKey** - Usage plan associations with API keys
- **aws.apigateway.ApiKey** - API keys for client authentication
- **aws.apigateway.Authorizer** - Cognito authorizer for authentication

## API Gateway V2 (HTTP API) Resources
- **aws.apigatewayv2.Api** - HTTP API for high-performance REST operations
- **aws.apigatewayv2.Stage** - HTTP API stages
- **aws.apigatewayv2.Route** - HTTP API routes
- **aws.apigatewayv2.Integration** - HTTP API integrations
- **aws.apigatewayv2.Authorizer** - JWT authorizer for HTTP API

## CloudFront Resources
- **aws.cloudfront.Distribution** - CDN distribution for API caching
- **aws.cloudfront.OriginAccessControl** - Origin access control for API Gateway

## Route53 Resources
- **aws.route53.Record** - DNS records for API endpoints (api.${DEPLOY_DOMAIN})
- **aws.route53.Record** - DNS records for admin API (admin-api.${DEPLOY_DOMAIN})

## WAF Resources
- **aws.wafv2.WebAcl** - Web Application Firewall for API protection
- **aws.wafv2.WebAclAssociation** - WAF association with API Gateway

## Lambda Resources (API Functions)
- **aws.lambda.Function** - Authentication functions
- **aws.lambda.Function** - Authorization functions
- **aws.lambda.Function** - Data validation functions
- **aws.lambda.Function** - Business logic functions
- **aws.lambda.Permission** - API Gateway invoke permissions

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - API Gateway access logs
- **aws.cloudwatch.LogGroup** - Lambda function logs
- **aws.cloudwatch.MetricAlarm** - API performance alarms
- **aws.cloudwatch.Dashboard** - API monitoring dashboard

## X-Ray Resources
- **aws.xray.SamplingRule** - Distributed tracing configuration

## Systems Manager Resources
- **aws.ssm.Parameter** - API configuration parameters
- **aws.ssm.Parameter** - API keys and secrets references

## Estimated Resource Count: 40 resources
## Estimated Monthly Cost: $20-100 (depending on API usage)

## Resource Dependencies
- Depends on: network, security, authentication, containers-apps
- Used by: compute-lambda, services-auth, services-webapp