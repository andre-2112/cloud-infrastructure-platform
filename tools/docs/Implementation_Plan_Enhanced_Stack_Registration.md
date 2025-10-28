# ONE-SHOT Implementation Plan: Enhanced Stack Registration System

**Target Document:** Stack_Parameters_and_Registration_Guide.md - All Recommended Enhancements
**Execution Mode:** CONTINUOUS - DO NOT STOP UNTIL 100% COMPLETE
**Estimated Duration:** Full implementation in one continuous session
**Status:** AWAITING APPROVAL

---

## ⚠️ CRITICAL EXECUTION RULES

**THIS IS A ONE-SHOT, NON-STOP IMPLEMENTATION:**

1. ✅ **START and CONTINUE** until ALL components are implemented
2. ✅ **DO NOT PAUSE** between phases or components
3. ✅ **DO NOT ASK** for intermediate approvals
4. ✅ **IMPLEMENT EVERYTHING** in the order specified below
5. ✅ **TEST EVERYTHING** as each component is completed
6. ✅ **FIX ALL ISSUES** immediately when tests fail
7. ✅ **ONLY STOP** when all 5 enhancements are 100% done and tested

**Success Criteria:** All tests passing, all 5 enhancements working, documentation complete.

---

## 📋 Enhancement Overview

### Enhancement 1: Automated Parameter Extraction (AST Parsing)
- TypeScript AST parser for extracting inputs and outputs from code
- Eliminate manual defaults files
- Auto-sync template with code

### Enhancement 2: Enhanced Template Format
- Support `parameters.inputs` with full metadata
- Support `parameters.outputs` with full metadata
- Backward compatibility with old format

### Enhancement 3: Template-First Validation
- Validate code matches template during registration
- Check all required inputs are used in code
- Check all required outputs are exported in code

### Enhancement 4: Strict Export Enforcement
- Enforce declared outputs are actually exported
- Catch missing/undeclared exports before deployment
- Clear error messages

### Enhancement 5: Enhanced Validation Commands
- Update `cloud register-stack` with `--validate` flag
- Update `cloud validate-stack` with export checking
- Add `cloud validate <deployment-id> --check-exports`

---

## 🎯 Implementation Roadmap (One Continuous Session)

### PHASE 1: Foundation - TypeScript Parser Module
**Duration: Part 1 of continuous session**

#### 1.1 Install Dependencies
```bash
cd cloud/tools/core
pip install esprima
```

#### 1.2 Create Parser Module Structure
**Files to create:**
- `cloud_core/parsers/__init__.py`
- `cloud_core/parsers/typescript_parser.py`
- `cloud_core/parsers/parameter_extractor.py`
- `tests/test_parsers/__init__.py`
- `tests/test_parsers/test_typescript_parser.py`
- `tests/test_parsers/test_parameter_extractor.py`

#### 1.3 Implement TypeScript Parser

**File:** `cloud_core/parsers/typescript_parser.py`

