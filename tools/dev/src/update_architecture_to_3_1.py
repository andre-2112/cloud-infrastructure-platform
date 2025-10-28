#!/usr/bin/env python3
"""
Script to update Multi_Stack_Architecture.3.0.md to 3.1.md
Makes surgical changes only where needed.
"""

import re
from pathlib import Path

def update_architecture_document():
    """Update architecture document from 3.0 to 3.1"""

    # Read the source file
    source_file = Path("C:/Users/Admin/Documents/Workspace/cloud/tools/docs/Multi_Stack_Architecture.3.0.md")
    dest_file = Path("C:/Users/Admin/Documents/Workspace/cloud/tools/docs/Multi_Stack_Architecture.3.1.md")

    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Starting document transformation...")

    # 1. Update header
    content = content.replace(
        "# Cloud Infrastructure Orchestration Platform v3.0",
        "# Cloud Infrastructure Orchestration Platform v3.1"
    )

    content = re.sub(
        r'\*\*Version:\*\* 3\.0',
        '**Version:** 3.1',
        content
    )

    content = re.sub(
        r'\*\*Date:\*\* 2025-10-09',
        '**Date:** 2025-10-21',
        content
    )

    # 2. Replace note about document location
    content = content.replace(
        "**Note:** This document will be moved to ./cloud/tools/docs/ when the new directory structure is created in Session 2.",
        """**Changes from v3.0:**
- **MAJOR:** Updated Pulumi State Management structure - Projects now represent business projects, not stacks
- **MAJOR:** Updated Pulumi Stack naming convention to `<deployment-id>-<stack-name>-<environment>`
- Fixed deployment directory structure - removed incorrect `src/` subdirectory for manifest
- Fixed deployment directory naming - consistently using `<deployment-id>-<org>-<project>/` format
- Completed templates directory structure documentation
- Updated all document version references to 3.1

**Note:** This document is located in ./cloud/tools/docs/ as the directory structure has been created."""
    )

    # 3. Update all references to 3.0 documents
    content = re.sub(r'\.3\.0\.md', '.3.1.md', content)
    content = re.sub(r' v3\.0', ' v3.1', content)
    content = re.sub(r'Version 3\.0', 'Version 3.1', content)
    content = re.sub(r'version 3\.0', 'version 3.1', content)
    content = re.sub(r'Architecture 3\.0', 'Architecture 3.1', content)

    # 4. Fix deployment manifest location - remove src/ subdirectory
    content = content.replace(
        "│   ├── src/\n│   │   └── Deployment_Manifest.yaml    # Deployment config",
        "│   ├── Deployment_Manifest.yaml    # Deployment configuration"
    )

    # 5. Update "What's New in v3.0" section title
    content = re.sub(
        r'## What\'s New in v3\.0',
        "## What's New in v3.1",
        content
    )

    # 6. Update Pulumi Stack Naming Convention section (lines ~1396-1418)
    old_pulumi_naming = """**Pulumi Stack Naming Convention:**
```
<deployment-id>-<environment>

Examples:
- D1BRV40-dev
- D1BRV40-stage
- D1BRV40-prod
```

**Stack Organization in Pulumi Cloud:**
```
Pulumi Organization: companyA
├── Project: network
│   ├── Stack: D1BRV40-dev
│   ├── Stack: D1BRV40-stage
│   └── Stack: D1BRV40-prod
├── Project: security
│   ├── Stack: D1BRV40-dev
│   ├── Stack: D1BRV40-stage
│   └── Stack: D1BRV40-prod
└── ... (14 more projects)
```"""

    new_pulumi_naming = """**Pulumi Stack Naming Convention:**
```
<deployment-id>-<stack-name>-<environment>

Examples:
- D1BRV40-network-dev
- D1BRV40-network-stage
- D1BRV40-network-prod
- D1BRV40-security-dev
```

**Stack Organization in Pulumi Cloud:**
```
Pulumi Organization: CompanyA
├── Project: ecommerce                   # Business project name
│   ├── Stack: D1BRV40-network-dev
│   ├── Stack: D1BRV40-network-stage
│   ├── Stack: D1BRV40-network-prod
│   ├── Stack: D1BRV40-security-dev
│   ├── Stack: D1BRV40-security-stage
│   ├── Stack: D1BRV40-security-prod
│   └── ... (all stacks for D1BRV40 deployment)
├── Project: analytics                   # Another business project
│   ├── Stack: D1BRV50-network-dev
│   ├── Stack: D1BRV50-network-stage
│   └── ... (all stacks for D1BRV50 deployment)
└── Organization: CompanyB
    └── Project: mobile
        └── ... (stacks for CompanyB projects)
```

**Key Changes from v3.0:**
- Pulumi Projects now represent **business projects** (ecommerce, mobile, analytics)
- Stack names include both deployment ID and stack name: `<deployment-id>-<stack-name>-<environment>`
- Better logical grouping by business project
- Easier resource discovery and management
- Clearer separation between different deployments"""

    content = content.replace(old_pulumi_naming, new_pulumi_naming)

    # 7. Update State Management section (lines ~1918-1939)
    old_state_structure = """**State Storage Architecture:**
```
Pulumi Cloud
├── Organization: companyA
│   ├── Project: dns
│   │   ├── Stack: D1BRV40-dev
│   │   │   ├── State Version: 1 (initial)
│   │   │   ├── State Version: 2 (update)
│   │   │   └── State Version: 3 (current)
│   │   ├── Stack: D1BRV40-stage
│   │   └── Stack: D1BRV40-prod
│   │
│   ├── Project: network
│   │   ├── Stack: D1BRV40-dev
│   │   ├── Stack: D1BRV40-stage
│   │   └── Stack: D1BRV40-prod
│   │
│   └── ... (14 more projects for remaining stacks)
│
└── Organization: companyB
    └── ... (same structure for CompanyB)
```"""

    new_state_structure = """**State Storage Architecture:**
```
Pulumi Cloud
├── Organization: CompanyA
│   ├── Project: ecommerce               # Business project
│   │   ├── Stack: D1BRV40-network-dev
│   │   │   ├── State Version: 1 (initial)
│   │   │   ├── State Version: 2 (update)
│   │   │   └── State Version: 3 (current)
│   │   ├── Stack: D1BRV40-network-stage
│   │   ├── Stack: D1BRV40-network-prod
│   │   ├── Stack: D1BRV40-security-dev
│   │   ├── Stack: D1BRV40-security-stage
│   │   ├── Stack: D1BRV40-security-prod
│   │   ├── Stack: D1BRV40-dns-dev
│   │   └── ... (all stacks for ecommerce project)
│   │
│   ├── Project: analytics               # Another business project
│   │   ├── Stack: D1BRV50-network-dev
│   │   ├── Stack: D1BRV50-network-stage
│   │   └── ... (all stacks for analytics project)
│   │
│   └── ... (more projects for CompanyA)
│
└── Organization: CompanyB
    ├── Project: mobile
    │   ├── Stack: D1BRV45-network-dev
    │   └── ... (all stacks for mobile project)
    └── ... (more projects for CompanyB)
```

**State Organization Benefits:**
- Logical grouping by business project
- All stacks for a deployment grouped under one project
- Clear separation between different deployments
- Easier navigation and discovery in Pulumi Cloud console
- Better alignment with organizational structure"""

    content = content.replace(old_state_structure, new_state_structure)

    # 8. Update templates/manifest/ to templates/default/ in directory structure
    content = content.replace("├── templates/manifest/", "├── templates/default/")
    content = content.replace("│   ├── manifest/                       # Manifest Templates",
                            "│   ├── default/                       # Manifest Templates")

    # 9. Add templates/docs/ and templates/stack/ to directory structure if missing
    # This is handled by the full directory structure replacement

    # 10. Update "After (v3.0):" to "After (v3.1):" in What's New section
    content = content.replace("**After (v3.0):**", "**After (v3.1):**")

    # 11. Fix the directory structure section to be complete
    # First, let's find and replace the incomplete section
    old_templates_section = """│   ├── templates/                          # Deployment Templates
│   │   ├── manifest/                       # Manifest Templates
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

    new_templates_section = """│   ├── templates/                          # Deployment Templates
