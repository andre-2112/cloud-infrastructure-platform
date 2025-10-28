#!/usr/bin/env python3
"""Fix templates directory structure across ALL documents"""

import os
import re

os.chdir('C:/Users/Admin/Documents/Workspace/cloud/tools/docs')

# The CORRECT structure from Directory_Structure_Diagram.3.1.md
CORRECT_TEMPLATES_STRUCTURE = """│   ├── templates/                                      # Deployment Templates
│   │   │
│   │   ├── docs/                                       # Stack Markdown Templates
│   │   │   ├── Stack_Prompt_Main.md.template
│   │   │   ├── Stack_Prompt_Extra.md.template
│   │   │   ├── Stack_Definitions.md.template
│   │   │   ├── Stack_Resources.md.template
│   │   │   ├── Stack_History_Errors.md.template
│   │   │   ├── Stack_History_Fixes.md.template
│   │   │   └── Stack_History.md.template
│   │   │
│   │   ├── stack/                                      # Stack Pulumi Templates
│   │   │   ├── index.ts.template                       # Main entry point template
│   │   │   ├── src/
│   │   │   │   ├── component-example.ts.template       # Optional additional stack components
│   │   │   │   └── outputs.ts.template                 # Exported outputs template
│   │   │   ├── Pulumi.yaml.template                    # Stack metadata template
│   │   │   ├── package.json.template                   # NPM package template
│   │   │   └── tsconfig.json.template                  # TypeScript config template
│   │   │
│   │   ├── config/                                     # Stack Definitions (with dependencies)
│   │   │   ├── network.yaml                            # Network stack template
│   │   │   ├── dns.yaml                                # DNS stack template
│   │   │   ├── security.yaml                           # Security stack template
│   │   │   ├── secrets.yaml                            # Secrets stack template
│   │   │   ├── authentication.yaml                     # Authentication stack template
│   │   │   ├── storage.yaml                            # Storage stack template
│   │   │   ├── database-rds.yaml                       # Database stack template
│   │   │   ├── containers-images.yaml                  # Container images stack template
│   │   │   ├── containers-apps.yaml                    # Container apps stack template
│   │   │   ├── services-ecr.yaml                       # ECR service stack template
│   │   │   ├── services-ecs.yaml                       # ECS service stack template
│   │   │   ├── services-eks.yaml                       # EKS service stack template
│   │   │   ├── services-api.yaml                       # API Gateway stack template
│   │   │   ├── compute-ec2.yaml                        # EC2 stack template
│   │   │   ├── compute-lambda.yaml                     # Lambda stack template
│   │   │   └── monitoring.yaml                         # Monitoring stack template
│   │   │
│   │   ├── default/                                    # Manifest Templates
│   │   │   ├── default.yaml                            # Full platform template
│   │   │   ├── minimal.yaml                            # Minimal infrastructure
│   │   │   ├── microservices.yaml                      # Container-focused
│   │   │   └── data-platform.yaml                      # Data processing focus
│   │   │
│   │   └── custom/                                     # Organization-specific Custom Templates"""

# The WRONG structure currently in Multi_Stack_Architecture.3.1.md
WRONG_TEMPLATES_STRUCTURE = """│   ├── templates/                          # Deployment Templates
│   │   ├── default/                       # Manifest Templates
│   │   │   ├── default.yaml                # Full platform template
│   │   │   ├── minimal.yaml                # Minimal infrastructure
│   │   │   ├── microservices.yaml          # Container-focused
│   │   │   ├── data-platform.yaml          # Data processing focus
│   │   │   └── custom/                     # Organization-specific
│   │   │
│   │   └── stacks/                         # Stack Definitions (with dependencies)
│   │       ├── network.yaml                # Network stack template
│   │       ├── dns.yaml                    # DNS stack template
│   │       ├── security.yaml               # Security stack template
│   │       └── ... (13 more stacks)"""

print("Fixing templates directory structure in Multi_Stack_Architecture.3.1.md...")

with open('Multi_Stack_Architecture.3.1.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if wrong structure exists
if WRONG_TEMPLATES_STRUCTURE in content:
    print("  Found incorrect structure - replacing...")
    content = content.replace(WRONG_TEMPLATES_STRUCTURE, CORRECT_TEMPLATES_STRUCTURE)

    with open('Multi_Stack_Architecture.3.1.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print("  ✓ Fixed!")
else:
    print("  Pattern not found - checking for variations...")

    # Try to find and fix any templates section
    # Look for the line with templates/ followed by incorrect structure
    if '│   ├── templates/' in content and '└── stacks/' in content:
        print("  Found templates section with stacks/ subdirectory...")

        # Find the section start
        start_idx = content.find('│   ├── templates/                          # Deployment Templates')
        if start_idx != -1:
            # Find the end (next major section at same level or cli/)
            end_pattern = '\n│   ├── cli/'
            end_idx = content.find(end_pattern, start_idx)

            if end_idx != -1:
                # Replace the entire section
                old_section = content[start_idx:end_idx]
                print(f"  Replacing section of {len(old_section)} characters")

                new_content = content[:start_idx] + CORRECT_TEMPLATES_STRUCTURE + content[end_idx:]

                with open('Multi_Stack_Architecture.3.1.md', 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print("  ✓ Fixed using smart replacement!")
            else:
                print("  ERROR: Could not find end of templates section")
        else:
            print("  ERROR: Could not find templates section start")
    else:
        print("  Structure might already be correct or pattern is different")

# Also fix references to "stacks/" that should be "config/"
print("\nFixing template path references...")
changes = 0

# Fix: templates/stacks/ → templates/config/
if 'templates/stacks/' in content:
    print("  Found templates/stacks/ references - fixing...")
    with open('Multi_Stack_Architecture.3.1.md', 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('templates/stacks/', 'templates/config/')
    changes = content.count('templates/config/')

    with open('Multi_Stack_Architecture.3.1.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Fixed {changes} references")

# Fix: templates/manifest/ → templates/default/
if 'templates/manifest/' in content:
    print("  Found templates/manifest/ references - fixing...")
    with open('Multi_Stack_Architecture.3.1.md', 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('templates/manifest/', 'templates/default/')

    with open('Multi_Stack_Architecture.3.1.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Fixed manifest/ references")

print("\nDone!")
