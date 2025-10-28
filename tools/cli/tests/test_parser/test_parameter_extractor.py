"""Tests for parameter extractor"""

import pytest
from pathlib import Path
import yaml
from cloud_cli.parser.parameter_extractor import ParameterExtractor


@pytest.fixture
def tmp_stack_dir(tmp_path):
    """Create a temporary stack directory with test files"""
    stack_dir = tmp_path / "test-stack"
    stack_dir.mkdir()

    # Create index.ts with sample code
    index_ts = stack_dir / "index.ts"
    index_ts.write_text("""
    import * as pulumi from "@pulumi/pulumi";
    const config = new pulumi.Config();

    const vpcCidr = config.require("vpcCidr");
    const region = config.get("region", "us-east-1");

    export const vpcId = "vpc-12345";
    export const vpcArn = "arn:aws:vpc:us-east-1:123456789012:vpc/vpc-12345";
    """)

    return stack_dir


def test_parameter_extractor_init():
    """Test ParameterExtractor initialization"""
    extractor = ParameterExtractor()
    assert extractor is not None
    assert extractor.parser is not None


def test_extract_from_stack_success(tmp_stack_dir):
    """Test successful parameter extraction from stack"""
    extractor = ParameterExtractor()
    result = extractor.extract_from_stack(tmp_stack_dir, "test-stack")

    assert result["success"] is True
    assert result["stack_name"] == "test-stack"
    assert "parameters" in result

    params = result["parameters"]
    assert "inputs" in params
    assert "outputs" in params

    # Check inputs
    assert "vpcCidr" in params["inputs"]
    assert "region" in params["inputs"]

    # Check outputs
    assert "vpcId" in params["outputs"]
    assert "vpcArn" in params["outputs"]


def test_extract_from_stack_directory_not_found():
    """Test extraction from non-existent directory"""
    extractor = ParameterExtractor()
    result = extractor.extract_from_stack(Path("/nonexistent/path"))

    assert result["success"] is False
    assert "error" in result


def test_extract_from_stack_no_typescript_file(tmp_path):
    """Test extraction from directory without TypeScript file"""
    stack_dir = tmp_path / "empty-stack"
    stack_dir.mkdir()

    extractor = ParameterExtractor()
    result = extractor.extract_from_stack(stack_dir)

    assert result["success"] is False
    assert "No TypeScript file found" in result["error"]


def test_find_main_typescript_file_index_ts(tmp_path):
    """Test finding index.ts as main file"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()

    (stack_dir / "index.ts").write_text("// test")

    extractor = ParameterExtractor()
    ts_file = extractor._find_main_typescript_file(stack_dir, "stack")

    assert ts_file is not None
    assert ts_file.name == "index.ts"


def test_find_main_typescript_file_named_file(tmp_path):
    """Test finding <stack-name>.ts as main file"""
    stack_dir = tmp_path / "network"
    stack_dir.mkdir()

    (stack_dir / "network.ts").write_text("// test")

    extractor = ParameterExtractor()
    ts_file = extractor._find_main_typescript_file(stack_dir, "network")

    assert ts_file is not None
    assert ts_file.name == "network.ts"


def test_find_main_typescript_file_first_ts(tmp_path):
    """Test finding first .ts file"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()

    (stack_dir / "main.ts").write_text("// test")

    extractor = ParameterExtractor()
    ts_file = extractor._find_main_typescript_file(stack_dir, "stack")

    assert ts_file is not None
    assert ts_file.suffix == ".ts"


def test_find_main_typescript_file_none(tmp_path):
    """Test when no TypeScript file exists"""
    stack_dir = tmp_path / "stack"
    stack_dir.mkdir()

    extractor = ParameterExtractor()
    ts_file = extractor._find_main_typescript_file(stack_dir, "stack")

    assert ts_file is None


