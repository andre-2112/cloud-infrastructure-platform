#!/usr/bin/env python3
"""
Migrate stacks from Pulumi-2 to cloud directory structure
Architecture 3.1 - Session 2.1 Implementation
"""

import os
import re
import shutil
from pathlib import Path

# Source and destination roots (Windows-compatible paths, supports WORKSPACE_ROOT env var)
import os
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "C:/Users/Admin/Documents/Workspace"))
SOURCE_ROOT = WORKSPACE_ROOT / "Pulumi-2" / "aws" / "build"
DEST_ROOT = WORKSPACE_ROOT / "cloud" / "stacks"

# All 16 stacks to migrate
STACKS = [
    "network",
    "security",
    "dns",
    "secrets",
    "authentication",
    "storage",
    "database-rds",
    "containers-images",
    "containers-apps",
    "services-ecr",
    "services-ecs",
    "services-eks",
    "services-api",
    "compute-ec2",
    "compute-lambda",
    "monitoring",
]


def adjust_text_content(content: str, stack_name: str) -> str:
    """Apply all required text replacements for Architecture 3.1"""

    # Replace "multi-stack" → "cloud"
    content = content.replace("multi-stack", "cloud")
    content = content.replace("Multi-Stack", "Cloud")
    content = content.replace("MULTI-STACK", "CLOUD")

    # Replace "staging" → "stage" (be careful not to replace in words like "staging")
    content = re.sub(r'\bstaging\b', 'stage', content)
    content = re.sub(r'\bStaging\b', 'Stage', content)

    # Update directory paths
    content = content.replace("/Pulumi-2/aws/build/", "/cloud/stacks/")
    content = content.replace("./aws/build/", "./cloud/stacks/")
    content = content.replace("/admin/v2/", "/cloud/tools/")
    content = content.replace("./admin/v2/", "./cloud/tools/")
    content = content.replace("/resources/", "/src/")  # For component references in docs
    content = content.replace("resources/", "src/")

    # Update Architecture version references
    content = re.sub(r'Architecture 2\.\d+', 'Architecture 3.1', content)
    content = re.sub(r'architecture 2\.\d+', 'architecture 3.1', content)
    content = re.sub(r'v2\.\d+', 'v3.1', content)

    # Update stack naming references (examples in docs)
    # OLD: D1BRV40-dev → NEW: D1BRV40-network-dev
    content = re.sub(
        r'\b(D\w{6})-([a-z]+)\b',
        rf'\1-{stack_name}-\2',
        content
    )

    return content


def copy_and_adjust_docs(stack_name: str) -> int:
    """Copy and adjust all documentation files for a stack"""
    source_docs = SOURCE_ROOT / stack_name / "v2" / "docs"
    dest_docs = DEST_ROOT / stack_name / "docs"

    if not source_docs.exists():
        print(f"  [WARN] No docs directory found for {stack_name}")
        return 0

    count = 0
    for doc_file in source_docs.glob("*.md"):
        # Skip versioned files if non-versioned exists
        if ".2.2." in doc_file.name:
            non_versioned = doc_file.parent / doc_file.name.replace(".2.2.", ".")
            if non_versioned.exists():
                continue  # Skip, use non-versioned

        # Read source file
        try:
            content = doc_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"  [WARN] Error reading {doc_file.name}: {e}")
            continue

        # Apply adjustments
        adjusted_content = adjust_text_content(content, stack_name)

        # Write to destination
        dest_file = dest_docs / doc_file.name
        try:
            dest_file.write_text(adjusted_content, encoding='utf-8')
            count += 1
        except Exception as e:
            print(f"  [WARN] Error writing {dest_file.name}: {e}")

    return count


def adjust_code_content(content: str, filename: str, stack_name: str) -> str:
    """Adjust code file content for Architecture 3.1"""

    # Replace "multi-stack" in comments
    content = content.replace("multi-stack", "cloud")

    # Update StackReference naming to v3.1 format
    # OLD: `${orgName}/network/${environment}`
    # OLD: `${deploymentId}-${environment}`
    # NEW: `${orgName}/${projectName}/${deploymentId}-${stackName}-${environment}`

    # Look for StackReference patterns and update them
    # This is a complex regex, so we'll do a simple placeholder approach
    if "StackReference" in content:
        # Add a comment noting the v3.1 format
        if "new pulumi.StackReference" in content:
            content = content.replace(
                "new pulumi.StackReference(",
                "// v3.1 format: ${orgName}/${projectName}/${deploymentId}-${stackName}-${environment}\n    new pulumi.StackReference("
            )

    # If this is index.ts, update imports for components moved to src/
    if filename == "index.ts":
        # Update relative imports to point to src/ directory
        content = re.sub(
            r'from\s+["\']\.\/([^"\']+)["\']',
            r'from "./src/\1"',
            content
        )
        # Fix if we accidentally added src/src/
        content = content.replace('from "./src/src/', 'from "./src/')

    return content


