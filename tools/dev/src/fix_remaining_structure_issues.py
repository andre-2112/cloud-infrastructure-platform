#!/usr/bin/env python3
"""Fix remaining structure issues identified by user"""

import os

os.chdir('C:/Users/Admin/Documents/Workspace/cloud/tools/docs')

print("="*80)
print("FIXING REMAINING STRUCTURE ISSUES")
print("="*80)

# Issue 1: Line 571 - manifest/ and stacks/ should be default/ and config/
print("\n1. Fixing template location structure (line 571)...")

with open('Multi_Stack_Architecture.3.1.md', 'r', encoding='utf-8') as f:
    content = f.read()

OLD_TEMPLATE_LOCATION = """**Template Location:**
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

NEW_TEMPLATE_LOCATION = """**Template Location:**
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

if OLD_TEMPLATE_LOCATION in content:
    content = content.replace(OLD_TEMPLATE_LOCATION, NEW_TEMPLATE_LOCATION)
    print("   Fixed: manifest/ -> default/, stacks/ -> config/, custom/ is sibling")
else:
    print("   Pattern not found or already fixed")

# Issue 2: Stacks missing docs subdirectory (lines 779+)
print("\n2. Fixing stack structure to include docs subdirectory...")

# Find the stacks section in the directory tree
lines = content.split('\n')
fixed_lines = []
in_stacks_section = False
stack_count = 0

for i, line in enumerate(lines):
    # Detect start of stacks section in directory tree
    if '├── stacks/' in line or '└── stacks/' in line:
        in_stacks_section = True
        fixed_lines.append(line)
        continue

    # Detect end of stacks section (when we hit deploy/ or end of tree)
    if in_stacks_section and ('└── deploy/' in line or '├── deploy/' in line):
        in_stacks_section = False

    # Fix stack entries that have /src/ without /docs/
    if in_stacks_section and '/src/' in line and '├── ' in line and '│   ├──' in line:
        # This is a stack entry like "│   ├── dns/src/"
        # We need to add the stack parent and docs subdirectory
        indent = line[:line.index('├──')]
        stack_name_match = line.split('├── ')[1].split('/src/')[0] if '/src/' in line else None

        if stack_name_match:
            # Add stack parent directory
            fixed_lines.append(f"{indent}├── {stack_name_match}/")
            # Add docs subdirectory
            fixed_lines.append(f"{indent}│   ├── docs/")
            # Add src subdirectory
            fixed_lines.append(f"{indent}│   └── src/")
            stack_count += 1

            # Skip lines until we hit the next stack or end of this stack's files
            # (we're replacing the structure)
            continue

    fixed_lines.append(line)

if stack_count > 0:
    content = '\n'.join(fixed_lines)
    print(f"   Fixed {stack_count} stack entries to include docs/ subdirectory")
else:
    print("   Stack structures need manual review")

# Issue 3: Line 816 - Deployment_Manifest.yaml under src/ instead of root
print("\n3. Fixing Deployment_Manifest.yaml location...")

OLD_DEPLOY_STRUCTURE = """└── deploy/                                 # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/         # Deployment Example 1
    │   ├── src/
    │   │   └── Deployment_Manifest.yaml    # Deployment config
    │   ├── config/"""

NEW_DEPLOY_STRUCTURE = """└── deploy/                                 # Active Deployments
    ├── D1BRV40-CompanyA-ecommerce/         # Deployment Example 1
    │   ├── Deployment_Manifest.yaml        # Deployment config
    │   ├── config/"""

if OLD_DEPLOY_STRUCTURE in content:
    content = content.replace(OLD_DEPLOY_STRUCTURE, NEW_DEPLOY_STRUCTURE)
    print("   Fixed: Moved Deployment_Manifest.yaml from src/ to deployment root")
else:
    print("   Pattern not found - checking for variations...")
    # Try alternative pattern
    if '│   ├── src/' in content and '│   │   └── Deployment_Manifest.yaml' in content:
        # More flexible replacement
        import re
        # Find and replace the specific pattern
        pattern = r'(\s+│   ├── src/\n\s+│   │   └── Deployment_Manifest\.yaml.*\n)(\s+│   ├── config/)'
        replacement = r'    │   ├── Deployment_Manifest.yaml        # Deployment config\n\2'
        content = re.sub(pattern, replacement, content)
        print("   Fixed with flexible pattern matching")

# Write back
with open('Multi_Stack_Architecture.3.1.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*80)
print("DONE - Verify changes:")
print("  Line ~571: Check template structure (default/, config/, custom/)")
print("  Line ~779: Check stacks have both docs/ and src/")
print("  Line ~816: Check Deployment_Manifest.yaml at deployment root")
print("="*80)