│   │   │
│   │   ├── docs/                           # Stack Markdown Templates
│   │   │   ├── Stack_Prompt_Main.md.template
│   │   │   ├── Stack_Prompt_Extra.md.template
│   │   │   ├── Stack_Definitions.md.template
│   │   │   ├── Stack_Resources.md.template
│   │   │   ├── Stack_History_Errors.md.template
│   │   │   ├── Stack_History_Fixes.md.template
│   │   │   └── Stack_History.md.template
│   │   │
│   │   ├── stack/                          # Stack Pulumi Templates
│   │   │   ├── index.ts.template           # Main entry point template
│   │   │   ├── src/
│   │   │   │   ├── component-example.ts.template
│   │   │   │   └── outputs.ts.template     # Exported outputs template
│   │   │   ├── Pulumi.yaml.template        # Stack metadata template
│   │   │   ├── package.json.template       # NPM package template
│   │   │   └── tsconfig.json.template      # TypeScript config template
│   │   │
│   │   ├── config/                         # Stack Definitions (with dependencies)
│   │   │   ├── network.yaml                # Network stack template
│   │   │   ├── dns.yaml                    # DNS stack template
│   │   │   ├── security.yaml               # Security stack template
│   │   │   └── ... (13 more stacks)
│   │   │
│   │   ├── default/                        # Manifest Templates
│   │   │   ├── default.yaml                # Full platform template
│   │   │   ├── minimal.yaml                # Minimal infrastructure
│   │   │   ├── microservices.yaml          # Container-focused
│   │   │   └── data-platform.yaml          # Data processing focus
│   │   │
│   │   └── custom/                         # Organization-specific Custom Templates"""

    content = content.replace(old_templates_section, new_templates_section)

    # 12. Update section "After (v3.0):" describing stack naming
    old_stack_naming_desc = """#### 9. Stack Naming Convention

**Before (Architecture 2.3):**
- Pulumi stack naming: `<org>/<stack>/<environment>`

**After (v3.0):**
- Pulumi stack naming: `<deployment-id>-<environment>`
- Simpler, deployment-centric naming

**Impact:**
- Clearer stack identification
- Better alignment with deployment model
- Simpler Pulumi Cloud organization"""

    new_stack_naming_desc = """#### 9. Stack Naming Convention

**Before (Architecture 2.3):**
- Pulumi stack naming: `<org>/<stack>/<environment>`
- Stacks treated as Pulumi Projects

**After (v3.1):**
- Pulumi stack naming: `<deployment-id>-<stack-name>-<environment>`
- Business projects as Pulumi Projects
- Stacks grouped by deployment within projects

**Impact:**
- Clearer stack identification with deployment context
- Better logical grouping by business project
- Easier resource discovery and management
- Better alignment with organizational structure"""

    content = content.replace(old_stack_naming_desc, new_stack_naming_desc)

    # Write the updated content
    with open(dest_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Successfully created {dest_file}")
    print("\nChanges made:")
    print("  1. Updated version to 3.1")
    print("  2. Added changelog at top")
    print("  3. Fixed deployment manifest location (removed src/ subdirectory)")
    print("  4. Updated all 3.0 references to 3.1")
    print("  5. Updated Pulumi stack naming convention")
    print("  6. Updated Pulumi state management structure")
    print("  7. Completed templates directory structure")
    print("  8. Updated 'What's New' section")

if __name__ == "__main__":
    update_architecture_document()
