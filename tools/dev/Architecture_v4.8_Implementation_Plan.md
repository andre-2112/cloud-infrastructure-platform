# Architecture v4.8 - Implementation Plan

**Version:** 4.8
**Date:** 2025-10-31
**Status:** Implementation Plan

## Overview

Architecture v4.8 introduces enhanced user experience features focusing on:
1. Name sanitization for organization and project names
2. Configurable output verbosity (short/verbose modes)
3. Interactive CLI modes for improved usability
4. Rich terminal UI for configuration management

## Features

### 1. Name Sanitization ✅ COMPLETED

**Status:** Implemented and Tested
**Module:** `cloud_core.utils.name_sanitizer`

Automatically sanitizes organization and project names by:
- Replacing consecutive spaces and special characters with single underscore
- Preserving alphanumeric characters and case
- Trimming leading/trailing underscores

**Testing:** 29 unit tests, 4 integration tests (100% pass rate)

### 2. Output Verbosity Control

**Goal:** Provide concise output by default, with verbose option for detailed information

**Implementation:**

#### 2.1 Output Modes
- **Short Mode (Default)**: Minimal, essential output only
  - Success/error status
  - Key resource identifiers
  - Critical warnings only
- **Verbose Mode**: Current detailed output
  - Full resource details
  - All warnings and info messages
  - Step-by-step progress

#### 2.2 CLI Interface
```python
# Add to commands: init, deploy, destroy
quiet: bool = typer.Option(
    False, "--quiet", "-q",
    help="Minimal output (default)"
)
verbose: bool = typer.Option(
    False, "--verbose", "-v",
    help="Detailed output"
)
```

#### 2.3 Affected Commands
- `cloud init` - deployment creation
- `cloud deploy` - stack deployment
- `cloud destroy` - resource cleanup

#### 2.4 Implementation Strategy
1. Create OutputFormatter utility class
2. Support three levels: quiet, normal, verbose
3. Use Rich console for formatting
4. Conditional message output based on level

### 3. Interactive Mode for `cloud init`

**Goal:** Guide users through deployment creation with prompts

**Implementation:**

#### 3.1 Flow
```
Welcome to Cloud Infrastructure Orchestration Platform!

Let's create a new deployment.

? Deployment ID (auto-generate): [D******]
? Organization name: ___
? Project name: ___
? Primary domain: ___
? Pulumi organization: [andre-2112]
? Template: [default] ▼
  - default
  - minimal
  - full-stack
? AWS Region: [us-east-1] ▼
? Dev AWS Account ID: ___

✓ Deployment created successfully!
```

#### 3.2 Features
- Auto-generate deployment ID if skipped
- Show sanitization warnings inline
- Dropdown for templates (from available)
- Dropdown for regions (common AWS regions)
- Validate inputs before proceeding
- Allow Ctrl+C to cancel

#### 3.3 CLI Flags Override
- If any flag provided via CLI, skip that prompt
- `--non-interactive` flag to disable prompts entirely

#### 3.4 Implementation Strategy
1. Add `--interactive/-i` flag to init command
2. Make interactive mode opt-in initially
3. Use `rich.prompt` for inputs
4. Use `Prompt.ask()` for text
5. Use `Confirm.ask()` for boolean
6. Integrate with existing init logic

### 4. Interactive Mode for `cloud config`

**Goal:** Simple interface to enable/disable stacks and environments

**Implementation:**

#### 4.1 Command Structure
```bash
cloud config <deployment-id>
```

#### 4.2 Flow
```
Configuration for Deployment: DYULPQM

What would you like to configure?
1. Enable/disable stacks
2. Enable/disable environments
3. Both
4. Exit

Choice [1-4]: 1

Select stacks to ENABLE (space to select, enter to confirm):
[ ] network
[ ] security
[x] dns
[ ] storage
[ ] database-rds

Select environments to deploy to:
[x] dev
[ ] stage
[ ] prod

✓ Configuration updated!
```

#### 4.3 Implementation Strategy
1. Create new `config_cmd.py` command
2. Use checkbox-style selection
3. Load current manifest
4. Show current state
5. Allow multi-select
6. Update manifest with changes
7. Validate before saving

