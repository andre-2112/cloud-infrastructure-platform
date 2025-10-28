# Session 5 - Pulumi Interface Setup (After CLI Completion)

**When:** After all 25+ CLI commands are implemented and tested
**Time Required:** 30 minutes
**Purpose:** Prepare for future Automation API migration

---

## Prerequisites

Before doing this:
- ✅ All CLI commands implemented (25+ commands)
- ✅ All CLI tests passing (40+ unit tests)
- ✅ CLI is stable and working
- ✅ Session 4 marked as complete

---

## Quick Setup (3 Steps)

### 1. Create Interface File

**File:** `cloud/tools/cli/src/cloud_cli/pulumi/interface.py` (NEW)

```python
"""Pulumi Backend Interface - defines contract for CLI and Automation API backends"""

from typing import Protocol, Dict, Any, Optional, Callable
from pathlib import Path

class IPulumiBackend(Protocol):
    """Interface that both CLI wrapper and Automation API must implement"""

    def select_stack(self, stack_name: str, create: bool = True, cwd: Optional[Path] = None) -> None:
        ...

    def set_config(self, key: str, value: str, secret: bool = False, cwd: Optional[Path] = None) -> None:
        ...

    def up(
        self,
        cwd: Optional[Path] = None,
        preview: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        ...

    def destroy(self, cwd: Optional[Path] = None, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        ...

    def get_outputs(self, stack_name: str, cwd: Optional[Path] = None) -> Dict[str, Any]:
        ...

    def preview(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        ...

    def refresh(self, cwd: Optional[Path] = None) -> None:
        ...
```

### 2. Add Note to PulumiWrapper

**File:** `cloud/tools/cli/src/cloud_cli/pulumi/pulumi_wrapper.py` (UPDATE docstring)

```python
class PulumiWrapper:
    """
    Wrapper for Pulumi operations using CLI subprocess calls.

    Future Enhancement: Will support Automation API backend in next session.
    See: pulumi/interface.py and tools/docs/Pulumi_Integration_Analysis.md
    """
```

### 3. Export Interface

**File:** `cloud/tools/cli/src/cloud_cli/pulumi/__init__.py` (ADD one line)

```python
from .interface import IPulumiBackend

__all__ = ["PulumiWrapper", "PulumiError", "IPulumiBackend"]
```

---

## Done!

**Now you can:**
- Mark Session 4 (CLI) as complete ✅
- Start Session 5 (REST API) or Session 6 (Automation API refactor)

**For Automation API implementation later:**
- See: `tools/docs/Pulumi_Integration_Analysis.md` (detailed plan)
- Estimated effort: 8-10 days
- Non-breaking: Current CLI keeps working

---

**Version:** 1.0 (Post-CLI)
**Time:** 30 minutes
**Breaking Changes:** None