def copy_and_restructure_code(stack_name: str) -> tuple:
    """Copy and restructure stack code files"""
    source_resources = SOURCE_ROOT / stack_name / "v2" / "resources"
    dest_stack_root = DEST_ROOT / stack_name
    dest_src = DEST_ROOT / stack_name / "src"

    if not source_resources.exists():
        print(f"  [WARN] No resources directory found for {stack_name}")
        return (0, 0, 0)

    index_count = 0
    component_count = 0
    config_count = 0

    # Process all TypeScript files
    for ts_file in source_resources.glob("*.ts"):
        content = ts_file.read_text(encoding='utf-8')

        # Check if this is index file
        if ts_file.name in ("index.ts", "index.2.2.ts"):
            # Move to stack root (use index.ts if both exist)
            dest_file = dest_stack_root / "index.ts"
            adjusted_content = adjust_code_content(content, "index.ts", stack_name)
            dest_file.write_text(adjusted_content, encoding='utf-8')
            index_count = 1
        else:
            # Move to src/ subdirectory (component files)
            dest_file = dest_src / ts_file.name
            adjusted_content = adjust_code_content(content, ts_file.name, stack_name)
            dest_file.write_text(adjusted_content, encoding='utf-8')
            component_count += 1

    # Copy configuration files to stack root
    for config_file in ["Pulumi.yaml", "package.json", "tsconfig.json"]:
        source_file = source_resources / config_file
        if source_file.exists():
            dest_file = dest_stack_root / config_file
            content = source_file.read_text(encoding='utf-8')

            # Adjust Pulumi.yaml to point to root index.ts
            if config_file == "Pulumi.yaml":
                content = content.replace("main: resources/index.ts", "main: index.ts")
                content = content.replace("main: index.2.2.ts", "main: index.ts")
                if "main:" not in content:
                    # Add main entry if missing
                    content = content.rstrip() + "\nmain: index.ts\n"

            # Update package.json version to 0.7.0
            if config_file == "package.json":
                content = re.sub(r'"version":\s*"[^"]*"', '"version": "0.7.0"', content)

            dest_file.write_text(content, encoding='utf-8')
            config_count += 1

    return (index_count, component_count, config_count)


def migrate_stack(stack_name: str) -> dict:
    """Migrate a single stack completely"""
    print(f"\nMigrating stack: {stack_name}")

    # Copy and adjust documentation
    doc_count = copy_and_adjust_docs(stack_name)
    print(f"  [OK] Docs: {doc_count} files")

    # Copy and restructure code
    index_count, component_count, config_count = copy_and_restructure_code(stack_name)
    print(f"  [OK] Code: index.ts={'OK' if index_count else 'MISSING'}, "
          f"{component_count} components, {config_count} config files")

    return {
        "docs": doc_count,
        "index": index_count,
        "components": component_count,
        "configs": config_count,
    }


def main():
    """Main migration process"""
    print("=" * 70)
    print("Stack Migration: Pulumi-2 -> Cloud (Architecture 3.1)")
    print("=" * 70)

    results = {}
    for stack in STACKS:
        try:
            results[stack] = migrate_stack(stack)
        except Exception as e:
            print(f"  [ERROR] Error migrating {stack}: {e}")
            results[stack] = {"error": str(e)}

    # Summary
    print("\n" + "=" * 70)
    print("Migration Summary")
    print("=" * 70)

    total_docs = 0
    total_index = 0
    total_components = 0
    total_configs = 0
    errors = 0

    for stack, result in results.items():
        if "error" in result:
            print(f"[ERROR] {stack}: ERROR - {result['error']}")
            errors += 1
        else:
            total_docs += result['docs']
            total_index += result['index']
            total_components += result['components']
            total_configs += result['configs']
            print(f"[OK] {stack}: {result['docs']} docs, {result['components']} components")

    print(f"\nTotals:")
    print(f"   Stacks migrated: {len(STACKS) - errors}/{len(STACKS)}")
    print(f"   Documentation files: {total_docs}")
    print(f"   Index files: {total_index}")
    print(f"   Component files: {total_components}")
    print(f"   Config files: {total_configs}")

    if errors == 0:
        print(f"\n[SUCCESS] All stacks migrated successfully!")
    else:
        print(f"\n[WARNING] {errors} stack(s) had errors")

    print("=" * 70)


if __name__ == "__main__":
    main()