```python
"""
TypeScript AST Parser for Stack Analysis
Extracts input parameters and output exports from TypeScript stack code
"""

import esprima
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class InputParameter:
    """Represents an input parameter found in code"""
    name: str
    type: str
    required: bool
    default: Optional[Any]
    description: str
    validation: Dict[str, Any]

@dataclass
class OutputParameter:
    """Represents an output export found in code"""
    name: str
    type: str
    required: bool
    description: str
    condition: Optional[str]

class TypeScriptParser:
    """Parse TypeScript stack code to extract parameters"""

    def __init__(self, stack_dir: Path):
        self.stack_dir = Path(stack_dir)
        self.index_file = self.stack_dir / "index.ts"

    def parse(self) -> Dict[str, Any]:
        """Parse stack and return inputs and outputs"""
        if not self.index_file.exists():
            raise FileNotFoundError(f"index.ts not found: {self.index_file}")

        source_code = self.index_file.read_text(encoding='utf-8')

        return {
            "inputs": self.extract_inputs(source_code),
            "outputs": self.extract_outputs(source_code)
        }

    def extract_inputs(self, source_code: str) -> List[InputParameter]:
        """Extract input parameters from config.require() and config.get()"""
        inputs = []

        # Pattern: config.require('paramName') or config.get('paramName')
        require_pattern = r"config\.(require|get|requireSecret|getSecret)\(['\"](\w+)['\"]\)"

        for match in re.finditer(require_pattern, source_code):
            method = match.group(1)
            param_name = match.group(2)

            # Extract JSDoc comment if exists
            description = self._extract_description(source_code, match.start())

            # Infer type from usage
            param_type = self._infer_type(source_code, param_name)

            # Determine if required
            required = method in ['require', 'requireSecret']

            # Extract default value for optional parameters
            default = self._extract_default(source_code, param_name) if not required else None

            inputs.append(InputParameter(
                name=param_name,
                type=param_type,
                required=required,
                default=default,
                description=description or f"Parameter: {param_name}",
                validation={}
            ))

        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_inputs = []
        for inp in inputs:
            if inp.name not in seen:
                seen.add(inp.name)
                unique_inputs.append(inp)

        return unique_inputs

    def extract_outputs(self, source_code: str) -> List[OutputParameter]:
        """Extract output exports from export statements and pulumi.export()"""
        outputs = []

        # Pattern 1: export const outputName = ...
        export_const_pattern = r"export\s+const\s+(\w+)\s*[:=]"

        for match in re.finditer(export_const_pattern, source_code):
            output_name = match.group(1)

            # Skip if it's not an output (e.g., helper functions)
            if output_name.startswith('_') or output_name[0].isupper():
                continue

            description = self._extract_description(source_code, match.start())
            output_type = self._infer_output_type(source_code, output_name)

            outputs.append(OutputParameter(
                name=output_name,
                type=output_type,
                required=True,  # Exported values are typically required
                description=description or f"Output: {output_name}",
                condition=None
            ))

        # Pattern 2: pulumi.export('outputName', ...)
        pulumi_export_pattern = r"pulumi\.export\(['\"](\w+)['\"]"

        for match in re.finditer(pulumi_export_pattern, source_code):
            output_name = match.group(1)
            description = self._extract_description(source_code, match.start())

            # Check if already added from export const
            if not any(o.name == output_name for o in outputs):
                outputs.append(OutputParameter(
                    name=output_name,
                    type="unknown",
                    required=True,
                    description=description or f"Output: {output_name}",
                    condition=None
                ))

        return outputs

    def _extract_description(self, source_code: str, position: int) -> Optional[str]:
        """Extract JSDoc or inline comment description"""
        # Look backward for JSDoc comment
        lines_before = source_code[:position].split('\n')

        # Check last few lines for comments
        for i in range(len(lines_before) - 1, max(0, len(lines_before) - 5), -1):
            line = lines_before[i].strip()

            # JSDoc comment: /** description */
            if line.startswith('/**') or line.startswith('*'):
                desc = line.replace('/**', '').replace('*/', '').replace('*', '').strip()
                if desc:
                    return desc

            # Single-line comment: // description
            if line.startswith('//'):
                desc = line.replace('//', '').strip()
                if desc:
                    return desc

        return None

    def _infer_type(self, source_code: str, param_name: str) -> str:
        """Infer type from variable usage or type annotations"""
        # Look for type annotations
        type_annotation_pattern = rf"const\s+{param_name}\s*:\s*(\w+(?:<[^>]+>)?)"
        match = re.search(type_annotation_pattern, source_code)
        if match:
            return self._normalize_type(match.group(1))

        # Look for config method with type hint
        typed_config_pattern = rf"config\.require(?:Number|Boolean|Object)\(['\"]({param_name})['\"]\)"
        match = re.search(typed_config_pattern, source_code)
        if match:
            if 'Number' in match.group(0):
                return 'number'
            elif 'Boolean' in match.group(0):
                return 'boolean'
            elif 'Object' in match.group(0):
                return 'object'

        # Default to string
        return 'string'

    def _infer_output_type(self, source_code: str, output_name: str) -> str:
        """Infer output type from assignment or type annotation"""
        # Look for type annotation
        type_pattern = rf"export\s+const\s+{output_name}\s*:\s*([^=]+)="
        match = re.search(type_pattern, source_code)
        if match:
            return self._normalize_type(match.group(1).strip())

        # Check if it's a Pulumi Output
        if re.search(rf"{output_name}\s*=.*\.id", source_code):
            return 'string'

        if re.search(rf"{output_name}\s*=.*\.map\(", source_code):
            return 'array'

        return 'unknown'

    def _normalize_type(self, type_str: str) -> str:
        """Normalize TypeScript types to simple types"""
        type_str = type_str.strip()

        # Handle Pulumi Output<T>
        if type_str.startswith('pulumi.Output<') or type_str.startswith('Output<'):
            inner = re.search(r'<(.+)>', type_str)
            if inner:
                type_str = inner.group(1).strip()

        # Map TypeScript types to simple types
        type_map = {
            'string': 'string',
            'number': 'number',
            'boolean': 'boolean',
            'any': 'string',
            'unknown': 'string',
            'string[]': 'array',
            'number[]': 'array',
        }

        for ts_type, simple_type in type_map.items():
            if type_str.startswith(ts_type):
                return simple_type

        if '[]' in type_str:
            return 'array'

        if type_str in ['Record', 'object', 'Object']:
            return 'object'

        return 'string'

    def _extract_default(self, source_code: str, param_name: str) -> Optional[Any]:
        """Extract default value from config.get() second argument"""
        default_pattern = rf"config\.get\(['\"]({param_name})['\"],\s*([^)]+)\)"
        match = re.search(default_pattern, source_code)

        if match:
            default_val = match.group(2).strip()

            # Remove quotes
            if default_val.startswith('"') or default_val.startswith("'"):
                return default_val[1:-1]

            # Try to parse as literal
            try:
                if default_val == 'true':
                    return True
                elif default_val == 'false':
                    return False
                elif default_val.isdigit():
                    return int(default_val)
                else:
                    return default_val
            except:
                return default_val

        return None
```

#### 1.4 Implement Parameter Extractor Utility

**File:** `cloud_core/parsers/parameter_extractor.py`

