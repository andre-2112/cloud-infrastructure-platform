"""Tests for TypeScript parser"""

import pytest
from pathlib import Path
from cloud_cli.parser.typescript_parser import (
    TypeScriptParser,
    InputParameter,
    OutputParameter,
    ParseResult
)


def test_typescript_parser_init():
    """Test TypeScriptParser initialization"""
    parser = TypeScriptParser()
    assert parser is not None
    assert parser.result is not None


def test_parse_simple_input():
    """Test parsing a simple config.require() input"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 1
    assert result.inputs[0].name == "vpcId"
    assert result.inputs[0].required is True
    assert result.inputs[0].type == "string"


def test_parse_multiple_inputs():
    """Test parsing multiple inputs"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    const region = config.get("region", "us-east-1");
    const enableLogging = config.getBoolean("enableLogging");
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 3

    # Check vpcId (required)
    vpc_input = next(i for i in result.inputs if i.name == "vpcId")
    assert vpc_input.required is True

    # Check region (optional with default)
    region_input = next(i for i in result.inputs if i.name == "region")
    assert region_input.required is False

    # Check enableLogging (boolean)
    logging_input = next(i for i in result.inputs if i.name == "enableLogging")
    assert logging_input.type == "boolean"


def test_parse_secret_inputs():
    """Test parsing secret inputs"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const dbPassword = config.requireSecret("dbPassword");
    const apiKey = config.getSecret("apiKey");
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 2

    for input_param in result.inputs:
        assert input_param.secret is True


def test_parse_typed_inputs():
    """Test parsing typed config methods"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const port = config.requireNumber("port");
    const enabled = config.getBoolean("enabled", true);
    const settings = config.getObject("settings");
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 3

    port = next(i for i in result.inputs if i.name == "port")
    assert port.type == "number"

    enabled = next(i for i in result.inputs if i.name == "enabled")
    assert enabled.type == "boolean"

    settings = next(i for i in result.inputs if i.name == "settings")
    assert settings.type == "object"


def test_parse_simple_output():
    """Test parsing a simple export statement"""
    parser = TypeScriptParser()
    source = """
    export const vpcId = vpc.id;
    """

    result = parser.parse_source(source)

    assert len(result.outputs) == 1
    assert result.outputs[0].name == "vpcId"


def test_parse_multiple_outputs():
    """Test parsing multiple export statements"""
    parser = TypeScriptParser()
    source = """
    export const vpcId = vpc.id;
    export const subnetIds = subnets.map(s => s.id);
    export const securityGroupId = sg.id;
    """

    result = parser.parse_source(source)

    assert len(result.outputs) == 3

    output_names = [o.name for o in result.outputs]
    assert "vpcId" in output_names
    assert "subnetIds" in output_names
    assert "securityGroupId" in output_names


def test_parse_inputs_and_outputs():
    """Test parsing both inputs and outputs"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcCidr = config.require("vpcCidr");
    const region = config.get("region", "us-east-1");

    const vpc = new aws.ec2.Vpc("main", { cidrBlock: vpcCidr });

    export const vpcId = vpc.id;
    export const vpcArn = vpc.arn;
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 2
    assert len(result.outputs) == 2


def test_parse_with_comments():
    """Test parsing code with inline comments"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcCidr = config.require("vpcCidr");  // VPC CIDR block
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 1
    input_param = result.inputs[0]
    assert input_param.description == "VPC CIDR block"


def test_parse_file(tmp_path):
    """Test parsing from a file"""
    parser = TypeScriptParser()

    # Create a test TypeScript file
    test_file = tmp_path / "test.ts"
    test_file.write_text("""
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    export const outputVpc = vpcId;
    """)

    result = parser.parse_file(test_file)

    assert len(result.inputs) == 1
    assert len(result.outputs) == 1


def test_parse_file_not_found(tmp_path):
    """Test parsing a non-existent file"""
    parser = TypeScriptParser()
    non_existent = tmp_path / "nonexistent.ts"

    result = parser.parse_file(non_existent)

    assert len(result.errors) > 0


def test_extract_inputs_convenience():
    """Test extract_inputs convenience method"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    """

    inputs = parser.extract_inputs(source)

    assert len(inputs) == 1
    assert inputs[0].name == "vpcId"


