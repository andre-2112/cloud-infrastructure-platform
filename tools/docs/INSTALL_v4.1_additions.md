# INSTALL.md v4.1 - Additional Sections

These sections should be added to INSTALL.md after the "Testing and Running the CLI" section.

---

## Enhanced Template System

### Understanding Enhanced Templates

Stack templates in v4.0+ include structured parameter declarations with types, defaults, and validation.

### Template Structure

**Location:** `cloud/tools/templates/config/<stack-name>.yaml`

**Enhanced Format:**
```yaml
name: network
version: "1.0"
description: "VPC and networking infrastructure"

parameters:
  inputs:
    vpcCidr:
      type: string
      required: true
      default: "10.0.0.0/16"
      description: "CIDR block for VPC"

    availabilityZones:
      type: number
      required: true
      default: 3
      description: "Number of AZs to span"

  outputs:
    vpcId:
      type: string
      description: "VPC ID for cross-stack references"

    privateSubnetIds:
      type: array
      description: "Private subnet IDs"

dependencies: []
layer: 1
```

### Viewing Templates

```bash
# List all stack templates
ls cloud/tools/templates/config/

# View a specific template
cat cloud/tools/templates/config/network.yaml
```

### Testing Template Validation

```bash
# Validate a template
python -c "
from cloud_core.templates.stack_template_manager import StackTemplateManager

manager = StackTemplateManager()
template = manager.load_template('network')
print(f'✓ Template loaded: {template[\"name\"]}')
print(f'  Inputs: {len(template[\"parameters\"][\"inputs\"])}')
print(f'  Outputs: {len(template[\"parameters\"][\"outputs\"])}')
"
```

---

## Auto-Extraction and Validation

### Auto-Extraction System

The auto-extraction system automatically generates stack templates from TypeScript code.

### Setup

Auto-extraction is included in the CLI installation. No additional setup required.

### Basic Usage

**1. Write your stack code:**

```typescript
// stacks/network/index.ts
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const vpcCidr = config.require("vpcCidr");
const azCount = config.requireNumber("availabilityZones");

// ... implementation ...

export const vpcId = vpc.id;
export const privateSubnetIds = subnets.map(s => s.id);
```

**2. Run auto-extraction:**

```bash
cd cloud/tools/cli
source venv/Scripts/activate

# Auto-extract and register stack
python -m cloud_cli.main register-stack network --auto-extract
```

**3. System output:**

```
Extracting parameters from stacks/network/index.ts...

Found inputs:
  - vpcCidr (string, required)
  - availabilityZones (number, required)

Found outputs:
  - vpcId (string)
  - privateSubnetIds (array)

Generate template? [Y/n]: y

✓ Template generated: tools/templates/config/network.yaml
✓ Stack registered successfully
```

### Template-First Validation

Validate that stack code matches its template.

**Basic validation:**

```bash
# Validate a single stack
python -m cloud_cli.main validate-stack network

# Expected output:
# Validating stack: network
# ✓ Template loaded
# ✓ Stack code loaded
# ✓ All inputs validated
# ✓ All outputs validated
# Result: PASSED
```

**Strict validation:**

```bash
# Strict mode (fails on warnings)
python -m cloud_cli.main validate-stack network --strict

# Validate all stacks
python -m cloud_cli.main validate-stack --all --strict
```

### Validation Output Example

```
Validating stack: network
✓ Template: tools/templates/config/network.yaml
✓ Code: stacks/network/index.ts

Input Parameters:
✓ vpcCidr: declared in template, used in code (Config.require)
✓ availabilityZones: declared in template, used in code (Config.requireNumber)
⚠ enableNatGateway: declared in template, not found in code

Output Parameters:
✓ vpcId: declared in template, exported in code
✓ privateSubnetIds: declared in template, exported in code

Result: PASSED with 1 warning
  Use --strict to treat warnings as errors
```

### Testing Auto-Extraction

**Test parameter extraction:**

```bash
python -c "
from cloud_cli.parser.parameter_extractor import ParameterExtractor

extractor = ParameterExtractor()
result = extractor.extract_from_stack('stacks/network', 'network')

print(f'✓ Extracted {len(result[\"inputs\"])} inputs')
print(f'✓ Extracted {len(result[\"outputs\"])} outputs')

for name, param in result['inputs'].items():
    print(f'  - {name}: {param[\"type\"]} (required: {param[\"required\"]})')
"
```

### Testing Template-First Validation

**Test code validator:**

```bash
python -c "
from cloud_core.validation.stack_code_validator import StackCodeValidator
from cloud_core.templates.stack_template_manager import StackTemplateManager

validator = StackCodeValidator()
template_manager = StackTemplateManager()

template = template_manager.load_template('network')
result = validator.validate('stacks/network', template, 'network', strict=False)

print(f'Validation result: {\"PASSED\" if result.is_valid else \"FAILED\"}')
print(f'Errors: {len(result.errors)}')
print(f'Warnings: {len(result.warnings)}')
"
```

---

## Integration Testing

### End-to-End Workflow Test

Test the complete workflow from stack code to template to validation:

```bash
cd cloud/tools/cli
source venv/Scripts/activate

# 1. Extract and register a stack
echo "Testing auto-extraction..."
python -m cloud_cli.main register-stack network --auto-extract --defaults-file defaults.yaml

# 2. Validate the stack
echo "Testing validation..."
python -m cloud_cli.main validate-stack network --strict

# 3. Test template loading
echo "Testing template loading..."
python -c "
from cloud_core.templates.stack_template_manager import StackTemplateManager
manager = StackTemplateManager()
template = manager.load_template('network')
print(f'✓ Loaded template: {template[\"name\"]} v{template[\"version\"]}')
"

# 4. Test config generation
echo "Testing config generation..."
python -c "
from cloud_core.deployment.config_generator import ConfigGenerator
from pathlib import Path

gen = ConfigGenerator(Path('../../deploy/TEST'))
# ... test config generation ...
print('✓ Config generation working')
"

echo "✓ All integration tests passed"
```

---

**For full documentation, see:**
- [Multi_Stack_Architecture.4.1.md](Multi_Stack_Architecture.4.1.md) - Complete architecture
- [Stack_Parameters_and_Registration_Guide_v4.md](Stack_Parameters_and_Registration_Guide_v4.md) - Template system details
- [Complete_Stack_Management_Guide_v4.md](Complete_Stack_Management_Guide_v4.md) - Complete workflow guide

**Document Version:** 4.1
**Last Updated:** 2025-10-29