def test_convert_to_template_format():
    """Test converting ParseResult to template format"""
    from cloud_cli.parser.typescript_parser import ParseResult, InputParameter, OutputParameter

    result = ParseResult()
    result.inputs.append(InputParameter(
        name="vpcCidr",
        type="string",
        required=True,
        secret=False,
        description="VPC CIDR block"
    ))
    result.outputs.append(OutputParameter(
        name="vpcId",
        type="string",
        description="VPC ID"
    ))

    extractor = ParameterExtractor()
    template = extractor._convert_to_template_format(result)

    assert "inputs" in template
    assert "outputs" in template

    # Check input
    assert "vpcCidr" in template["inputs"]
    assert template["inputs"]["vpcCidr"]["type"] == "string"
    assert template["inputs"]["vpcCidr"]["required"] is True
    assert template["inputs"]["vpcCidr"]["description"] == "VPC CIDR block"

    # Check output
    assert "vpcId" in template["outputs"]
    assert template["outputs"]["vpcId"]["type"] == "string"
    assert template["outputs"]["vpcId"]["description"] == "VPC ID"


def test_convert_to_template_format_with_defaults():
    """Test template format conversion with default values"""
    from cloud_cli.parser.typescript_parser import ParseResult, InputParameter

    result = ParseResult()
    result.inputs.append(InputParameter(
        name="region",
        type="string",
        required=False,
        secret=False,
        default="us-east-1"
    ))

    extractor = ParameterExtractor()
    template = extractor._convert_to_template_format(result)

    assert template["inputs"]["region"]["default"] == "us-east-1"


def test_extract_from_multiple_stacks(tmp_path):
    """Test extracting from multiple stacks"""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create two stack directories
    for stack_name in ["network", "security"]:
        stack_dir = stacks_dir / stack_name
        stack_dir.mkdir()
        (stack_dir / "index.ts").write_text(f"""
        const config = new pulumi.Config();
        const param = config.require("param");
        export const output = "value";
        """)

    extractor = ParameterExtractor()
    results = extractor.extract_from_multiple_stacks(stacks_dir)

    assert len(results) == 2
    assert "network" in results
    assert "security" in results

    for result in results.values():
        assert result["success"] is True


def test_extract_from_multiple_stacks_specific_names(tmp_path):
    """Test extracting from specific stack names"""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create three stacks but only extract from two
    for stack_name in ["network", "security", "database"]:
        stack_dir = stacks_dir / stack_name
        stack_dir.mkdir()
        (stack_dir / "index.ts").write_text("export const output = 'value';")

    extractor = ParameterExtractor()
    results = extractor.extract_from_multiple_stacks(
        stacks_dir,
        stack_names=["network", "security"]
    )

    assert len(results) == 2
    assert "network" in results
    assert "security" in results
    assert "database" not in results


def test_generate_template_file(tmp_stack_dir, tmp_path):
    """Test generating template YAML file"""
    output_path = tmp_path / "templates" / "test-stack.yaml"

    extractor = ParameterExtractor()
    success, error = extractor.generate_template_file(
        tmp_stack_dir,
        output_path,
        "test-stack"
    )

    assert success is True
    assert error is None
    assert output_path.exists()

    # Verify content
    with open(output_path, 'r') as f:
        template = yaml.safe_load(f)

    assert template["name"] == "test-stack"
    assert "parameters" in template
    assert "inputs" in template["parameters"]
    assert "outputs" in template["parameters"]


def test_generate_template_file_extraction_failure(tmp_path):
    """Test template generation with extraction failure"""
    non_existent = tmp_path / "nonexistent"
    output_path = tmp_path / "output.yaml"

    extractor = ParameterExtractor()
    success, error = extractor.generate_template_file(
        non_existent,
        output_path
    )

    assert success is False
    assert error is not None


