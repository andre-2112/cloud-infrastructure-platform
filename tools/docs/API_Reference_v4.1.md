# API Reference - v4.1

**Platform:** cloud-0.7
**Architecture Version:** 4.1
**Document Type:** API Reference
**Date:** 2025-10-29
**Status:** Authoritative

---

## Table of Contents

1. [Introduction](#introduction)
2. [Validation Module](#validation-module)
3. [Template Module](#template-module)
4. [Deployment Module](#deployment-module)
5. [Orchestration Module](#orchestration-module)
6. [Runtime Module](#runtime-module)
7. [Pulumi Module](#pulumi-module)
8. [Utils Module](#utils-module)
9. [Data Structures](#data-structures)
10. [Error Handling](#error-handling)

---

## Introduction

### Purpose

This document provides complete API reference for the cloud-0.7 platform core library (`cloud_core`). All public APIs are documented with signatures, parameters, return types, and examples.

### Module Organization

```
cloud_core/
├── validation/     # Template-first validation, manifest validation
├── templates/      # Template management, parameter extraction
├── deployment/     # Deployment orchestration, config generation
├── orchestrator/   # Dependency resolution, layer calculation
├── runtime/        # Placeholder resolution, stack references
├── pulumi/         # Pulumi wrapper, stack operations
└── utils/          # Logging, file operations, helpers
```

### Type Conventions

- `Path`: `pathlib.Path`
- `Dict`: `typing.Dict`
- `List`: `typing.List`
- `Optional[T]`: `typing.Optional[T]` (value or None)
- `Tuple[A, B]`: `typing.Tuple[A, B]`

---

## Validation Module

**Location:** `cloud_core/validation/`

### StackCodeValidator

Validates that stack TypeScript code matches enhanced template declarations.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 15

#### Constructor

```python
class StackCodeValidator:
    def __init__(self):
        """Initialize the validator"""
```

**Parameters:** None

**Example:**
```python
from cloud_core.validation.stack_code_validator import StackCodeValidator

validator = StackCodeValidator()
```

#### validate()

Validate stack code against template.

```python
def validate(
    self,
    stack_dir: Path,
    template_data: Dict,
    stack_name: Optional[str] = None,
    strict: bool = False
) -> ValidationResult:
```

**Parameters:**
- `stack_dir` (Path): Directory containing stack TypeScript code (e.g., `stacks/network`)
- `template_data` (Dict): Enhanced template with parameter declarations
  ```python
  {
      "name": "network",
      "parameters": {
          "inputs": {
              "vpcCidr": {"type": "string", "required": True, ...}
          },
          "outputs": {
              "vpcId": {"type": "string", ...}
          }
      }
  }
  ```
- `stack_name` (Optional[str]): Stack name (defaults to `stack_dir.name`)
- `strict` (bool): Enable strict validation mode (default: `False`)

**Returns:** `ValidationResult`
- `valid` (bool): Overall validation status
- `errors` (List[ValidationIssue]): List of errors (violations)
- `warnings` (List[ValidationIssue]): List of warnings (inconsistencies)
- `stack_name` (str): Name of validated stack

**Raises:**
- `Exception`: If parameter extraction fails or stack directory not found

**Behavior:**

| Condition | Non-Strict | Strict |
|-----------|-----------|--------|
| Undeclared input (used but not in template) | ERROR | ERROR |
| Unused input (in template but not used) | WARNING | ERROR |
| Missing output (in template but not exported) | ERROR | ERROR |
| Extra output (exported but not in template) | WARNING | ERROR |
| Type mismatch (code vs template) | WARNING | WARNING |
| Required/optional mismatch | WARNING | WARNING |
| Secret flag mismatch | WARNING | WARNING |

**Example:**
```python
from pathlib import Path
from cloud_core.validation.stack_code_validator import StackCodeValidator
from cloud_core.templates.stack_template_manager import StackTemplateManager

# Load template
template_manager = StackTemplateManager()
template = template_manager.load_template("network")

# Validate
validator = StackCodeValidator()
result = validator.validate(
    stack_dir=Path("stacks/network"),
    template_data=template,
    stack_name="network",
    strict=False
)

# Check result
if not result.valid:
    print(f"Validation failed with {result.get_error_count()} errors")
    for error in result.errors:
        print(f"  ERROR: {error.message} [{error.location}]")

if result.warnings:
    print(f"Found {result.get_warning_count()} warnings")
    for warning in result.warnings:
        print(f"  WARNING: {warning.message} [{warning.location}]")
```

#### validate_multiple_stacks()

Validate multiple stacks.

```python
def validate_multiple_stacks(
    self,
    stacks_base_dir: Path,
    templates: Dict[str, Dict],
    strict: bool = False
) -> Dict[str, ValidationResult]:
```

**Parameters:**
- `stacks_base_dir` (Path): Base directory containing stack directories (e.g., `stacks/`)
- `templates` (Dict[str, Dict]): Dictionary mapping stack names to template data
  ```python
  {
      "network": {template data},
      "security": {template data},
      ...
  }
  ```
- `strict` (bool): Enable strict validation mode

**Returns:** `Dict[str, ValidationResult]`
- Dictionary mapping stack names to their validation results

**Example:**
```python
templates = {
    "network": template_manager.load_template("network"),
    "security": template_manager.load_template("security")
}

results = validator.validate_multiple_stacks(
    stacks_base_dir=Path("stacks"),
    templates=templates,
    strict=True
)

for stack_name, result in results.items():
    if not result.valid:
        print(f"{stack_name}: FAILED")
    else:
        print(f"{stack_name}: PASSED")
```

#### validate_deployment()

Validate all stacks in a deployment manifest.

```python
def validate_deployment(
    self,
    stacks_base_dir: Path,
    manifest: Dict,
    strict: bool = False
) -> Tuple[bool, Dict[str, ValidationResult]]:
```

**Parameters:**
- `stacks_base_dir` (Path): Base directory containing stack directories
- `manifest` (Dict): Deployment manifest with stack configurations
  ```python
  {
      "environment": "dev",
      "stacks": {
          "network": {"enabled": True, "config": {...}},
          "security": {"enabled": True, "config": {...}}
      }
  }
  ```
- `strict` (bool): Enable strict validation mode

**Returns:** `Tuple[bool, Dict[str, ValidationResult]]`
- First element: `True` if all enabled stacks are valid, `False` otherwise
- Second element: Dictionary of validation results per stack

**Example:**
```python
with open("deploy/dev/manifest.yaml") as f:
    manifest = yaml.safe_load(f)

all_valid, results = validator.validate_deployment(
    stacks_base_dir=Path("stacks"),
    manifest=manifest,
    strict=True
)

if all_valid:
    print("✓ All stacks in deployment are valid")
else:
    print("✗ Some stacks have validation errors:")
    for name, result in results.items():
        if not result.valid:
            print(f"  - {name}: {result.get_error_count()} errors")
```

#### format_validation_result()

Format validation result as human-readable string.

```python
def format_validation_result(self, result: ValidationResult) -> str:
```

**Parameters:**
- `result` (ValidationResult): Validation result to format

**Returns:** `str`
- Formatted multi-line string

**Output Format:**
```
Stack: network
✓ Validation passed
```

Or with errors:
```
Stack: network

✗ 2 Error(s):
  - Input 'invalidParam' is used in code but not declared in template [input:invalidParam]
  - Output 'vpcId' is declared in template but not exported in code [output:vpcId]

⚠ 1 Warning(s):
  - Input 'enableNatGateway' is declared in template but not used in code [input:enableNatGateway]
```

**Example:**
```python
result = validator.validate(stack_dir, template)
output = validator.format_validation_result(result)
print(output)
```

#### format_multiple_results()

Format multiple validation results.

```python
def format_multiple_results(
    self,
    results: Dict[str, ValidationResult]
) -> str:
```

**Parameters:**
- `results` (Dict[str, ValidationResult]): Dictionary of validation results

**Returns:** `str`
- Formatted report with summary and per-stack details

**Example:**
```python
results = validator.validate_multiple_stacks(stacks_base_dir, templates)
report = validator.format_multiple_results(results)
print(report)
```

---

### ValidationResult

Data class representing validation result.

**Location:** `cloud_core.validation.stack_code_validator`

#### Structure

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    stack_name: Optional[str] = None
```

#### Methods

##### add_error()

Add an error to the result.

```python
def add_error(self, message: str, location: Optional[str] = None):
```

**Parameters:**
- `message` (str): Error message
- `location` (Optional[str]): Location reference (e.g., `"input:vpcCidr"`, `"line:42"`)

**Side Effects:**
- Adds error to `errors` list
- Sets `valid` to `False`

**Example:**
```python
result = ValidationResult(valid=True)
result.add_error(
    "Input 'vpcCidr' is used in code but not declared in template",
    location="input:vpcCidr"
)
# Now: result.valid == False, len(result.errors) == 1
```

##### add_warning()

Add a warning to the result.

```python
def add_warning(self, message: str, location: Optional[str] = None):
```

**Parameters:**
- `message` (str): Warning message
- `location` (Optional[str]): Location reference

**Side Effects:**
- Adds warning to `warnings` list
- Does NOT change `valid` status

**Example:**
```python
result = ValidationResult(valid=True)
result.add_warning(
    "Input 'enableNatGateway' is declared but not used",
    location="input:enableNatGateway"
)
# Now: result.valid == True, len(result.warnings) == 1
```

##### has_issues()

Check if there are any issues (errors or warnings).

```python
def has_issues(self) -> bool:
```

**Returns:** `bool`
- `True` if there are any errors or warnings
- `False` if clean validation

**Example:**
```python
if result.has_issues():
    print("Validation has issues to review")
```

##### get_error_count()

Get number of errors.

```python
def get_error_count(self) -> int:
```

**Returns:** `int` - Number of errors

##### get_warning_count()

Get number of warnings.

```python
def get_warning_count(self) -> int:
```

**Returns:** `int` - Number of warnings

---

### ValidationIssue

Data class representing a single validation issue.

**Location:** `cloud_core.validation.stack_code_validator`

#### Structure

```python
@dataclass
class ValidationIssue:
    severity: str  # "error" or "warning"
    message: str
    location: Optional[str] = None
```

**Fields:**
- `severity` (str): `"error"` or `"warning"`
- `message` (str): Human-readable issue description
- `location` (Optional[str]): Location reference (e.g., `"input:vpcCidr"`, `"output:vpcId"`)

**Example:**
```python
issue = ValidationIssue(
    severity="error",
    message="Input 'vpcCidr' is used in code but not declared in template",
    location="input:vpcCidr"
)

print(f"{issue.severity.upper()}: {issue.message} [{issue.location}]")
# Output: ERROR: Input 'vpcCidr' is used in code but not declared in template [input:vpcCidr]
```

---

## Template Module

**Location:** `cloud_core/templates/`

### ParameterExtractor

Extracts parameters from stack TypeScript code.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 14

#### Constructor

```python
class ParameterExtractor:
    def __init__(self):
        """Initialize the extractor"""
```

#### extract_from_stack()

Extract parameters from a stack directory.

```python
def extract_from_stack(
    self,
    stack_dir: Path,
    stack_name: Optional[str] = None
) -> Dict:
```

**Parameters:**
- `stack_dir` (Path): Path to stack directory containing TypeScript code
- `stack_name` (Optional[str]): Stack name (defaults to directory name)

**Returns:** `Dict`

**Success Response:**
```python
{
    "success": True,
    "stack_name": "network",
    "source_file": "/path/to/stacks/network/index.ts",
    "parameters": {
        "inputs": {
            "vpcCidr": {
                "type": "string",
                "required": True,
                "secret": False,
                "default": "10.0.0.0/16",  # If found in code
                "description": "..."        # If found in comments
            },
            ...
        },
        "outputs": {
            "vpcId": {
                "type": "string",
                "description": "..."  # If found in comments
            },
            ...
        }
    },
    "warnings": [...]  # List of extraction warnings
}
```

**Failure Response:**
```python
{
    "success": False,
    "error": "No TypeScript file found in /path/to/stack",
    "errors": [...]  # List of parse errors
}
```

**TypeScript Patterns Recognized:**

**Inputs (Config access):**
```typescript
// Recognized patterns:
const config = new pulumi.Config();

config.require("paramName")        // type: string, required: true
config.requireSecret("apiKey")     // type: string, required: true, secret: true
config.get("optional")             // type: string, required: false
config.getNumber("count")          // type: number, required: false
config.requireNumber("zones")      // type: number, required: true
config.getBoolean("enabled")       // type: boolean, required: false
config.getObject("settings")       // type: object, required: false
```

**Outputs (exports):**
```typescript
// Recognized patterns:
export const vpcId = vpc.id;                    // type: string
export const subnetIds = subnets.map(s => s.id); // type: array
```

**File Discovery Order:**
1. `index.ts` (preferred)
2. `<stack-name>.ts`
3. First `.ts` file found

**Example:**
```python
from pathlib import Path
from cloud_core.templates.parameter_extractor import ParameterExtractor

extractor = ParameterExtractor()
result = extractor.extract_from_stack(
    stack_dir=Path("stacks/network"),
    stack_name="network"
)

if result["success"]:
    params = result["parameters"]
    print(f"Found {len(params['inputs'])} inputs:")
    for name, config in params["inputs"].items():
        print(f"  - {name}: {config['type']}, required={config['required']}")

    print(f"Found {len(params['outputs'])} outputs:")
    for name, config in params["outputs"].items():
        print(f"  - {name}: {config['type']}")
else:
    print(f"Extraction failed: {result['error']}")
```

#### extract_from_multiple_stacks()

Extract parameters from multiple stacks.

```python
def extract_from_multiple_stacks(
    self,
    stacks_base_dir: Path,
    stack_names: Optional[List[str]] = None
) -> Dict[str, Dict]:
```

**Parameters:**
- `stacks_base_dir` (Path): Base directory containing stack directories
- `stack_names` (Optional[List[str]]): List of stack names to process (defaults to all subdirectories)

**Returns:** `Dict[str, Dict]`
- Dictionary mapping stack names to extraction results

**Example:**
```python
results = extractor.extract_from_multiple_stacks(
    stacks_base_dir=Path("stacks"),
    stack_names=["network", "security", "database-rds"]
)

for stack_name, result in results.items():
    if result["success"]:
        print(f"✓ {stack_name}: extracted successfully")
    else:
        print(f"✗ {stack_name}: {result['error']}")
```

#### generate_template_file()

Generate a template YAML file from stack code.

```python
def generate_template_file(
    self,
    stack_dir: Path,
    output_path: Path,
    stack_name: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
```

**Parameters:**
- `stack_dir` (Path): Path to stack directory
- `output_path` (Path): Where to write the template YAML file
- `stack_name` (Optional[str]): Stack name

**Returns:** `Tuple[bool, Optional[str]]`
- First element: `True` if successful, `False` otherwise
- Second element: Error message if failed, `None` if successful

**Generated Template Structure:**
```yaml
name: network
parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for VPC"
  outputs:
    vpcId:
      type: string
      description: "VPC ID for cross-stack references"
```

**Example:**
```python
success, error = extractor.generate_template_file(
    stack_dir=Path("stacks/network"),
    output_path=Path("tools/templates/config/network.yaml"),
    stack_name="network"
)

if success:
    print("✓ Template generated successfully")
else:
    print(f"✗ Failed to generate template: {error}")
```

#### compare_with_template()

Compare extracted parameters with existing template.

```python
def compare_with_template(
    self,
    stack_dir: Path,
    template_path: Path,
    stack_name: Optional[str] = None
) -> Dict:
```

**Parameters:**
- `stack_dir` (Path): Path to stack directory
- `template_path` (Path): Path to existing template YAML
- `stack_name` (Optional[str]): Stack name

**Returns:** `Dict`

**Success Response:**
```python
{
    "success": True,
    "differences": {
        "missing_in_template": ["input:newParam", "output:newOutput"],
        "missing_in_code": ["input:unusedParam"],
        "type_mismatches": [
            {
                "parameter": "input:count",
                "code_type": "number",
                "template_type": "string"
            }
        ],
        "matches": ["input:vpcCidr", "output:vpcId"]
    },
    "is_synchronized": False  # True if no differences
}
```

**Failure Response:**
```python
{
    "success": False,
    "error": "Failed to load template: ..."
}
```

**Example:**
```python
comparison = extractor.compare_with_template(
    stack_dir=Path("stacks/network"),
    template_path=Path("tools/templates/config/network.yaml"),
    stack_name="network"
)

if comparison["success"]:
    if comparison["is_synchronized"]:
        print("✓ Code and template are synchronized")
    else:
        diff = comparison["differences"]
        if diff["missing_in_template"]:
            print("Parameters in code but not in template:")
            for param in diff["missing_in_template"]:
                print(f"  - {param}")

        if diff["missing_in_code"]:
            print("Parameters in template but not in code:")
            for param in diff["missing_in_code"]:
                print(f"  - {param}")

        if diff["type_mismatches"]:
            print("Type mismatches:")
            for mismatch in diff["type_mismatches"]:
                print(f"  - {mismatch['parameter']}: "
                      f"code={mismatch['code_type']}, "
                      f"template={mismatch['template_type']}")
```

---

### StackTemplateManager

Manages loading and accessing stack templates.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 6-7

#### Constructor

```python
class StackTemplateManager:
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager

        Args:
            templates_dir: Custom templates directory
                          (defaults to tools/templates/config)
        """
```

**Example:**
```python
from cloud_core.templates.stack_template_manager import StackTemplateManager

# Use default location (tools/templates/config)
manager = StackTemplateManager()

# Or custom location
manager = StackTemplateManager(templates_dir=Path("/custom/templates"))
```

#### load_template()

Load a stack template.

```python
def load_template(self, stack_name: str) -> Dict:
```

**Parameters:**
- `stack_name` (str): Stack name (without `.yaml` extension)

**Returns:** `Dict`
- Complete template data structure

**Raises:**
- `FileNotFoundError`: If template file doesn't exist
- `yaml.YAMLError`: If template YAML is invalid

**Example:**
```python
try:
    template = manager.load_template("network")
    print(f"Loaded template: {template['name']}")
    print(f"Version: {template.get('version', 'unknown')}")
    print(f"Inputs: {len(template['parameters']['inputs'])}")
    print(f"Outputs: {len(template['parameters']['outputs'])}")
except FileNotFoundError:
    print("Template not found. Register stack first.")
except yaml.YAMLError as e:
    print(f"Invalid template YAML: {e}")
```

#### template_exists()

Check if a template exists.

```python
def template_exists(self, stack_name: str) -> bool:
```

**Parameters:**
- `stack_name` (str): Stack name

**Returns:** `bool`
- `True` if template file exists, `False` otherwise

**Example:**
```python
if manager.template_exists("network"):
    template = manager.load_template("network")
else:
    print("Template not found. Run: cloud register-stack network --auto-extract")
```

#### list_templates()

List all available templates.

```python
def list_templates(self) -> List[str]:
```

**Returns:** `List[str]`
- List of stack names (without `.yaml` extension)

**Example:**
```python
templates = manager.list_templates()
print(f"Available templates: {', '.join(templates)}")

for stack_name in templates:
    template = manager.load_template(stack_name)
    print(f"  {stack_name}: layer {template.get('layer', '?')}")
```

#### save_template()

Save a template to file.

```python
def save_template(self, template: Dict, stack_name: str) -> None:
```

**Parameters:**
- `template` (Dict): Template data to save
- `stack_name` (str): Stack name (determines filename)

**Raises:**
- `OSError`: If file cannot be written

**Example:**
```python
template = {
    "name": "my-stack",
    "version": "1.0",
    "description": "My custom stack",
    "parameters": {
        "inputs": {...},
        "outputs": {...}
    },
    "dependencies": [],
    "layer": 1
}

manager.save_template(template, "my-stack")
# Writes to: tools/templates/config/my-stack.yaml
```

---

## Deployment Module

**Location:** `cloud_core/deployment/`

### ConfigGenerator

Generates Pulumi configuration files from deployment manifests.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 13

#### Constructor

```python
class ConfigGenerator:
    def __init__(self, deployment_dir: Path):
        """
        Initialize config generator

        Args:
            deployment_dir: Deployment directory (e.g., deploy/dev)
        """
```

#### generate_stack_config()

Generate Pulumi config for a single stack.

```python
def generate_stack_config(
    self,
    stack_name: str,
    stack_config: Dict,
    base_config: Dict,
    project_name: str,
    environment: str
) -> Dict[str, str]:
```

**Parameters:**
- `stack_name` (str): Stack name (e.g., `"network"`)
- `stack_config` (Dict): Stack-specific config from manifest
- `base_config` (Dict): Base/default configuration
- `project_name` (str): Pulumi project name
- `environment` (str): Environment name (e.g., `"dev"`)

**Returns:** `Dict[str, str]`
- Dictionary in Pulumi native format: `{"network:vpcCidr": "10.0.0.0/16", ...}`

**Config Tier Resolution:**
1. Stack-specific config (highest priority)
2. Environment config
3. Base defaults (lowest priority)

**Example:**
```python
from cloud_core.deployment.config_generator import ConfigGenerator

generator = ConfigGenerator(Path("deploy/dev"))

stack_config = {
    "vpcCidr": "10.0.0.0/16",
    "availabilityZones": "3"
}

base_config = {
    "aws:region": "us-east-1",
    "enableLogging": "true"
}

config = generator.generate_stack_config(
    stack_name="network",
    stack_config=stack_config,
    base_config=base_config,
    project_name="myproject",
    environment="dev"
)

# Result:
# {
#     "network:vpcCidr": "10.0.0.0/16",
#     "network:availabilityZones": "3",
#     "aws:region": "us-east-1",
#     "network:enableLogging": "true"
# }
```

#### generate_all_configs()

Generate configs for all stacks in manifest.

```python
def generate_all_configs(
    self,
    manifest: Dict,
    project_name: str
) -> Dict[str, Dict[str, str]]:
```

**Parameters:**
- `manifest` (Dict): Complete deployment manifest
- `project_name` (str): Pulumi project name

**Returns:** `Dict[str, Dict[str, str]]`
- Dictionary mapping stack names to their Pulumi configs

**Example:**
```python
with open("deploy/dev/manifest.yaml") as f:
    manifest = yaml.safe_load(f)

configs = generator.generate_all_configs(
    manifest=manifest,
    project_name="myproject"
)

for stack_name, config in configs.items():
    print(f"Config for {stack_name}:")
    for key, value in config.items():
        print(f"  {key}: {value}")
```

#### write_config_file()

Write Pulumi config file for a stack.

```python
def write_config_file(
    self,
    stack_full_name: str,
    config: Dict[str, str],
    output_dir: Path
) -> Path:
```

**Parameters:**
- `stack_full_name` (str): Full Pulumi stack name (e.g., `"myproject-dev-network"`)
- `config` (Dict[str, str]): Config in Pulumi format
- `output_dir` (Path): Where to write config file

**Returns:** `Path`
- Path to written config file

**Writes:** `output_dir/Pulumi.<stack_full_name>.yaml`

**Example:**
```python
config_path = generator.write_config_file(
    stack_full_name="myproject-dev-network",
    config={"network:vpcCidr": "10.0.0.0/16"},
    output_dir=Path("deploy/dev/config")
)

print(f"Config written to: {config_path}")
# deploy/dev/config/Pulumi.myproject-dev-network.yaml
```

---

### DeploymentManager

Manages deployment orchestration and execution.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 11

#### Constructor

```python
class DeploymentManager:
    def __init__(
        self,
        project_name: str,
        environment: str,
        deployment_dir: Path,
        stacks_dir: Path
    ):
```

**Parameters:**
- `project_name` (str): Pulumi project name
- `environment` (str): Environment name (dev, stage, prod)
- `deployment_dir` (Path): Deployment directory (e.g., `deploy/dev`)
- `stacks_dir` (Path): Base directory containing stack code

#### load_manifest()

Load and parse deployment manifest.

```python
def load_manifest(self) -> Dict:
```

**Returns:** `Dict`
- Parsed manifest data

**Raises:**
- `FileNotFoundError`: If manifest.yaml doesn't exist
- `yaml.YAMLError`: If manifest is invalid

**Example:**
```python
from cloud_core.deployment.deployment_manager import DeploymentManager

manager = DeploymentManager(
    project_name="myproject",
    environment="dev",
    deployment_dir=Path("deploy/dev"),
    stacks_dir=Path("stacks")
)

manifest = manager.load_manifest()
print(f"Environment: {manifest['environment']}")
print(f"Enabled stacks: {len([s for s in manifest['stacks'].values() if s.get('enabled')])}")
```

#### get_enabled_stacks()

Get list of enabled stacks from manifest.

```python
def get_enabled_stacks(self) -> List[str]:
```

**Returns:** `List[str]`
- List of enabled stack names

**Example:**
```python
enabled = manager.get_enabled_stacks()
print(f"Deploying {len(enabled)} stacks: {', '.join(enabled)}")
```

#### calculate_deployment_order()

Calculate deployment order respecting dependencies.

```python
def calculate_deployment_order(self) -> List[List[str]]:
```

**Returns:** `List[List[str]]`
- List of layers, where each layer is a list of stack names that can be deployed in parallel

**Example:**
```python
layers = manager.calculate_deployment_order()

print(f"Deployment will occur in {len(layers)} layers:")
for i, layer in enumerate(layers, 1):
    print(f"  Layer {i}: {', '.join(layer)}")

# Output:
# Deployment will occur in 3 layers:
#   Layer 1: network
#   Layer 2: security, storage-s3
#   Layer 3: database-rds, compute-ecs
```

#### deploy()

Execute full deployment.

```python
def deploy(
    self,
    destroy: bool = False,
    preview: bool = False,
    parallel: bool = True
) -> DeploymentResult:
```

**Parameters:**
- `destroy` (bool): If `True`, destroy instead of deploy
- `preview` (bool): If `True`, preview only (no changes)
- `parallel` (bool): If `True`, deploy stacks in same layer concurrently

**Returns:** `DeploymentResult`
- Result object with status, outputs, and errors

**Example:**
```python
# Preview deployment
result = manager.deploy(preview=True)
if result.success:
    print("Preview successful. Ready to deploy.")

# Execute deployment
result = manager.deploy(parallel=True)
if result.success:
    print("✓ Deployment successful")
    print(f"Deployed {result.stacks_deployed} stacks")
else:
    print(f"✗ Deployment failed: {result.error}")
    for stack_name, error in result.stack_errors.items():
        print(f"  {stack_name}: {error}")
```

---

### StateManager

Manages Pulumi state queries and stack references.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 10.4

#### Constructor

```python
class StateManager:
    def __init__(self, project_name: str, environment: str):
```

**Parameters:**
- `project_name` (str): Pulumi project name
- `environment` (str): Environment name

#### get_stack_output()

Get output value from a deployed stack.

```python
def get_stack_output(
    self,
    stack_name: str,
    output_name: str
) -> Any:
```

**Parameters:**
- `stack_name` (str): Stack name
- `output_name` (str): Output parameter name

**Returns:** `Any`
- Output value (type depends on output)

**Raises:**
- `StackNotFoundError`: If stack doesn't exist
- `OutputNotFoundError`: If output doesn't exist

**Example:**
```python
from cloud_core.deployment.state_manager import StateManager

state = StateManager(project_name="myproject", environment="dev")

# Get VPC ID from network stack
vpc_id = state.get_stack_output("network", "vpcId")
print(f"VPC ID: {vpc_id}")

# Get subnet IDs (array output)
subnet_ids = state.get_stack_output("network", "privateSubnetIds")
print(f"Subnets: {', '.join(subnet_ids)}")
```

#### get_all_stack_outputs()

Get all outputs from a stack.

```python
def get_all_stack_outputs(self, stack_name: str) -> Dict[str, Any]:
```

**Parameters:**
- `stack_name` (str): Stack name

**Returns:** `Dict[str, Any]`
- Dictionary of all output names and values

**Example:**
```python
outputs = state.get_all_stack_outputs("network")
for name, value in outputs.items():
    print(f"{name}: {value}")
```

#### stack_exists()

Check if a stack is deployed.

```python
def stack_exists(self, stack_name: str) -> bool:
```

**Parameters:**
- `stack_name` (str): Stack name

**Returns:** `bool`
- `True` if stack exists in Pulumi state

**Example:**
```python
if state.stack_exists("network"):
    vpc_id = state.get_stack_output("network", "vpcId")
else:
    print("Network stack not deployed yet")
```

---

## Orchestration Module

**Location:** `cloud_core/orchestrator/`

### DependencyResolver

Resolves stack dependencies from templates.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 9

#### Constructor

```python
class DependencyResolver:
    def __init__(self, template_manager: StackTemplateManager):
```

**Parameters:**
- `template_manager` (StackTemplateManager): Template manager instance

#### build_dependency_graph()

Build dependency graph from templates.

```python
def build_dependency_graph(
    self,
    stack_names: List[str]
) -> Dict[str, Set[str]]:
```

**Parameters:**
- `stack_names` (List[str]): List of stack names to include

**Returns:** `Dict[str, Set[str]]`
- Dictionary mapping each stack to its dependencies
  ```python
  {
      "network": set(),
      "security": {"network"},
      "database-rds": {"network", "security"}
  }
  ```

**Example:**
```python
from cloud_core.orchestrator.dependency_resolver import DependencyResolver

resolver = DependencyResolver(template_manager)
graph = resolver.build_dependency_graph(["network", "security", "database-rds"])

for stack, deps in graph.items():
    if deps:
        print(f"{stack} depends on: {', '.join(deps)}")
    else:
        print(f"{stack} has no dependencies")
```

#### detect_circular_dependencies()

Detect circular dependencies in graph.

```python
def detect_circular_dependencies(
    self,
    graph: Dict[str, Set[str]]
) -> Optional[List[str]]:
```

**Parameters:**
- `graph` (Dict[str, Set[str]]): Dependency graph

**Returns:** `Optional[List[str]]`
- List of stacks forming a cycle, or `None` if no cycles

**Example:**
```python
cycle = resolver.detect_circular_dependencies(graph)

if cycle:
    print(f"✗ Circular dependency detected: {' -> '.join(cycle)}")
else:
    print("✓ No circular dependencies")
```

#### validate_dependencies()

Validate all dependencies exist.

```python
def validate_dependencies(
    self,
    stack_names: List[str]
) -> Tuple[bool, List[str]]:
```

**Parameters:**
- `stack_names` (List[str]): Stack names to validate

**Returns:** `Tuple[bool, List[str]]`
- First element: `True` if valid, `False` if missing dependencies
- Second element: List of missing stack names

**Example:**
```python
valid, missing = resolver.validate_dependencies([
    "network", "security", "database-rds"
])

if valid:
    print("✓ All dependencies are available")
else:
    print(f"✗ Missing dependencies: {', '.join(missing)}")
```

---

### LayerCalculator

Calculates deployment layers from dependency graph.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 9.2

#### Constructor

```python
class LayerCalculator:
    def __init__(self):
```

#### calculate_layers()

Calculate deployment layers using topological sort.

```python
def calculate_layers(
    self,
    graph: Dict[str, Set[str]]
) -> List[List[str]]:
```

**Parameters:**
- `graph` (Dict[str, Set[str]]): Dependency graph from DependencyResolver

**Returns:** `List[List[str]]`
- List of layers, ordered for deployment
- Stacks in same layer can be deployed in parallel

**Algorithm:** Kahn's algorithm for topological sorting

**Example:**
```python
from cloud_core.orchestrator.layer_calculator import LayerCalculator

calculator = LayerCalculator()
layers = calculator.calculate_layers(graph)

print(f"Calculated {len(layers)} deployment layers:")
for i, layer in enumerate(layers, 1):
    print(f"  Layer {i} ({len(layer)} stacks): {', '.join(layer)}")

# Output:
# Calculated 4 layers:
#   Layer 1 (1 stack): network
#   Layer 2 (2 stacks): security, storage-s3
#   Layer 3 (2 stacks): database-rds, compute-ecs
#   Layer 4 (1 stack): monitoring
```

#### validate_layer_order()

Validate that layer order respects dependencies.

```python
def validate_layer_order(
    self,
    layers: List[List[str]],
    graph: Dict[str, Set[str]]
) -> bool:
```

**Parameters:**
- `layers` (List[List[str]]): Calculated layers
- `graph` (Dict[str, Set[str]]): Original dependency graph

**Returns:** `bool`
- `True` if layer order is valid

**Example:**
```python
if calculator.validate_layer_order(layers, graph):
    print("✓ Layer order is valid")
else:
    print("✗ Layer order violates dependencies")
```

---

### ExecutionEngine

Executes deployment across layers.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 11

#### Constructor

```python
class ExecutionEngine:
    def __init__(
        self,
        deployment_manager: DeploymentManager,
        parallel: bool = True
    ):
```

**Parameters:**
- `deployment_manager` (DeploymentManager): Deployment manager instance
- `parallel` (bool): Enable parallel execution within layers

#### execute_layers()

Execute deployment layer by layer.

```python
def execute_layers(
    self,
    layers: List[List[str]],
    operation: str = "up"
) -> ExecutionResult:
```

**Parameters:**
- `layers` (List[List[str]]): Deployment layers
- `operation` (str): Pulumi operation (`"up"`, `"preview"`, `"destroy"`)

**Returns:** `ExecutionResult`
- Result with status, timing, and errors

**Example:**
```python
from cloud_core.orchestrator.execution_engine import ExecutionEngine

engine = ExecutionEngine(deployment_manager, parallel=True)
result = engine.execute_layers(layers, operation="up")

if result.success:
    print(f"✓ Deployment completed in {result.total_time:.1f}s")
    print(f"  Stacks deployed: {result.stacks_completed}")
else:
    print(f"✗ Deployment failed")
    print(f"  Stacks completed: {result.stacks_completed}")
    print(f"  Stacks failed: {len(result.failed_stacks)}")
```

---

## Runtime Module

**Location:** `cloud_core/runtime/`

### PlaceholderResolver

Resolves placeholder values in configurations.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 12

#### Constructor

```python
class PlaceholderResolver:
    def __init__(self, state_manager: StateManager):
```

**Parameters:**
- `state_manager` (StateManager): State manager for querying stack outputs

#### resolve()

Resolve placeholders in a value.

```python
def resolve(self, value: str) -> Any:
```

**Parameters:**
- `value` (str): Value potentially containing placeholders

**Returns:** `Any`
- Resolved value (type depends on placeholder)

**Placeholder Syntax:**
- Stack reference: `${stack_name.output_name}`
- AWS query: `${aws:service:query}`
- Environment variable: `${env:VAR_NAME}`

**Example:**
```python
from cloud_core.runtime.placeholder_resolver import PlaceholderResolver

resolver = PlaceholderResolver(state_manager)

# Resolve stack reference
value = "${network.vpcId}"
vpc_id = resolver.resolve(value)
print(f"VPC ID: {vpc_id}")

# Resolve array reference
value = "${network.privateSubnetIds}"
subnet_ids = resolver.resolve(value)
print(f"Subnets: {', '.join(subnet_ids)}")

# Resolve environment variable
value = "${env:AWS_REGION}"
region = resolver.resolve(value)
print(f"Region: {region}")
```

#### resolve_dict()

Resolve all placeholders in a dictionary.

```python
def resolve_dict(self, config: Dict) -> Dict:
```

**Parameters:**
- `config` (Dict): Configuration dictionary with potential placeholders

**Returns:** `Dict`
- Dictionary with all placeholders resolved

**Example:**
```python
config = {
    "vpcId": "${network.vpcId}",
    "subnetIds": "${network.privateSubnetIds}",
    "region": "${env:AWS_REGION}",
    "instanceType": "t3.micro"  # No placeholder
}

resolved = resolver.resolve_dict(config)
# resolved now has actual values instead of placeholder strings
```

---

### StackReferenceResolver

Specialized resolver for cross-stack references.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 10

#### Constructor

```python
class StackReferenceResolver:
    def __init__(self, state_manager: StateManager):
```

#### resolve_reference()

Resolve a stack output reference.

```python
def resolve_reference(
    self,
    reference: str
) -> Any:
```

**Parameters:**
- `reference` (str): Reference in format `"stack_name.output_name"`

**Returns:** `Any`
- Output value

**Raises:**
- `ValueError`: If reference format is invalid
- `StackNotFoundError`: If stack doesn't exist
- `OutputNotFoundError`: If output doesn't exist

**Example:**
```python
from cloud_core.runtime.stack_reference_resolver import StackReferenceResolver

resolver = StackReferenceResolver(state_manager)

# Resolve single reference
vpc_id = resolver.resolve_reference("network.vpcId")

# Resolve array reference
subnet_ids = resolver.resolve_reference("network.privateSubnetIds")
```

---

## Pulumi Module

**Location:** `cloud_core/pulumi/`

### PulumiWrapper

Wrapper for Pulumi CLI operations.

**Architecture Reference:** Multi_Stack_Architecture.4.1.md section 10

#### Constructor

```python
class PulumiWrapper:
    def __init__(
        self,
        project_name: str,
        stack_dir: Path,
        environment: str
    ):
```

**Parameters:**
- `project_name` (str): Pulumi project name
- `stack_dir` (Path): Directory containing Pulumi stack code
- `environment` (str): Environment name

#### up()

Deploy a stack (pulumi up).

```python
def up(
    self,
    stack_name: str,
    config: Dict[str, str],
    preview: bool = False
) -> PulumiResult:
```

**Parameters:**
- `stack_name` (str): Stack name
- `config` (Dict[str, str]): Pulumi configuration
- `preview` (bool): If `True`, preview only (no changes)

**Returns:** `PulumiResult`
- Result with status, outputs, and logs

**Example:**
```python
from cloud_core.pulumi.pulumi_wrapper import PulumiWrapper

pulumi = PulumiWrapper(
    project_name="myproject",
    stack_dir=Path("stacks/network"),
    environment="dev"
)

config = {
    "network:vpcCidr": "10.0.0.0/16",
    "network:availabilityZones": "3",
    "aws:region": "us-east-1"
}

# Preview
result = pulumi.up("network", config, preview=True)
if result.success:
    print(f"Preview: {result.summary}")

# Deploy
result = pulumi.up("network", config, preview=False)
if result.success:
    print("✓ Stack deployed successfully")
    print(f"Outputs: {result.outputs}")
else:
    print(f"✗ Deployment failed: {result.error}")
```

#### destroy()

Destroy a stack (pulumi destroy).

```python
def destroy(
    self,
    stack_name: str,
    preview: bool = False
) -> PulumiResult:
```

**Parameters:**
- `stack_name` (str): Stack name
- `preview` (bool): Preview destruction

**Returns:** `PulumiResult`

**Example:**
```python
result = pulumi.destroy("network", preview=True)
if result.success:
    print(f"Destroy preview: {result.resources_to_delete} resources")

# Confirm and destroy
if confirm("Really destroy?"):
    result = pulumi.destroy("network", preview=False)
```

#### refresh()

Refresh stack state (pulumi refresh).

```python
def refresh(self, stack_name: str) -> PulumiResult:
```

**Example:**
```python
result = pulumi.refresh("network")
if result.success:
    print("✓ State refreshed")
```

---

## Utils Module

**Location:** `cloud_core/utils/`

### Logger

Structured logging for the platform.

#### get_logger()

Get a logger instance for a module.

```python
def get_logger(name: str) -> logging.Logger:
```

**Parameters:**
- `name` (str): Logger name (typically `__name__`)

**Returns:** `logging.Logger`
- Configured logger instance

**Example:**
```python
from cloud_core.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Starting validation")
logger.warning("Template not found")
logger.error("Validation failed", extra={"stack": "network"})
```

---

## Data Structures

### Template Structure

Enhanced template YAML format:

```yaml
name: string                    # Stack name
version: string                 # Template version (optional)
description: string             # Stack description (optional)

parameters:
  inputs:
    <param_name>:
      type: string              # "string" | "number" | "boolean" | "array" | "object"
      required: boolean         # true | false
      default: any              # Default value (optional)
      description: string       # Parameter description (optional)
      secret: boolean           # Mark as secret (optional, default: false)

  outputs:
    <output_name>:
      type: string              # Output type
      description: string       # Output description (optional)

dependencies:                   # List of stack names this depends on
  - stack_name_1
  - stack_name_2

layer: number                   # Deployment layer (calculated or manual)
```

### Manifest Structure

Deployment manifest YAML format:

```yaml
environment: string             # "dev" | "stage" | "prod"
project: string                 # Project name

config:                         # Base configuration (all stacks)
  aws:region: string
  <key>: <value>

stacks:
  <stack_name>:
    enabled: boolean            # true | false
    config:                     # Stack-specific configuration
      <param>: <value>
      <param>: "${reference}"   # Cross-stack reference
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── ValidationError              # Validation failures
├── TemplateError               # Template issues
│   ├── TemplateNotFoundError
│   └── TemplateFormatError
├── DeploymentError             # Deployment failures
│   ├── StackDeploymentError
│   └── DependencyError
├── StateError                  # State management issues
│   ├── StackNotFoundError
│   └── OutputNotFoundError
└── PulumiError                 # Pulumi operation failures
```

### Error Handling Pattern

```python
from cloud_core.validation.stack_code_validator import StackCodeValidator, ValidationError
from cloud_core.utils.logger import get_logger

logger = get_logger(__name__)

try:
    validator = StackCodeValidator()
    result = validator.validate(stack_dir, template)

    if not result.valid:
        # Handle validation failure (not an exception)
        logger.error(f"Validation failed with {result.get_error_count()} errors")
        for error in result.errors:
            logger.error(f"  {error.message}", extra={"location": error.location})
        raise ValidationError("Stack validation failed")

except FileNotFoundError as e:
    logger.error(f"Stack directory not found: {e}")
    raise

except ValidationError as e:
    logger.error(f"Validation error: {e}")
    raise

except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

---

## Complete Usage Example

### End-to-End Stack Lifecycle

```python
from pathlib import Path
from cloud_core.templates.parameter_extractor import ParameterExtractor
from cloud_core.templates.stack_template_manager import StackTemplateManager
from cloud_core.validation.stack_code_validator import StackCodeValidator
from cloud_core.deployment.deployment_manager import DeploymentManager
from cloud_core.utils.logger import get_logger

logger = get_logger(__name__)

# 1. Extract parameters from stack code
logger.info("Extracting parameters...")
extractor = ParameterExtractor()
extraction = extractor.extract_from_stack(
    stack_dir=Path("stacks/network"),
    stack_name="network"
)

if not extraction["success"]:
    logger.error(f"Extraction failed: {extraction['error']}")
    exit(1)

logger.info(f"Extracted {len(extraction['parameters']['inputs'])} inputs, "
           f"{len(extraction['parameters']['outputs'])} outputs")

# 2. Generate template
logger.info("Generating template...")
success, error = extractor.generate_template_file(
    stack_dir=Path("stacks/network"),
    output_path=Path("tools/templates/config/network.yaml"),
    stack_name="network"
)

if not success:
    logger.error(f"Template generation failed: {error}")
    exit(1)

# 3. Load template
logger.info("Loading template...")
template_manager = StackTemplateManager()
template = template_manager.load_template("network")
logger.info(f"Loaded template: {template['name']} v{template.get('version', 'unknown')}")

# 4. Validate code matches template
logger.info("Validating stack...")
validator = StackCodeValidator()
result = validator.validate(
    stack_dir=Path("stacks/network"),
    template_data=template,
    stack_name="network",
    strict=True
)

if not result.valid:
    logger.error("Validation failed:")
    print(validator.format_validation_result(result))
    exit(1)

logger.info("✓ Validation passed")

# 5. Deploy
logger.info("Deploying stack...")
deployment_manager = DeploymentManager(
    project_name="myproject",
    environment="dev",
    deployment_dir=Path("deploy/dev"),
    stacks_dir=Path("stacks")
)

# Preview first
deploy_result = deployment_manager.deploy(preview=True)
if not deploy_result.success:
    logger.error(f"Preview failed: {deploy_result.error}")
    exit(1)

logger.info("Preview successful")

# Confirm and deploy
if input("Deploy? (y/n): ").lower() == 'y':
    deploy_result = deployment_manager.deploy(parallel=True)
    if deploy_result.success:
        logger.info("✓ Deployment successful")
        logger.info(f"Deployed {deploy_result.stacks_deployed} stacks in "
                   f"{deploy_result.total_time:.1f}s")
    else:
        logger.error(f"✗ Deployment failed: {deploy_result.error}")
        exit(1)
```

---

**Document Version:** 4.1
**Last Updated:** 2025-10-29
**Status:** Authoritative API Reference
**Completeness:** Core modules documented

**Note:** This API reference documents the core library (`cloud_core`). For CLI commands, see CLI_Commands_Reference.3.1.md.

**Maintainers:** Platform Development Team
**Questions:** Open GitHub issue or contact platform-team@example.com
