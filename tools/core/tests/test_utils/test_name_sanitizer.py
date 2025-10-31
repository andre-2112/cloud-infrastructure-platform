"""Tests for name_sanitizer utility"""

import pytest
from cloud_core.utils.name_sanitizer import sanitize_name, sanitize_org_and_project


class TestSanitizeName:
    """Test suite for sanitize_name function"""

    def test_sanitize_simple_name(self):
        """Test sanitizing a simple alphanumeric name"""
        assert sanitize_name("MyCompany") == "MyCompany"
        assert sanitize_name("Project123") == "Project123"
        assert sanitize_name("test") == "test"

    def test_sanitize_name_with_spaces(self):
        """Test sanitizing names with spaces"""
        assert sanitize_name("My Company") == "My_Company"
        assert sanitize_name("Test Project") == "Test_Project"
        assert sanitize_name("Web App 2.0") == "Web_App_2_0"

    def test_sanitize_name_with_multiple_spaces(self):
        """Test sanitizing names with consecutive spaces"""
        assert sanitize_name("My   Company") == "My_Company"
        assert sanitize_name("Test     Project") == "Test_Project"
        assert sanitize_name("A  B  C") == "A_B_C"

    def test_sanitize_name_with_special_characters(self):
        """Test sanitizing names with special characters"""
        assert sanitize_name("My Company!") == "My_Company"
        assert sanitize_name("Company@Test") == "Company_Test"
        assert sanitize_name("Project#123") == "Project_123"
        assert sanitize_name("Web-App") == "Web_App"
        assert sanitize_name("Company & Co.") == "Company_Co"

    def test_sanitize_name_with_mixed_special_chars_and_spaces(self):
        """Test sanitizing names with mixed spaces and special characters"""
        assert sanitize_name("My Company @ Test!") == "My_Company_Test"
        assert sanitize_name("Web App 2.0!") == "Web_App_2_0"
        assert sanitize_name("Test & Development Project") == "Test_Development_Project"
        assert sanitize_name("Company (USA)") == "Company_USA"

    def test_sanitize_name_with_consecutive_special_chars(self):
        """Test sanitizing names with consecutive special characters"""
        assert sanitize_name("Company@#$Test") == "Company_Test"
        assert sanitize_name("Project!!!") == "Project"
        assert sanitize_name("Web---App") == "Web_App"
        assert sanitize_name("Test...123") == "Test_123"

    def test_sanitize_name_leading_trailing_spaces(self):
        """Test sanitizing names with leading/trailing spaces"""
        assert sanitize_name("  Company  ") == "Company"
        assert sanitize_name("   Test   ") == "Test"
        assert sanitize_name("  My Company  ") == "My_Company"

    def test_sanitize_name_leading_trailing_special_chars(self):
        """Test sanitizing names with leading/trailing special characters"""
        assert sanitize_name("!Company!") == "Company"
        assert sanitize_name("@Test@") == "Test"
        assert sanitize_name("_Company_") == "Company"
        assert sanitize_name("-Project-") == "Project"

    def test_sanitize_name_only_alphanumeric_unchanged(self):
        """Test that purely alphanumeric names are unchanged"""
        assert sanitize_name("TestOrg") == "TestOrg"
        assert sanitize_name("TestProject") == "TestProject"
        assert sanitize_name("Company123") == "Company123"
        assert sanitize_name("ABC") == "ABC"

    def test_sanitize_name_empty_string(self):
        """Test sanitizing empty string"""
        assert sanitize_name("") == ""

    def test_sanitize_name_only_spaces(self):
        """Test sanitizing string with only spaces"""
        assert sanitize_name("   ") == ""
        assert sanitize_name("     ") == ""

    def test_sanitize_name_only_special_chars(self):
        """Test sanitizing string with only special characters"""
        assert sanitize_name("!!!") == ""
        assert sanitize_name("@@@") == ""
        assert sanitize_name("---") == ""

    def test_sanitize_name_mixed_case_preserved(self):
        """Test that mixed case is preserved"""
        assert sanitize_name("MyCompany") == "MyCompany"
        assert sanitize_name("TestOrg") == "TestOrg"
        assert sanitize_name("My Company Test") == "My_Company_Test"

    def test_sanitize_name_numbers_preserved(self):
        """Test that numbers are preserved"""
        assert sanitize_name("Company123") == "Company123"
        assert sanitize_name("Test 2.0") == "Test_2_0"
        assert sanitize_name("Version 1.2.3") == "Version_1_2_3"

    def test_sanitize_name_unicode_characters(self):
        """Test sanitizing names with unicode characters"""
        # Unicode special chars should be replaced
        assert sanitize_name("Company™") == "Company"
        assert sanitize_name("Test©") == "Test"
        assert sanitize_name("Project®") == "Project"

    def test_sanitize_name_underscores(self):
        """Test that existing underscores are handled"""
        # Single underscores between alphanumeric should be replaced
        assert sanitize_name("My_Company") == "My_Company"
        assert sanitize_name("Test___Project") == "Test_Project"  # Multiple underscores collapsed

    def test_sanitize_name_real_world_examples(self):
        """Test real-world company/project names"""
        assert sanitize_name("Acme Corp.") == "Acme_Corp"
        assert sanitize_name("Smith & Associates") == "Smith_Associates"
        assert sanitize_name("Web Development (2024)") == "Web_Development_2024"
        assert sanitize_name("Project Alpha-Beta") == "Project_Alpha_Beta"
        assert sanitize_name("Company, LLC") == "Company_LLC"


