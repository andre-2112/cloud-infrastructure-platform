# AWS Resources for Authentication Stack

## Cognito User Pool Resources
- **aws.cognito.UserPool** - Main user pool for application authentication
- **aws.cognito.UserPoolDomain** - Custom domain for Cognito hosted UI
- **aws.cognito.UserPoolClient** - Web application client
- **aws.cognito.UserPoolClient** - Mobile application client
- **aws.cognito.UserPoolClient** - Admin client for backend operations
- **aws.cognito.IdentityPool** - Identity pool for AWS resource access
- **aws.cognito.IdentityPoolRoleAttachment** - Role mapping for identity pool

## User Pool Configuration
- **aws.cognito.UserPoolPasswordPolicy** - Password complexity requirements
- **aws.cognito.UserPoolAccountRecoverySetting** - Account recovery methods
- **aws.cognito.UserPoolVerificationMessageTemplate** - Email/SMS verification templates
- **aws.cognito.UserPoolUICustomization** - Hosted UI customization
- **aws.cognito.UserPoolSchema** - Custom user attributes

## Identity Providers
- **aws.cognito.IdentityProvider** - Google OAuth provider
- **aws.cognito.IdentityProvider** - GitHub OAuth provider
- **aws.cognito.IdentityProvider** - Facebook OAuth provider (optional)
- **aws.cognito.IdentityProvider** - SAML provider for enterprise SSO (optional)

## Lambda Triggers
- **aws.lambda.Function** - Pre-signup trigger (user validation)
- **aws.lambda.Function** - Post-confirmation trigger (user onboarding)
- **aws.lambda.Function** - Pre-authentication trigger (security checks)
- **aws.lambda.Function** - Post-authentication trigger (session logging)
- **aws.lambda.Function** - Custom message trigger (email customization)
- **aws.lambda.Function** - User migration trigger (legacy system integration)

## IAM Resources for Authentication
- **aws.iam.Role** - Authenticated user role (logged-in users)
- **aws.iam.Role** - Unauthenticated user role (guest access)
- **aws.iam.Role** - Admin user role (elevated permissions)
- **aws.iam.Policy** - Application access policy for authenticated users
- **aws.iam.Policy** - S3 access policy for user uploads
- **aws.iam.Policy** - API Gateway access policy

## API Gateway Integration
- **aws.apigateway.Authorizer** - Cognito User Pool authorizer
- **aws.apigateway.RequestValidator** - JWT token validation
- **aws.apigateway.UsagePlan** - Rate limiting by user tier

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - Lambda trigger logs
- **aws.cloudwatch.LogGroup** - Authentication audit logs
- **aws.cloudwatch.Alarm** - Failed authentication attempts alarm
- **aws.cloudwatch.Alarm** - Suspicious activity alarm
- **aws.cloudwatch.Dashboard** - Authentication metrics dashboard

## SES Integration (Optional)
- **aws.ses.DomainIdentity** - Custom email domain for Cognito
- **aws.ses.DomainDkim** - DKIM signing for email authentication
- **aws.ses.Template** - Custom email templates

## Estimated Resource Count: 28-35 resources
## Estimated Monthly Cost:
- Cognito MAU: $0.0055 per MAU (first 50K free)
- Lambda triggers: $0.10-2.00 (depending on usage)
- SES emails: $0.10 per 1,000 emails
- CloudWatch logs: $0.50-1.50
- **Total: ~$1-5/month** (scales with users)

## Resource Dependencies
- Depends on: Security stack (IAM roles), Secrets stack (OAuth credentials)
- Required by: API services, Frontend applications, Mobile apps