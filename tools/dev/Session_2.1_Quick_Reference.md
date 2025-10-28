# Session 2.1 Quick Reference

**For:** Session 2 Implementation
**Use:** Session-2.1.md as execution guide
**Date:** 2025-10-21

---

## Critical Fixes Applied

### 1. Stack Structure ✅
```
CORRECT:
./cloud/stacks/network/
├── index.ts              ← AT ROOT!
├── docs/
├── src/                  ← Components only
│   ├── vpc.ts
│   └── subnets.ts
├── Pulumi.yaml
└── package.json
```

### 2. CLI Technology ✅
- **Language:** Python 3.11+ (not TypeScript)
- **Framework:** Typer (not Commander.js)
- **Structure:** Per Directory_Structure_Diagram.3.1.md

### 3. Template Structure ✅
```
CORRECT:
./cloud/tools/templates/stack/
├── index.ts.template     ← AT ROOT!
├── src/
│   └── component.ts.template
├── Pulumi.yaml.template
└── package.json.template
```

---

## Quick Commands

### Pre-Session Check:
```bash
cd /c/Users/Admin/Documents/Workspace
python3 --version  # Need 3.11+
ls -la cloud/tools/docs/*.3.1.md | wc -l  # Should show 16
```

### Create Structure:
```bash
mkdir -p cloud/tools/cli/src/{commands,orchestrator,templates,deployment,runtime,pulumi,validation,utils}
```

### Verify Stack Structure:
```bash
# index.ts should be at root
test -f cloud/stacks/network/index.ts && echo "✓ Correct" || echo "✗ Wrong"
```

### Setup Python CLI:
```bash
cd cloud/tools/cli
python3 -m venv venv
source venv/bin/activate
pip install typer[all] pydantic pyyaml rich pulumi
```

---

## Python CLI Example

```python
# src/main.py
import typer

app = typer.Typer(name="cloud", help="Cloud Platform CLI v0.7")

@app.command()
def init(
    org: str = typer.Option(..., "--org"),
    project: str = typer.Option(..., "--project"),
):
    """Initialize deployment"""
    typer.echo(f"Creating deployment for {org}/{project}")

if __name__ == "__main__":
    app()
```

---

## Key Files

### Use These:
- ✅ Session-2.1.md (execution guide)
- ✅ Directory_Structure_Diagram.3.1.md (authority)
- ✅ Session_2.1_Changes_Summary.md (detailed changes)

### Don't Use:
- ❌ Session-2-Prompt.3.1.IMPROVED.md (superseded)
- ❌ Prompt-12 (historical only)

---

## Working Directory

**Start here:**
```bash
cd /c/Users/Admin/Documents/Workspace
```

**Source:** `/c/Users/Admin/Documents/Workspace/Pulumi-2`
**Destination:** `/c/Users/Admin/Documents/Workspace/cloud`

---

## Technology Stack

### CLI (Python):
- Typer 0.9.0
- Pydantic 2.5.0
- PyYAML 6.0.1
- Rich 13.7.0
- Pulumi 3.98.0

### Stacks (TypeScript):
- Pulumi 3.x
- AWS SDK 6.x
- TypeScript 5.x

---

**Ready to execute Session 2 with Session-2.1.md!**