class TestSanitizeOrgAndProject:
    """Test suite for sanitize_org_and_project function"""

    def test_sanitize_both_names(self):
        """Test sanitizing both organization and project names"""
        org, project = sanitize_org_and_project("My Company", "Test Project")
        assert org == "My_Company"
        assert project == "Test_Project"

    def test_sanitize_with_special_chars(self):
        """Test sanitizing both names with special characters"""
        org, project = sanitize_org_and_project("Company @ Test!", "Web App 2.0")
        assert org == "Company_Test"
        assert project == "Web_App_2_0"

    def test_sanitize_already_clean_names(self):
        """Test that clean names are unchanged"""
        org, project = sanitize_org_and_project("TestOrg", "TestProject")
        assert org == "TestOrg"
        assert project == "TestProject"

    def test_sanitize_empty_names(self):
        """Test sanitizing empty names"""
        org, project = sanitize_org_and_project("", "")
        assert org == ""
        assert project == ""

    def test_sanitize_one_dirty_one_clean(self):
        """Test sanitizing when only one name needs cleaning"""
        org, project = sanitize_org_and_project("My Company!", "TestProject")
        assert org == "My_Company"
        assert project == "TestProject"

        org, project = sanitize_org_and_project("TestOrg", "Test Project")
        assert org == "TestOrg"
        assert project == "Test_Project"


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""

    def test_very_long_name(self):
        """Test sanitizing a very long name"""
        long_name = "A" * 100 + " " + "B" * 100
        result = sanitize_name(long_name)
        assert result == "A" * 100 + "_" + "B" * 100

    def test_alternating_chars_and_spaces(self):
        """Test alternating characters and spaces"""
        assert sanitize_name("A B C D E") == "A_B_C_D_E"
        assert sanitize_name("1 2 3 4") == "1_2_3_4"

    def test_mixed_separators(self):
        """Test names with mixed separator characters"""
        assert sanitize_name("Test-Project_Name.Final") == "Test_Project_Name_Final"
        assert sanitize_name("Company|Division/Team") == "Company_Division_Team"

    def test_repeated_underscores_collapsed(self):
        """Test that repeated underscores are collapsed to single underscore"""
        assert sanitize_name("Test___Project") == "Test_Project"
        assert sanitize_name("A____B____C") == "A_B_C"


class TestIntegration:
    """Integration tests for real-world scenarios"""

    def test_deployment_directory_naming(self):
        """Test that sanitized names work for deployment directory naming"""
        org = "My Company @ Test!"
        project = "Web App 2.0"
        deployment_id = "D1BRV40"

        org_sanitized, project_sanitized = sanitize_org_and_project(org, project)

        # Should be safe for directory names
        dir_name = f"{deployment_id}-{org_sanitized}-{project_sanitized}"
        assert dir_name == "D1BRV40-My_Company_Test-Web_App_2_0"

        # Should not contain problematic characters
        assert "@" not in dir_name
        assert "!" not in dir_name
        assert "." not in dir_name
        assert " " not in dir_name

    def test_pulumi_project_naming(self):
        """Test that sanitized names work for Pulumi project naming"""
        org = "Company (USA)"
        project = "Project-Alpha"
        deployment_id = "DABC123"

        org_sanitized, project_sanitized = sanitize_org_and_project(org, project)

        # Create composite project name
        composite_project = f"{deployment_id}-{org_sanitized}-{project_sanitized}"
        assert composite_project == "DABC123-Company_USA-Project_Alpha"

        # Should be valid for Pulumi (alphanumeric, dash, underscore)
        assert all(c.isalnum() or c in "-_" for c in composite_project)

    def test_aws_resource_naming(self):
        """Test that sanitized names work for AWS resource naming"""
        org = "Test & Development"
        project = "API Gateway v2"

        org_sanitized, project_sanitized = sanitize_org_and_project(org, project)

        # Should be safe for AWS resource tags
        assert org_sanitized == "Test_Development"
        assert project_sanitized == "API_Gateway_v2"

        # AWS allows alphanumeric, underscore, dash, space
        # Our sanitized version uses only alphanumeric and underscore
        assert all(c.isalnum() or c == "_" for c in org_sanitized)
        assert all(c.isalnum() or c == "_" for c in project_sanitized)
