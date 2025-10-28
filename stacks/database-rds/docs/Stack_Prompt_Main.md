# Database RDS Stack Pulumi Generation Prompt

Create Pulumi TypeScript code for PostgreSQL RDS database for ${PROJECT_NAME}. Include primary instance, read replica (production), subnet group, parameter group, monitoring, and backup configuration. Dependencies: network, security, secrets. Key outputs: primaryEndpoint, replicaEndpoint, subnetGroupName, masterUserSecretArn. Use variables: ${DEPLOYMENT_ID}, ${PROJECT_NAME}. Focus on encryption, performance insights, and automated backups.