def test_extract_outputs_convenience():
    """Test extract_outputs convenience method"""
    parser = TypeScriptParser()
    source = """
    export const vpcId = vpc.id;
    """

    outputs = parser.extract_outputs(source)

    assert len(outputs) == 1
    assert outputs[0].name == "vpcId"


def test_validate_extraction_success():
    """Test validation with successful parsing"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    """

    parser.parse_source(source)

    assert parser.validate_extraction() is True


def test_validate_extraction_failure():
    """Test validation with parsing errors"""
    parser = TypeScriptParser()

    # Simulate an error
    parser.result.errors.append("Test error")

    assert parser.validate_extraction() is False


def test_get_errors():
    """Test getting errors"""
    parser = TypeScriptParser()

    parser.result.errors.append("Error 1")
    parser.result.errors.append("Error 2")

    errors = parser.get_errors()

    assert len(errors) == 2
    assert "Error 1" in errors


def test_get_warnings():
    """Test getting warnings"""
    parser = TypeScriptParser()

    parser.result.warnings.append("Warning 1")

    warnings = parser.get_warnings()

    assert len(warnings) == 1
    assert "Warning 1" in warnings


def test_input_parameter_dataclass():
    """Test InputParameter dataclass"""
    param = InputParameter(
        name="vpcId",
        type="string",
        required=True,
        secret=False
    )

    assert param.name == "vpcId"
    assert param.type == "string"
    assert param.required is True
    assert param.secret is False
    assert param.default is None


def test_output_parameter_dataclass():
    """Test OutputParameter dataclass"""
    param = OutputParameter(
        name="vpcId",
        type="string",
        description="The VPC ID"
    )

    assert param.name == "vpcId"
    assert param.type == "string"
    assert param.description == "The VPC ID"


def test_parse_result_dataclass():
    """Test ParseResult dataclass"""
    result = ParseResult()

    assert len(result.inputs) == 0
    assert len(result.outputs) == 0
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_parse_deduplicate_inputs():
    """Test that duplicate inputs are not added"""
    parser = TypeScriptParser()
    source = """
    const config = new pulumi.Config();
    const vpcId = config.require("vpcId");
    const vpcIdAgain = config.require("vpcId");  // Same parameter
    """

    result = parser.parse_source(source)

    # Should only have one vpcId input
    assert len(result.inputs) == 1
    assert result.inputs[0].name == "vpcId"


def test_parse_deduplicate_outputs():
    """Test that duplicate outputs are not added"""
    parser = TypeScriptParser()
    source = """
    export const vpcId = vpc.id;
    export let vpcId = vpc.id;  // Duplicate
    """

    result = parser.parse_source(source)

    # Should only have one vpcId output
    assert len(result.outputs) == 1
    assert result.outputs[0].name == "vpcId"


def test_parse_empty_source():
    """Test parsing empty source code"""
    parser = TypeScriptParser()
    source = ""

    result = parser.parse_source(source)

    assert len(result.inputs) == 0
    assert len(result.outputs) == 0
    assert len(result.errors) == 0


def test_parse_complex_real_world_stack():
    """Test parsing a complex real-world stack"""
    parser = TypeScriptParser()
    source = """
    import * as pulumi from "@pulumi/pulumi";
    import * as aws from "@pulumi/aws";

    const config = new pulumi.Config();

    // Inputs
    const vpcCidr = config.require("vpcCidr");
    const region = config.get("region", "us-east-1");
    const enableNatGateway = config.getBoolean("enableNatGateway", true);
    const availabilityZones = config.requireNumber("availabilityZones");
    const tags = config.getObject("tags");

    // Resources
    const vpc = new aws.ec2.Vpc("main", {
        cidrBlock: vpcCidr,
        tags: tags as any,
    });

    // Outputs
    export const vpcId = vpc.id;
    export const vpcArn = vpc.arn;
    export const vpcCidrBlock = vpc.cidrBlock;
    """

    result = parser.parse_source(source)

    assert len(result.inputs) == 5
    assert len(result.outputs) == 3

    # Verify input types
    input_names = {i.name: i for i in result.inputs}
    assert input_names["vpcCidr"].required is True
    assert input_names["region"].required is False
    assert input_names["enableNatGateway"].type == "boolean"
    assert input_names["availabilityZones"].type == "number"
    assert input_names["tags"].type == "object"

    # Verify outputs
    output_names = [o.name for o in result.outputs]
    assert "vpcId" in output_names
    assert "vpcArn" in output_names
    assert "vpcCidrBlock" in output_names