```python
"""
High-level parameter extraction interface
Orchestrates TypeScript parsing and produces template-ready data
"""

from pathlib import Path
from typing import Dict, List, Any
from .typescript_parser import TypeScriptParser, InputParameter, OutputParameter

class ParameterExtractor:
    """Extract and format parameters for template generation"""

    @staticmethod
    def extract_from_stack(stack_dir: Path) -> Dict[str, Any]:
        """
        Extract parameters from stack directory

        Returns:
            Dict with 'inputs' and 'outputs' in template format
        """
        parser = TypeScriptParser(stack_dir)
        result = parser.parse()

        return {
            "inputs": [ParameterExtractor._format_input(inp) for inp in result["inputs"]],
            "outputs": [ParameterExtractor._format_output(out) for out in result["outputs"]]
        }

    @staticmethod
    def _format_input(param: InputParameter) -> Dict[str, Any]:
        """Format InputParameter for template"""
        formatted = {
            "name": param.name,
            "type": param.type,
            "required": param.required,
            "description": param.description,
        }

        if param.default is not None:
            formatted["default"] = param.default

        if param.validation:
            formatted["validation"] = param.validation

        return formatted

    @staticmethod
    def _format_output(param: OutputParameter) -> Dict[str, Any]:
        """Format OutputParameter for template"""
        formatted = {
            "name": param.name,
            "type": param.type,
            "required": param.required,
            "description": param.description,
        }

        if param.condition:
            formatted["condition"] = param.condition

        return formatted
```

#### 1.5 Create Comprehensive Tests

**File:** `tests/test_parsers/test_typescript_parser.py`

```python
"""Tests for TypeScript parser"""

import pytest
from pathlib import Path
from cloud_core.parsers.typescript_parser import TypeScriptParser, InputParameter, OutputParameter

# Test fixtures with sample TypeScript code
SAMPLE_STACK_CODE = '''
import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';

const config = new pulumi.Config();

// VPC CIDR block
const vpcCidr = config.require('vpcCidr');

// Number of availability zones
const availabilityZones = config.requireNumber('availabilityZones');

// Enable NAT gateway (optional)
const enableNatGateway = config.getBoolean('enableNatGateway', false);

// Environment name
const environment = config.get('environment', 'dev');

// Create VPC
const vpc = new aws.ec2.Vpc('main', {
    cidrBlock: vpcCidr,
    enableDnsHostnames: true,
});

/** ID of the created VPC */
export const vpcId = vpc.id;

/** CIDR block of the VPC */
export const vpcCidr = vpc.cidrBlock;

// Export using pulumi.export
pulumi.export('availabilityZones', availabilityZones);
'''

@pytest.fixture
def temp_stack_dir(tmp_path):
    """Create temporary stack directory with sample code"""
    stack_dir = tmp_path / "test-stack"
    stack_dir.mkdir()

    index_file = stack_dir / "index.ts"
    index_file.write_text(SAMPLE_STACK_CODE)

    return stack_dir

def test_parser_initialization(temp_stack_dir):
    """Test parser can be initialized"""
    parser = TypeScriptParser(temp_stack_dir)
    assert parser.stack_dir == temp_stack_dir
    assert parser.index_file.exists()

def test_extract_inputs(temp_stack_dir):
    """Test extracting input parameters"""
    parser = TypeScriptParser(temp_stack_dir)
    source_code = SAMPLE_STACK_CODE

    inputs = parser.extract_inputs(source_code)

    # Should find 4 input parameters
    assert len(inputs) >= 4

    # Check vpcCidr (required string)
    vpc_cidr = next((inp for inp in inputs if inp.name == 'vpcCidr'), None)
    assert vpc_cidr is not None
    assert vpc_cidr.required is True
    assert vpc_cidr.type == 'string'

    # Check availabilityZones (required number)
    az = next((inp for inp in inputs if inp.name == 'availabilityZones'), None)
    assert az is not None
    assert az.required is True
    assert az.type == 'number'

    # Check enableNatGateway (optional boolean)
    nat = next((inp for inp in inputs if inp.name == 'enableNatGateway'), None)
    assert nat is not None
    assert nat.required is False
    assert nat.type == 'boolean'
    assert nat.default is False

def test_extract_outputs(temp_stack_dir):
    """Test extracting output parameters"""
    parser = TypeScriptParser(temp_stack_dir)
    source_code = SAMPLE_STACK_CODE

    outputs = parser.extract_outputs(source_code)

    # Should find at least 3 outputs
    assert len(outputs) >= 2

    # Check vpcId export
    vpc_id = next((out for out in outputs if out.name == 'vpcId'), None)
    assert vpc_id is not None
    assert vpc_id.required is True
    assert 'VPC' in vpc_id.description

def test_parse_complete(temp_stack_dir):
    """Test complete parsing"""
    parser = TypeScriptParser(temp_stack_dir)
    result = parser.parse()

    assert 'inputs' in result
    assert 'outputs' in result
    assert len(result['inputs']) > 0
    assert len(result['outputs']) > 0

def test_missing_index_file(tmp_path):
    """Test error when index.ts missing"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    parser = TypeScriptParser(empty_dir)

    with pytest.raises(FileNotFoundError):
        parser.parse()

def test_extract_description():
    """Test description extraction from comments"""
    parser = TypeScriptParser(Path('.'))

    code = '''
    /** This is a VPC CIDR */
    const vpcCidr = config.require('vpcCidr');
    '''

    desc = parser._extract_description(code, code.index('const vpcCidr'))
    assert desc == "This is a VPC CIDR"

def test_infer_types():
    """Test type inference"""
    parser = TypeScriptParser(Path('.'))

    code = '''
    const count: number = config.requireNumber('count');
    const enabled: boolean = config.getBoolean('enabled');
    const name = config.require('name');
    '''

    # Test number
    assert parser._infer_type(code, 'count') == 'number'

    # Test boolean
    assert parser._infer_type(code, 'enabled') == 'boolean'

    # Test string (default)
    assert parser._infer_type(code, 'name') == 'string'
```