def test_compare_with_template_matching(tmp_stack_dir, tmp_path):
    """Test comparing with matching template"""
    # First extract parameters
    extractor = ParameterExtractor()
    extraction = extractor.extract_from_stack(tmp_stack_dir)

    # Create template file
    template_path = tmp_path / "template.yaml"
    template = {
        "name": "test-stack",
        "parameters": extraction["parameters"]
    }

    with open(template_path, 'w') as f:
        yaml.dump(template, f)

    # Compare
    result = extractor.compare_with_template(tmp_stack_dir, template_path)

    assert result["success"] is True
    assert result["is_synchronized"] is True
    assert len(result["differences"]["missing_in_template"]) == 0
    assert len(result["differences"]["missing_in_code"]) == 0


def test_compare_with_template_missing_in_template(tmp_stack_dir, tmp_path):
    """Test comparison when parameter is missing in template"""
    # Create template without one of the outputs
    template_path = tmp_path / "template.yaml"
    template = {
        "name": "test-stack",
        "parameters": {
            "inputs": {
                "vpcCidr": {"type": "string", "required": True},
                "region": {"type": "string", "required": False}
            },
            "outputs": {
                "vpcId": {"type": "string"}
                # vpcArn is missing
            }
        }
    }

    with open(template_path, 'w') as f:
        yaml.dump(template, f)

    extractor = ParameterExtractor()
    result = extractor.compare_with_template(tmp_stack_dir, template_path)

    assert result["success"] is True
    assert result["is_synchronized"] is False
    assert len(result["differences"]["missing_in_template"]) > 0
    assert "output:vpcArn" in result["differences"]["missing_in_template"]


def test_compare_with_template_missing_in_code(tmp_stack_dir, tmp_path):
    """Test comparison when parameter is in template but not code"""
    # Create template with extra output
    template_path = tmp_path / "template.yaml"
    template = {
        "name": "test-stack",
        "parameters": {
            "inputs": {
                "vpcCidr": {"type": "string", "required": True},
                "region": {"type": "string", "required": False}
            },
            "outputs": {
                "vpcId": {"type": "string"},
                "vpcArn": {"type": "string"},
                "extraOutput": {"type": "string"}  # Not in code
            }
        }
    }

    with open(template_path, 'w') as f:
        yaml.dump(template, f)

    extractor = ParameterExtractor()
    result = extractor.compare_with_template(tmp_stack_dir, template_path)

    assert result["success"] is True
    assert result["is_synchronized"] is False
    assert len(result["differences"]["missing_in_code"]) > 0
    assert "output:extraOutput" in result["differences"]["missing_in_code"]


def test_compare_with_template_type_mismatch(tmp_stack_dir, tmp_path):
    """Test comparison with type mismatches"""
    # Create template with wrong type
    template_path = tmp_path / "template.yaml"
    template = {
        "name": "test-stack",
        "parameters": {
            "inputs": {
                "vpcCidr": {"type": "number", "required": True},  # Wrong type
                "region": {"type": "string", "required": False}
            },
            "outputs": {
                "vpcId": {"type": "string"},
                "vpcArn": {"type": "string"}
            }
        }
    }

    with open(template_path, 'w') as f:
        yaml.dump(template, f)

    extractor = ParameterExtractor()
    result = extractor.compare_with_template(tmp_stack_dir, template_path)

    assert result["success"] is True
    assert len(result["differences"]["type_mismatches"]) > 0

    mismatches = result["differences"]["type_mismatches"]
    vpc_cidr_mismatch = next(m for m in mismatches if "vpcCidr" in m["parameter"])
    assert vpc_cidr_mismatch["code_type"] == "string"
    assert vpc_cidr_mismatch["template_type"] == "number"


def test_compare_with_template_load_error(tmp_stack_dir, tmp_path):
    """Test comparison with template load error"""
    non_existent_template = tmp_path / "nonexistent.yaml"

    extractor = ParameterExtractor()
    result = extractor.compare_with_template(tmp_stack_dir, non_existent_template)

    assert result["success"] is False
    assert "error" in result
