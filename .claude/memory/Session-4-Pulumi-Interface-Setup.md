# Session 4 - Pulumi Interface Setup (Option C)

**Time Required:** 30 minutes
**Purpose:** Define interface for future Automation API migration without changing current code

---

## What to Do

### 1. Create Interface File (20 minutes)

**File:** `cloud/tools/cli/src/cloud_cli/pulumi/interface.py` (NEW)

```python
"""Pulumi Backend Interface - defines contract for CLI and Automation API backends"""

from typing import Protocol, Dict, Any, Optional, Callable
from pathlib import Path

class IPulumiBackend(Protocol):
    """Interface that both CLI wrapper and Automation API must implement"""

    def select_stack(self, stack_name: str, create: bool = True, cwd: Optional[Path] = None) -> None:
        """Select (and optionally create) a Pulumi stack"""
        ...

    def set_config(self, key: str, value: str, secret: bool = False, cwd: Optional[Path] = None) -> None:
        """Set configuration value for selected stack"""
        ...

    def up(
        self,
        cwd: Optional[Path] = None,
        preview: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Deploy stack - returns {"summary": {...}, "outputs": {...}}"""
        ...

    def destroy(self, cwd: Optional[Path] = None, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Destroy stack - returns summary"""
        ...

    def get_outputs(self, stack_name: str, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Get outputs from deployed stack"""
        ...

    def preview(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Preview changes without applying"""
        ...

    def refresh(self, cwd: Optional[Path] = None) -> None:
        """Refresh stack state from cloud provider"""
        ...
```

### 2. Update Existing File (10 minutes)

**File:** `cloud/tools/cli/src/cloud_cli/pulumi/pulumi_wrapper.py` (UPDATE)

Add to the top of `PulumiWrapper` class docstring:

```python
class PulumiWrapper:
    """
    Wrapper for Pulumi operations using CLI subprocess calls.

    NOTE: Implements IPulumiBackend interface (conceptually).
    Session 5 will refactor this to support both CLI and Automation API backends.
    Current code will continue to work without changes.

    See: pulumi/interface.py for the interface definition
    See: tools/docs/Pulumi_Integration_Analysis.md for migration plan
    """
```

### 3. Update Module Exports

**File:** `cloud/tools/cli/src/cloud_cli/pulumi/__init__.py` (UPDATE)

Add this line:
```python
from .interface import IPulumiBackend

__all__ = ["PulumiWrapper", "PulumiError", "IPulumiBackend"]
```

---

## That's It!

**What Changed:**
- ✅ Interface defined (guides future refactoring)
- ✅ Current code documented (notes future migration)

**What Did NOT Change:**
- ❌ No changes to PulumiWrapper implementation
- ❌ No changes to how orchestrator uses it
- ❌ No changes to commands
- ❌ All tests still pass

**Now:** Continue with the 21 remaining CLI commands

**Later (Session 5):** Use this interface to add Automation API backend

---

**Document Version:** 2.0
**Time Required:** 30 minutes
**Breaking Changes:** None