**Continue with more test cases for edge cases, error handling, etc.**

---

### PHASE 2: Enhanced Template Format Support
**Duration: Part 2 of continuous session**

#### 2.1 Update Template Manager

**File:** `cloud_core/templates/template_manager.py`

**Add to existing class:**

```python
def validate_enhanced_template(self, template_data: Dict[str, Any], template_name: str) -> None:
    """
    Validate enhanced template format with parameters.inputs and parameters.outputs

    Raises:
        TemplateValidationError: If validation fails
    """
    # Check for parameters section
    if "parameters" in template_data:
        parameters = template_data["parameters"]

        if not isinstance(parameters, dict):
            raise TemplateValidationError(
                f"Template '{template_name}' has invalid parameters section (must be dict)"
            )

        # Validate inputs if present
        if "inputs" in parameters:
            self._validate_inputs(parameters["inputs"], template_name)

        # Validate outputs if present
        if "outputs" in parameters:
            self._validate_outputs(parameters["outputs"], template_name)

    # Call original validation for backward compatibility
    self._validate_template(template_data, template_name)

def _validate_inputs(self, inputs: Any, template_name: str) -> None:
    """Validate inputs section"""
    if not isinstance(inputs, list):
        raise TemplateValidationError(
            f"Template '{template_name}' parameters.inputs must be a list"
        )

    for idx, input_param in enumerate(inputs):
        if not isinstance(input_param, dict):
            raise TemplateValidationError(
                f"Template '{template_name}' input parameter {idx} must be a dict"
            )

        # Required fields
        required_fields = ['name', 'type', 'required', 'description']
        for field in required_fields:
            if field not in input_param:
                raise TemplateValidationError(
                    f"Template '{template_name}' input parameter {idx} missing required field: {field}"
                )

        # Validate type
        valid_types = ['string', 'number', 'boolean', 'array', 'object']
        if input_param['type'] not in valid_types:
            raise TemplateValidationError(
                f"Template '{template_name}' input parameter '{input_param['name']}' has invalid type: {input_param['type']}"
            )

def _validate_outputs(self, outputs: Any, template_name: str) -> None:
    """Validate outputs section"""
    if not isinstance(outputs, list):
        raise TemplateValidationError(
            f"Template '{template_name}' parameters.outputs must be a list"
        )

    for idx, output_param in enumerate(outputs):
        if not isinstance(output_param, dict):
            raise TemplateValidationError(
                f"Template '{template_name}' output parameter {idx} must be a dict"
            )

        # Required fields
        required_fields = ['name', 'type', 'required', 'description']
        for field in required_fields:
            if field not in output_param:
                raise TemplateValidationError(
                    f"Template '{template_name}' output parameter {idx} missing required field: {field}"
                )
```

#### 2.2 Create Template Format Tests

**Add comprehensive tests for enhanced format validation**

---

### PHASE 3: Stack Code Validator
**Duration: Part 3 of continuous session**

#### 3.1 Create Validator Module

**File:** `cloud_core/validation/stack_code_validator.py`

