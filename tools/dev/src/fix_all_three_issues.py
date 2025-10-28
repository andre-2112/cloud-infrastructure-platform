#!/usr/bin/env python3
"""Fix all three structural issues at once"""

import os
import re

os.chdir('C:/Users/Admin/Documents/Workspace/cloud/tools/docs')

with open('Multi_Stack_Architecture.3.1.md', 'r', encoding='utf-8') as f:
    content = f.read()

print("="*80)
print("FIXING ALL THREE STRUCTURAL ISSUES")
print("="*80)

# Issue 1: Template location structure (around line 571)
print("\n1. Fixing template location (manifest/ -> default/, stacks/ -> config/)...")

OLD1 = """**Template Location:**
```
./cloud/tools/templates/
├── manifest/
│   ├── default.yaml
│   ├── minimal.yaml
│   ├── microservices.yaml
│   ├── data-platform.yaml
│   └── custom/
│       └── <org>-standard.yaml
└── stacks/
    ├── network.yaml
    ├── dns.yaml
    ├── security.yaml
    └── ... (all 16 stacks)
```"""

NEW1 = """**Template Location:**
```
./cloud/tools/templates/
├── default/                         # Manifest templates
│   ├── default.yaml
│   ├── minimal.yaml
│   ├── microservices.yaml
│   └── data-platform.yaml
├── custom/                          # Organization-specific manifest templates
│   └── <org>-standard.yaml
└── config/                          # Stack definition templates
    ├── network.yaml
    ├── dns.yaml
    ├── security.yaml
    └── ... (all 16 stacks)
```"""

if OLD1 in content:
    content = content.replace(OLD1, NEW1)
    print("   OK Fixed template location structure")
else:
    print("   ERROR Pattern not found")

# Issue 2: Deployment manifest location (around line 816)
print("\n2. Fixing Deployment_Manifest.yaml location (src/ -> root)...")

OLD2 = """└── deploy/                                 # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/         # Deployment Example 1
    │   ├── src/
    │   │   └── Deployment_Manifest.yaml    # Deployment config
    │   ├── config/"""

NEW2 = """└── deploy/                                 # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/         # Deployment Example 1
    │   ├── Deployment_Manifest.yaml        # Deployment config
    │   ├── config/"""

if OLD2 in content:
    content = content.replace(OLD2, NEW2)
    print("   OK Fixed Deployment_Manifest.yaml location")
else:
    print("   ERROR Pattern not found")

# Issue 3: Add docs/ subdirectory to all stacks (around line 779)
print("\n3. Fixing stack structures (adding docs/ subdirectory)...")

# This is the complex one - need to replace the entire stacks section
OLD3_START = """│   │
│   ├── dns/src/                            # DNS Stack
│   │   ├── Pulumi.yaml                     # Minimal config
│   │   ├── index.ts                        # Main program
│   │   ├── route53.ts                      # Route53 resources
│   │   ├── acm.ts                          # Certificate Manager
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── network/src/                        # Network Stack
│   │   ├── Pulumi.yaml
│   │   ├── index.ts
│   │   ├── vpc.ts                          # VPC resources
│   │   ├── subnets.ts                      # Subnet resources
│   │   ├── routing.ts                      # Route tables
│   │   ├── nat-gateway.ts                  # NAT gateways
│   │   ├── endpoints.ts                    # VPC endpoints
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── security/src/                       # Security Stack
│   ├── secrets/src/                        # Secrets Stack
│   ├── authentication/src/                 # Authentication Stack
│   ├── storage/src/                        # Storage Stack
│   ├── database-rds/src/                   # Database Stack
│   ├── containers-images/src/              # Container Images
│   ├── containers-apps/src/                # Container Apps
│   ├── services-ecr/src/                   # ECR Stack
│   ├── services-ecs/src/                   # ECS Stack
│   ├── services-eks/src/                   # EKS Stack
│   ├── services-api/src/                   # API Gateway Stack
│   ├── compute-ec2/src/                    # EC2 Stack
│   ├── compute-lambda/src/                 # Lambda Stack
│   └── monitoring/src/                     # Monitoring Stack"""

NEW3_START = """│   │
│   ├── dns/                                # DNS Stack
│   │   ├── docs/
│   │   └── src/
│   │       ├── Pulumi.yaml                 # Minimal config
│   │       ├── index.ts                    # Main program
│   │       ├── route53.ts                  # Route53 resources
│   │       ├── acm.ts                      # Certificate Manager
│   │       ├── package.json
│   │       └── tsconfig.json
│   │
│   ├── network/                            # Network Stack
│   │   ├── docs/
│   │   └── src/
│   │       ├── Pulumi.yaml
│   │       ├── index.ts
│   │       ├── vpc.ts                      # VPC resources
│   │       ├── subnets.ts                  # Subnet resources
│   │       ├── routing.ts                  # Route tables
│   │       ├── nat-gateway.ts              # NAT gateways
│   │       ├── endpoints.ts                # VPC endpoints
│   │       ├── package.json
│   │       └── tsconfig.json
│   │
│   ├── security/                           # Security Stack
│   │   ├── docs/
│   │   └── src/
│   ├── secrets/                            # Secrets Stack
│   │   ├── docs/
│   │   └── src/
│   ├── authentication/                     # Authentication Stack
│   │   ├── docs/
│   │   └── src/
│   ├── storage/                            # Storage Stack
│   │   ├── docs/
│   │   └── src/
│   ├── database-rds/                       # Database Stack
│   │   ├── docs/
│   │   └── src/
│   ├── containers-images/                  # Container Images
│   │   ├── docs/
│   │   └── src/
│   ├── containers-apps/                    # Container Apps
│   │   ├── docs/
│   │   └── src/
│   ├── services-ecr/                       # ECR Stack
│   │   ├── docs/
│   │   └── src/
│   ├── services-ecs/                       # ECS Stack
│   │   ├── docs/
│   │   └── src/
│   ├── services-eks/                       # EKS Stack
│   │   ├── docs/
│   │   └── src/
│   ├── services-api/                       # API Gateway Stack
│   │   ├── docs/
│   │   └── src/
│   ├── compute-ec2/                        # EC2 Stack
│   │   ├── docs/
│   │   └── src/
│   ├── compute-lambda/                     # Lambda Stack
│   │   ├── docs/
│   │   └── src/
│   └── monitoring/                         # Monitoring Stack
│       ├── docs/
│       └── src/"""

if OLD3_START in content:
    content = content.replace(OLD3_START, NEW3_START)
    print("   OK Fixed all stack structures (added docs/ subdirectories)")
else:
    print("   ERROR Pattern not found")

# Write back
with open('Multi_Stack_Architecture.3.1.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*80)
print("ALL THREE ISSUES FIXED")
print("Verify:")
print("  Line ~571: template structure (default/, config/, custom/ as siblings)")
print("  Line ~779: stacks have both docs/ and src/")
print("  Line ~816: Deployment_Manifest.yaml at deployment root")
print("="*80)