### 5. Rich Interactive Table for `cloud config`

**Goal:** Visual grid interface for stack/environment configuration

**Implementation:**

#### 5.1 UI Layout
```
┌─────────────────────────────────────────────────────────┐
│  Configure Stacks for Deployment: DYULPQM              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Stack            │ dev  │ stage │ prod  │ Enabled    │
│  ─────────────────┼──────┼───────┼───────┼────────────│
│  network          │  ☑   │  ☐    │  ☐    │    ☑       │
│  security         │  ☐   │  ☐    │  ☐    │    ☐       │
│  dns              │  ☑   │  ☐    │  ☐    │    ☑       │
│  storage          │  ☐   │  ☐    │  ☐    │    ☐       │
│  database-rds     │  ☑   │  ☐    │  ☐    │    ☑       │
│                                                         │
│  [s] Save  [c] Cancel  [a] Enable All  [n] Disable All│
└─────────────────────────────────────────────────────────┘
```

#### 5.2 Interaction Model
- Arrow keys to navigate
- Space to toggle checkbox
- Tab to move between columns
- Enter to confirm selection
- Keyboard shortcuts for actions

#### 5.3 Implementation Strategy
1. Use `rich.table` for rendering
2. Use `rich.live` for updates (simple refresh, not real-time)
3. Capture keyboard input
4. Update selection state
5. Re-render table on changes
6. Save to manifest on confirmation

#### 5.4 Library Decision
- Primary: `rich` (already installed)
- Fallback: Simple terminal with blessed or curses
- **No external dependencies** if possible

### 6. Documentation

**Goal:** Comprehensive documentation of v4.8 features

**Deliverables:**
1. Architecture addendum document
2. User guide updates
3. CLI help text updates
4. Code documentation

## File Structure

```
cloud/
├── tools/
│   ├── core/
│   │   └── cloud_core/
│   │       ├── utils/
│   │       │   ├── name_sanitizer.py ✅
│   │       │   └── output_formatter.py (NEW)
│   │       └── ui/
│   │           ├── __init__.py (NEW)
│   │           ├── interactive.py (NEW)
│   │           └── table_config.py (NEW)
│   ├── cli/
│   │   └── src/cloud_cli/
│   │       └── commands/
│   │           ├── init_cmd.py (MODIFIED)
│   │           ├── deploy_cmd.py (MODIFIED)
│   │           ├── destroy_cmd.py (MODIFIED)
│   │           └── config_cmd.py (NEW)
│   └── docs/
│       ├── Architecture_v4.8_Implementation_Plan.md (THIS FILE)
│       └── Architecture_v4.8_User_Features.md (NEW)
```

## Implementation Phases

### Phase 1: Core Utilities
1. OutputFormatter class
2. Interactive prompt utilities
3. Table configuration utilities

### Phase 2: Output Modes
1. Add flags to init/deploy/destroy
2. Implement OutputFormatter integration
3. Test output modes

### Phase 3: Interactive Init
1. Add interactive flag
2. Implement prompt flow
3. Integrate with existing logic
4. Test interactive mode

### Phase 4: Simple Config Interface
1. Create config command
2. Implement checkbox selection
3. Manifest update logic
4. Test config changes

### Phase 5: Rich Config Interface
1. Implement table rendering
2. Add keyboard navigation
3. Integration with manifest
4. Test full workflow

### Phase 6: Testing & Documentation
1. Unit tests for new utilities
2. Integration tests for commands
3. End-to-end testing
4. Documentation updates

## Testing Strategy

### Unit Tests
- OutputFormatter: 10 tests
- Interactive prompts: 5 tests
- Table config: 8 tests

### Integration Tests
- Init command: 6 tests (existing + 3 new)
- Deploy command: 3 tests (existing + 1 new)
- Config command: 10 tests (new)

### End-to-End Tests
- Complete init workflow
- Complete config workflow
- Output mode variations

## Success Criteria

✅ All features implemented
✅ All tests passing (100%)
✅ Documentation complete
✅ User experience validated
✅ Backward compatibility maintained