```python
"""
Stack Code Validator
Validates that stack code matches template declarations
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..parsers.parameter_extractor import ParameterExtractor
from ..templates.template_manager import TemplateManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    """Result of stack code validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]

    def is_valid(self) -> bool:
        return self.valid and len(self.errors) == 0

class StackCodeValidator:
    """Validate stack code against template"""

    def __init__(self, template_manager: Optional[TemplateManager] = None):
        self.template_manager = template_manager or TemplateManager()

    def validate_against_template(
        self,
        stack_name: str,
        stack_dir: Path,
        template: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate that stack code matches template

        Args:
            stack_name: Name of the stack
            stack_dir: Path to stack directory
            template: Optional template dict (loads if not provided)

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        try:
            # Load template if not provided
            if template is None:
                template = self.template_manager.load_template(stack_name)

            # Extract actual parameters from code
            extractor = ParameterExtractor()
            actual_params = extractor.extract_from_stack(stack_dir)

            # Validate inputs
            if "parameters" in template and "inputs" in template["parameters"]:
                input_errors, input_warnings = self._validate_inputs(
                    template["parameters"]["inputs"],
                    actual_params["inputs"]
                )
                errors.extend(input_errors)
                warnings.extend(input_warnings)

            # Validate outputs
            if "parameters" in template and "outputs" in template["parameters"]:
                output_errors, output_warnings = self._validate_outputs(
                    template["parameters"]["outputs"],
                    actual_params["outputs"]
                )
                errors.extend(output_errors)
                warnings.extend(output_warnings)

        except FileNotFoundError as e:
            errors.append(f"Template or code file not found: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
            logger.error(f"Stack validation failed for {stack_name}: {e}", exc_info=True)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_inputs(
        self,
        declared_inputs: List[Dict[str, Any]],
        actual_inputs: List[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """Validate inputs match between template and code"""
        errors = []
        warnings = []

        # Check all required inputs are used in code
        for declared in declared_inputs:
            if not declared.get('required', False):
                continue

            actual = next(
                (inp for inp in actual_inputs if inp['name'] == declared['name']),
                None
            )

            if actual is None:
                errors.append(
                    f"Required input '{declared['name']}' declared in template but not found in code"
                )

        # Warn about inputs in code but not in template
        for actual in actual_inputs:
            declared = next(
                (inp for inp in declared_inputs if inp['name'] == actual['name']),
                None
            )

            if declared is None:
                warnings.append(
                    f"Input '{actual['name']}' used in code but not declared in template. "
                    f"Consider adding to template for documentation."
                )

        return errors, warnings

    def _validate_outputs(
        self,
        declared_outputs: List[Dict[str, Any]],
        actual_outputs: List[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """Validate outputs match between template and code"""
        errors = []
        warnings = []

        # Check all required outputs are exported
        for declared in declared_outputs:
            if not declared.get('required', False):
                continue

            actual = next(
                (out for out in actual_outputs if out['name'] == declared['name']),
                None
            )

            if actual is None:
                errors.append(
                    f"Required output '{declared['name']}' declared in template but not exported in code"
                )

        # Warn about exports not in template
        for actual in actual_outputs:
            declared = next(
                (out for out in declared_outputs if out['name'] == actual['name']),
                None
            )

            if declared is None:
                warnings.append(
                    f"Output '{actual['name']}' exported in code but not declared in template. "
                    f"Consider adding to template for documentation."
                )

        return errors, warnings
```

#### 3.2 Create Validator Tests

**File:** `tests/test_validation/test_stack_code_validator.py`

**Comprehensive test suite for all validation scenarios**

---

### PHASE 4: Update CLI Commands
**Duration: Part 4 of continuous session**

#### 4.1 Update register-stack Command

**File:** `cloud_cli/commands/stack_cmd.py`

**Replace existing register_stack_command with:**

```python
@app.command(name="register-stack")
def register_stack_command(
    stack_name: str = typer.Argument(..., help="Stack name"),
    description: str = typer.Option(..., "--description", "-d", help="Stack description"),
    dependencies: Optional[str] = typer.Option(
        None, "--dependencies", help="Comma-separated list of dependencies"
    ),
    priority: int = typer.Option(100, "--priority", "-p", help="Stack priority"),
    defaults_file: Optional[str] = typer.Option(
        None, "--defaults-file", help="YAML file with default configuration (optional)"
    ),
    auto_extract: bool = typer.Option(
        True, "--auto-extract/--no-auto-extract",
        help="Automatically extract parameters from code"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate code matches template"
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Treat warnings as errors"
    ),
) -> None:
    """Register a new stack with the platform (Enhanced)"""

    from cloud_core.parsers.parameter_extractor import ParameterExtractor
    from cloud_core.validation.stack_code_validator import StackCodeValidator

    try:
        # Validate stack directory exists
        stack_dir = Path.cwd() / "stacks" / stack_name
        if not stack_dir.exists():
            console.print(f"[red]Error:[/red] Stack directory not found: {stack_dir}")
            raise typer.Exit(1)

        # Check required files
        index_ts = stack_dir / "index.ts"
        pulumi_yaml = stack_dir / "Pulumi.yaml"

        if not index_ts.exists():
            console.print(f"[red]Error:[/red] index.ts not found in {stack_dir}")
            raise typer.Exit(1)

        if not pulumi_yaml.exists():
            console.print(f"[red]Error:[/red] Pulumi.yaml not found in {stack_dir}")
            raise typer.Exit(1)

        # Parse dependencies
        deps = []
        if dependencies:
            deps = [d.strip() for d in dependencies.split(',')]

        # ENHANCEMENT 1: Auto-extract parameters from code
        parameters = None
        if auto_extract:
            console.print("[cyan]Extracting parameters from code...[/cyan]")
            try:
                extractor = ParameterExtractor()
                extracted = extractor.extract_from_stack(stack_dir)

                parameters = extracted

                console.print(f"[green]✓[/green] Found {len(extracted['inputs'])} input parameters")
                console.print(f"[green]✓[/green] Found {len(extracted['outputs'])} output parameters")

            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Auto-extraction failed: {e}")
                console.print("[yellow]Falling back to manual defaults file...[/yellow]")
                auto_extract = False

        # Fallback: Load from defaults file
        if not auto_extract:
            config_defaults = {}
            if defaults_file:
                defaults_path = Path(defaults_file)
                if defaults_path.exists():
                    with open(defaults_path, 'r') as f:
                        config_defaults = yaml.safe_load(f) or {}
                else:
                    console.print(f"[yellow]Warning:[/yellow] Defaults file not found: {defaults_file}")

            # Convert old format to new format
            parameters = {
                "inputs": [
                    {
                        "name": key,
                        "type": "string",
                        "required": False,
                        "default": value,
                        "description": f"Parameter: {key}"
                    }
                    for key, value in config_defaults.items()
                ],
                "outputs": []
            }

        # ENHANCEMENT 2: Create enhanced template
        template_data = {
            "name": stack_name,
            "description": description,
            "dependencies": deps,
            "priority": priority,
            "parameters": parameters,
        }

        # ENHANCEMENT 3: Validate if requested
        if validate:
            console.print("[cyan]Validating stack code against template...[/cyan]")

            validator = StackCodeValidator()
            result = validator.validate_against_template(
                stack_name,
                stack_dir,
                template=template_data
            )

            if result.errors:
                console.print("[red]✗ Validation failed:[/red]")
                for error in result.errors:
                    console.print(f"  [red]•[/red] {error}")
                raise typer.Exit(1)

            if result.warnings:
                console.print("[yellow]⚠ Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  [yellow]•[/yellow] {warning}")

                if strict:
                    console.print("[red]Strict mode: treating warnings as errors[/red]")
                    raise typer.Exit(1)

            console.print("[green]✓[/green] Validation passed")

        # Write template file
        template_dir = Path.cwd() / "tools" / "templates" / "config"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / f"{stack_name}.yaml"

        with open(template_file, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓[/green] Stack '{stack_name}' registered successfully")
        console.print(f"  Template: {template_file}")
        console.print(f"  Dependencies: {', '.join(deps) if deps else 'none'}")
        console.print(f"  Priority: {priority}")
        console.print(f"  Inputs: {len(parameters['inputs'])}")
        console.print(f"  Outputs: {len(parameters['outputs'])}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Register-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)
```

