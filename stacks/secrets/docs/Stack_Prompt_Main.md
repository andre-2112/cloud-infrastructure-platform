# Secrets Stack Pulumi Generation Prompt

## Context
Create Pulumi TypeScript code for secrets management using AWS Secrets Manager for ${PROJECT_NAME}. This stack provides secure storage and rotation for application secrets, database credentials, and API keys.

## Requirements
1. **Secret Storage**: Database passwords, API keys, JWT tokens, session secrets
2. **Secret Rotation**: Automatic rotation for database credentials
3. **Access Policies**: IAM policies for controlled secret access
4. **Encryption**: Use KMS keys from security stack

## Dependencies
- **security**: KMS keys for encryption

## Key Outputs
- databaseMasterPasswordArn, jwtSigningKeyArn, sessionSecretArn, externalApiKeysArn
- secretsReadPolicyArn, secretsRotationPolicyArn

## State Integration
Use variables: `${DEPLOYMENT_ID}`, `${ORG_NAME}`, `${PROJECT_NAME}`. Tag resources and reference security stack KMS keys through centralized state.