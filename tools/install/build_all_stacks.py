#!/usr/bin/env python3
"""
Build all Pulumi stacks
Architecture 3.1 - Session 2.1 Verification
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Stack root (relative to workspace root)
import os
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "C:/Users/Admin/Documents/Workspace"))
STACKS_ROOT = WORKSPACE_ROOT / "cloud" / "stacks"

# All 16 stacks
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


def run_command(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def build_stack(stack_name: str) -> Dict[str, any]:
    """Build a single stack"""
    stack_dir = STACKS_ROOT / stack_name

    print(f"\nBuilding stack: {stack_name}")
    print(f"  Directory: {stack_dir}")

    result = {
        "stack": stack_name,
        "npm_install": False,
        "npm_build": False,
        "errors": [],
    }

    # Check if directory exists
    if not stack_dir.exists():
        result["errors"].append("Directory does not exist")
        return result

    # Check if index.ts exists at root
    if not (stack_dir / "index.ts").exists():
        result["errors"].append("index.ts not found at root")
        return result

    # Check if package.json exists
    if not (stack_dir / "package.json").exists():
        result["errors"].append("package.json not found")
        return result

    # npm install
    print("  Running npm install...")
    exit_code, stdout, stderr = run_command(["npm", "install"], stack_dir)

    if exit_code == 0:
        result["npm_install"] = True
        print("  [OK] npm install")
    else:
        result["errors"].append(f"npm install failed: {stderr}")
        print(f"  [ERROR] npm install failed")
        return result

    # npm run build (TypeScript compilation)
    print("  Running npm run build...")
    exit_code, stdout, stderr = run_command(["npm", "run", "build"], stack_dir)

    if exit_code == 0:
        result["npm_build"] = True
        print("  [OK] npm run build")
    else:
        # Check if it's just missing script (some stacks may not have build script)
        if "Missing script" in stderr or "Missing script" in stdout:
            # Try tsc directly
            print("  No build script, trying tsc directly...")
            exit_code, stdout, stderr = run_command(["npx", "tsc"], stack_dir)
            if exit_code == 0:
                result["npm_build"] = True
                print("  [OK] tsc compilation")
            else:
                result["errors"].append(f"TypeScript compilation failed: {stderr}")
                print(f"  [ERROR] TypeScript compilation failed")
        else:
            result["errors"].append(f"npm run build failed: {stderr}")
            print(f"  [ERROR] npm run build failed")

    return result


def main():
    """Build all stacks"""
    print("=" * 70)
    print("Building All Pulumi Stacks - Architecture 3.1")
    print("=" * 70)

    results = []
    for stack in STACKS:
        try:
            result = build_stack(stack)
            results.append(result)
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            results.append({
                "stack": stack,
                "npm_install": False,
                "npm_build": False,
                "errors": [str(e)],
            })

    # Summary
    print("\n" + "=" * 70)
    print("Build Summary")
    print("=" * 70)

    successful = 0
    failed = 0

    for result in results:
        stack = result["stack"]
        if result["npm_install"] and result["npm_build"]:
            print(f"[OK] {stack}")
            successful += 1
        else:
            print(f"[FAIL] {stack}")
            for error in result["errors"]:
                print(f"  - {error}")
            failed += 1

    print(f"\nResults:")
    print(f"  Successful: {successful}/{len(STACKS)}")
    print(f"  Failed: {failed}/{len(STACKS)}")

    if failed == 0:
        print("\n[SUCCESS] All stacks built successfully!")
        return 0
    else:
        print(f"\n[WARNING] {failed} stack(s) failed to build")
        return 1


if __name__ == "__main__":
    sys.exit(main())