#### 4.2 Update validate-stack Command

**Replace existing validate_stack_command with:**

```python
@app.command(name="validate-stack")
def validate_stack_command(
    stack_name: str = typer.Argument(..., help="Stack name"),
    check_exports: bool = typer.Option(
        True, "--check-exports/--no-check-exports",
        help="Check that code exports match template"
    ),
) -> None:
    """Validate a stack's structure and configuration (Enhanced)"""

    from cloud_core.validation.stack_code_validator import StackCodeValidator

    try:
        # Check stack directory
        stack_dir = Path.cwd() / "stacks" / stack_name

        if not stack_dir.exists():
            console.print(f"[red]Error:[/red] Stack directory not found: {stack_dir}")
            raise typer.Exit(1)

        errors = []
        warnings = []

        # Check required files
        required_files = ["index.ts", "Pulumi.yaml", "package.json"]
        for file in required_files:
            if not (stack_dir / file).exists():
                errors.append(f"Missing required file: {file}")

        # Check if registered
        template_file = Path.cwd() / "tools" / "templates" / "config" / f"{stack_name}.yaml"

        if not template_file.exists():
            warnings.append(f"Stack not registered (run 'cloud register-stack {stack_name}')")
        else:
            # ENHANCEMENT: Validate code against template
            if check_exports:
                console.print(f"[cyan]Validating code against template...[/cyan]")

                validator = StackCodeValidator()
                result = validator.validate_against_template(stack_name, stack_dir)

                errors.extend(result.errors)
                warnings.extend(result.warnings)

                if result.is_valid():
                    console.print("[green]✓ Code matches template[/green]")

        # Report results
        if errors:
            console.print(f"[red]Validation failed for '{stack_name}':[/red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error}")
            raise typer.Exit(1)

        console.print(f"[green]✓ Stack '{stack_name}' is valid[/green]")

        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  [yellow]![/yellow] {warning}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validate-stack command failed: {e}", exc_info=True)
        raise typer.Exit(1)
```

#### 4.3 Add Deployment Validation Command

**Add new command to deploy_cmd.py:**

```python
@app.command(name="validate")
def validate_deployment_command(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    check_exports: bool = typer.Option(
        True, "--check-exports", help="Check stack exports"
    ),
) -> None:
    """Validate deployment before deploying"""

    from cloud_core.validation.stack_code_validator import StackCodeValidator
    from cloud_core.deployment.deployment_manager import DeploymentManager

    try:
        console.print(f"[cyan]Validating deployment {deployment_id}...[/cyan]\n")

        # Load deployment
        deploy_root = Path.cwd() / "deploy"
        manager = DeploymentManager(deploy_root)

        deployment_dir = manager.get_deployment_dir(deployment_id)
        manifest = manager.load_manifest(deployment_id)

        # Get enabled stacks
        enabled_stacks = [
            name for name, config in manifest['stacks'].items()
            if config.get('enabled', True)
        ]

        all_valid = True
        validator = StackCodeValidator()

        for stack_name in enabled_stacks:
            console.print(f"Validating stack: [cyan]{stack_name}[/cyan]")

            stack_dir = Path.cwd() / "stacks" / stack_name

            # Validate
            result = validator.validate_against_template(stack_name, stack_dir)

            if result.errors:
                all_valid = False
                for error in result.errors:
                    console.print(f"  [red]✗[/red] {error}")
            else:
                console.print(f"  [green]✓[/green] All checks passed")

            if result.warnings:
                for warning in result.warnings:
                    console.print(f"  [yellow]![/yellow] {warning}")

            console.print()

        if all_valid:
            console.print("[green]✓ All stacks valid. Ready for deployment.[/green]")
        else:
            console.print("[red]✗ Validation failed. Fix errors before deployment.[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

---

### PHASE 5: Integration Tests
**Duration: Part 5 of continuous session**

#### 5.1 End-to-End Test Suite

**File:** `tests/test_integration/test_enhanced_registration.py`

```python
"""Integration tests for enhanced registration system"""

import pytest
import yaml
from pathlib import Path
from typer.testing import CliRunner

from cloud_cli.main import app

runner = CliRunner()

@pytest.fixture
def sample_stack_dir(tmp_path):
    """Create a sample stack for testing"""
    stack_dir = tmp_path / "stacks" / "test-stack"
    stack_dir.mkdir(parents=True)

    # Create index.ts
    index_code = '''
import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';

const config = new pulumi.Config();

// Required inputs
const vpcCidr = config.require('vpcCidr');
const environment = config.require('environment');

// Optional inputs
const enableNat = config.getBoolean('enableNat', false);

// Create VPC
const vpc = new aws.ec2.Vpc('main', {
    cidrBlock: vpcCidr,
});

// Exports
export const vpcId = vpc.id;
export const vpcCidr = vpc.cidrBlock;
'''

    (stack_dir / "index.ts").write_text(index_code)

    # Create Pulumi.yaml
    pulumi_config = {
        "name": "test-stack",
        "runtime": "nodejs",
        "description": "Test stack"
    }

    with open(stack_dir / "Pulumi.yaml", 'w') as f:
        yaml.dump(pulumi_config, f)

    # Create package.json
    package_json = {
        "name": "test-stack",
        "dependencies": {
            "@pulumi/pulumi": "^3.0.0",
            "@pulumi/aws": "^5.0.0"
        }
    }

    with open(stack_dir / "package.json", 'w') as f:
        import json
        json.dump(package_json, f)

    return tmp_path

def test_register_with_auto_extract(sample_stack_dir, monkeypatch):
    """Test registration with auto-extraction"""
    monkeypatch.chdir(sample_stack_dir)

    result = runner.invoke(app, [
        "register-stack",
        "test-stack",
        "--description", "Test stack",
        "--auto-extract",
    ])

    assert result.exit_code == 0
    assert "Found 3 input parameters" in result.output
    assert "Found 2 output parameters" in result.output

    # Check template was created
    template_file = sample_stack_dir / "tools" / "templates" / "config" / "test-stack.yaml"
    assert template_file.exists()

    # Verify template structure
    with open(template_file) as f:
        template = yaml.safe_load(f)

    assert "parameters" in template
    assert "inputs" in template["parameters"]
    assert "outputs" in template["parameters"]

    # Check inputs
    inputs = {inp['name']: inp for inp in template["parameters"]["inputs"]}
    assert 'vpcCidr' in inputs
    assert inputs['vpcCidr']['required'] is True
    assert 'enableNat' in inputs
    assert inputs['enableNat']['required'] is False

    # Check outputs
    outputs = {out['name']: out for out in template["parameters"]["outputs"]}
    assert 'vpcId' in outputs
    assert 'vpcCidr' in outputs

def test_register_with_validation(sample_stack_dir, monkeypatch):
    """Test registration with validation"""
    monkeypatch.chdir(sample_stack_dir)

    result = runner.invoke(app, [
        "register-stack",
        "test-stack",
        "--description", "Test stack",
        "--auto-extract",
        "--validate",
    ])

    assert result.exit_code == 0
    assert "Validation passed" in result.output

def test_validate_stack_command(sample_stack_dir, monkeypatch):
    """Test validate-stack command"""
    monkeypatch.chdir(sample_stack_dir)

    # First register
    runner.invoke(app, [
        "register-stack",
        "test-stack",
        "--description", "Test stack",
        "--auto-extract",
    ])

    # Then validate
    result = runner.invoke(app, [
        "validate-stack",
        "test-stack",
        "--check-exports",
    ])

    assert result.exit_code == 0
    assert "Code matches template" in result.output
```

#### 5.2 Add More Integration Tests

**Continue with tests for:**
- Template format validation
- Error scenarios
- Warning scenarios
- Strict mode
- Backward compatibility

---

### PHASE 6: Documentation and Examples
**Duration: Part 6 of continuous session**

#### 6.1 Create Usage Examples

**File:** `tools/docs/examples/Enhanced_Registration_Examples.md`

**Include:**
- Basic registration with auto-extract
- Registration with validation
- Handling warnings
- Strict mode usage
- Manual defaults fallback
- Update existing registrations

#### 6.2 Update CLI Help

**Add comprehensive help text to all commands**

---

## 📊 Testing Strategy

### Unit Tests (90% coverage minimum)

1. **TypeScript Parser Tests** (20 tests)
   - Input extraction
   - Output extraction
   - Type inference
   - Description extraction
   - Edge cases

2. **Parameter Extractor Tests** (10 tests)
   - Extraction and formatting
   - Error handling

3. **Template Validation Tests** (15 tests)
   - Enhanced format validation
   - Backward compatibility
   - Error scenarios

4. **Stack Code Validator Tests** (20 tests)
   - Input validation
   - Output validation
   - Warning generation
   - Error generation

5. **CLI Command Tests** (15 tests)
   - register-stack variations
   - validate-stack scenarios
   - validate deployment

### Integration Tests (Full workflows)

1. **End-to-End Registration** (10 tests)
   - Complete registration flow
   - With all combinations of flags

2. **Validation Workflows** (10 tests)
   - Stack validation
   - Deployment validation

### Manual Testing Checklist

- [ ] Register new stack with auto-extract
- [ ] Register with validation enabled
- [ ] Register with strict mode
- [ ] Validate existing stack
- [ ] Validate before deployment
- [ ] Handle errors gracefully
- [ ] Backward compatibility with old templates

---

## 📦 Deliverables

### New Files Created (19 files)

**Core Implementation:**
1. `cloud_core/parsers/__init__.py`
2. `cloud_core/parsers/typescript_parser.py` (~400 lines)
3. `cloud_core/parsers/parameter_extractor.py` (~100 lines)
4. `cloud_core/validation/stack_code_validator.py` (~250 lines)

**Tests:**
5. `tests/test_parsers/__init__.py`
6. `tests/test_parsers/test_typescript_parser.py` (~400 lines)
7. `tests/test_parsers/test_parameter_extractor.py` (~200 lines)
8. `tests/test_validation/test_stack_code_validator.py` (~300 lines)
9. `tests/test_integration/test_enhanced_registration.py` (~500 lines)

**Documentation:**
10. `tools/docs/examples/Enhanced_Registration_Examples.md`
11. `tools/docs/Implementation_Plan_Enhanced_Stack_Registration.md` (this file)

### Files Modified (4 files)

1. `cloud_core/templates/template_manager.py` (+150 lines)
2. `cloud_cli/commands/stack_cmd.py` (+200 lines)
3. `cloud_cli/commands/deploy_cmd.py` (+80 lines)
4. `requirements.txt` (add esprima)

### Total Lines of Code

- **Implementation:** ~1,500 lines
- **Tests:** ~1,400 lines
- **Documentation:** ~1,000 lines
- **TOTAL:** ~3,900 lines

---

## ✅ Acceptance Criteria

### Functional Requirements

1. ✅ `cloud register-stack` with `--auto-extract` works
2. ✅ Input parameters auto-extracted from `config.require()` calls
3. ✅ Output parameters auto-extracted from `export` statements
4. ✅ Enhanced template format with `parameters.inputs` and `parameters.outputs`
5. ✅ `--validate` flag during registration works
6. ✅ Code/template mismatch errors caught and reported
7. ✅ `cloud validate-stack` checks exports
8. ✅ `cloud validate <deployment-id>` validates all stacks
9. ✅ Backward compatibility with old template format
10. ✅ Clear error messages for all failure scenarios

### Quality Requirements

1. ✅ 90%+ test coverage on all new code
2. ✅ All tests passing
3. ✅ No regression on existing functionality
4. ✅ Comprehensive error handling
5. ✅ Clear user-facing messages
6. ✅ Well-documented code
7. ✅ Examples and usage documentation

---

## 🚀 Execution Sequence

**Once approved, execute in this exact order:**

1. **START** - Clear todos, create fresh todo list
2. **Install dependencies** - pip install esprima
3. **PHASE 1** - TypeScript parser (create, implement, test)
4. **PHASE 2** - Enhanced template format (update, test)
5. **PHASE 3** - Stack validator (create, implement, test)
6. **PHASE 4** - CLI commands (update all 3, test)
7. **PHASE 5** - Integration tests (create, run)
8. **PHASE 6** - Documentation (create examples)
9. **RUN ALL TESTS** - Verify 90%+ coverage
10. **MANUAL VALIDATION** - Test with real stack
11. **COMPLETE** - Mark all todos done

**DO NOT STOP** between phases. Execute continuously until 100% complete.

---

## 📝 Post-Implementation Tasks (Task 3)

After all enhancements are implemented and tested:

1. Create `Stack_Parameters_and_Registration_Guide_v2.md`
   - Update with actual implementation details
   - Include code examples from implementation
   - Update all diagrams

2. Create `Complete_Guide_Templates_Stacks_Config_and_Registration_v2.md`
   - Update template format documentation
   - Add output support documentation
   - Update all workflows

3. Create `Complete_Stack_Management_Guide_v3.md`
   - Combine both v2 documents
   - Remove redundant information
   - Include all diagrams from both
   - Create comprehensive unified guide

---

## ⚡ Ready for Execution

**This plan is COMPLETE and READY.**

**Upon approval, I will:**
- Execute ALL phases without stopping
- Implement ALL 5 enhancements
- Write ALL tests (90%+ coverage)
- Create ALL documentation
- NOT stop until 100% complete

**Awaiting your approval to proceed with Task 2 (Full Implementation).**

---

**End of Implementation Plan**

**Document Version:** 1.0
**Created:** 2025-10-28
**Status:** AWAITING APPROVAL
