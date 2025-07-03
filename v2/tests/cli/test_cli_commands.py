"""
CLI command tests for Theodore v2.
"""

import pytest
from click.testing import CliRunner
from src.cli.main import cli
import json


class TestCLICommands:
    """Test CLI command functionality"""
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main CLI help"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Theodore AI Company Intelligence System" in result.output
        assert "research" in result.output
        assert "discover" in result.output
        assert "export" in result.output
        assert "config" in result.output
        assert "plugin" in result.output
    
    def test_version_flag(self):
        """Test version flag"""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "2.0.0" in result.output
        assert "Theodore AI Company Intelligence" in result.output
    
    def test_verbose_flag(self):
        """Test verbose flag"""
        result = self.runner.invoke(cli, ['--verbose', 'research', '--help'])
        assert result.exit_code == 0
        assert "Verbose mode enabled" in result.output
    
    def test_research_company_command(self):
        """Test research company command"""
        result = self.runner.invoke(cli, [
            'research', 'company', 'Test Corp', '--output', 'table'
        ])
        assert result.exit_code == 0
        assert "Test Corp" in result.output
        assert "Company Research Results" in result.output
        assert "Technology" in result.output
    
    def test_research_company_json_output(self):
        """Test research company with JSON output"""
        result = self.runner.invoke(cli, [
            'research', 'company', 'Acme Corp', 'https://acme.com', 
            '--output', 'json'
        ])
        assert result.exit_code == 0
        
        # Parse JSON output to verify structure
        try:
            output_lines = result.output.strip().split('\n')
            # Find JSON content (after progress indicator)
            json_start = -1
            for i, line in enumerate(output_lines):
                if line.strip().startswith('{'):
                    json_start = i
                    break
            
            if json_start >= 0:
                json_content = '\n'.join(output_lines[json_start:])
                data = json.loads(json_content)
                assert data["company_name"] == "Acme Corp"
                assert data["website"] == "https://acme.com"
                assert "industry" in data
        except (json.JSONDecodeError, KeyError) as e:
            pytest.fail(f"Invalid JSON output: {e}")
    
    def test_research_company_csv_output(self):
        """Test research company with CSV output"""
        result = self.runner.invoke(cli, [
            'research', 'company', 'CSV Corp', '--output', 'csv'
        ])
        assert result.exit_code == 0
        assert "company_name,website,industry" in result.output
        assert "CSV Corp" in result.output
    
    def test_research_batch_command(self):
        """Test research batch command (placeholder)"""
        # Create temporary CSV file
        with self.runner.isolated_filesystem():
            with open('companies.csv', 'w') as f:
                f.write('name,website\nTest Corp,test.com\n')
            
            result = self.runner.invoke(cli, [
                'research', 'batch', 'companies.csv'
            ])
            assert result.exit_code == 0
            assert "batch research" in result.output.lower()
            assert "not implemented yet" in result.output
    
    def test_discover_similar_command(self):
        """Test discover similar command"""
        result = self.runner.invoke(cli, [
            'discover', 'similar', 'Stripe', '--limit', '3', '--min-confidence', '0.7'
        ])
        assert result.exit_code == 0
        assert "Discovering companies similar to Stripe" in result.output
        assert "Similar Corp" in result.output
        assert "Confidence" in result.output
    
    def test_discover_similar_no_results(self):
        """Test discover similar with high confidence threshold"""
        result = self.runner.invoke(cli, [
            'discover', 'similar', 'Unknown Corp', '--min-confidence', '0.95'
        ])
        assert result.exit_code == 0
        assert "No similar companies found" in result.output
    
    def test_discover_similar_json_export(self):
        """Test discover similar with JSON export"""
        result = self.runner.invoke(cli, [
            'discover', 'similar', 'Salesforce', '--export-format', 'json'
        ])
        assert result.exit_code == 0
        assert "source_company" in result.output
        assert "similar_companies" in result.output
    
    def test_discover_competitors_command(self):
        """Test discover competitors command (placeholder)"""
        result = self.runner.invoke(cli, [
            'discover', 'competitors', 'Slack', '--industry', 'Communication'
        ])
        assert result.exit_code == 0
        assert "Finding competitors of Slack" in result.output
        assert "not implemented yet" in result.output
    
    def test_export_companies_command(self):
        """Test export companies command (placeholder)"""
        result = self.runner.invoke(cli, [
            'export', 'companies', '--format', 'json', '--output', 'test.json'
        ])
        assert result.exit_code == 0
        assert "Exporting companies to test.json" in result.output
        assert "not implemented yet" in result.output
    
    def test_export_report_command(self):
        """Test export report command (placeholder)"""
        result = self.runner.invoke(cli, [
            'export', 'report', 'GitHub', '--format', 'pdf', '--include-similar'
        ])
        assert result.exit_code == 0
        assert "Generating PDF report for GitHub" in result.output
        assert "Including similar companies" in result.output
    
    def test_config_show_command(self):
        """Test config show command"""
        result = self.runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
        assert "Theodore Configuration" in result.output
        assert "AI Models" in result.output
        assert "Search Settings" in result.output
    
    def test_config_set_command(self):
        """Test config set command (placeholder)"""
        result = self.runner.invoke(cli, [
            'config', 'set', 'ai.primary_model', 'gpt-4'
        ])
        assert result.exit_code == 0
        assert "Setting project config" in result.output
        assert "ai.primary_model = gpt-4" in result.output
    
    def test_config_get_command(self):
        """Test config get command"""
        result = self.runner.invoke(cli, [
            'config', 'get', 'ai.primary_model'
        ])
        assert result.exit_code == 0
        assert "ai.primary_model" in result.output
        assert "gemini-2.0-flash-exp" in result.output
    
    def test_config_validate_command(self):
        """Test config validate command"""
        result = self.runner.invoke(cli, ['config', 'validate'])
        assert result.exit_code == 0
        assert "Validating Theodore configuration" in result.output
        assert "Configuration Validation" in result.output
    
    def test_plugin_list_command(self):
        """Test plugin list command"""
        result = self.runner.invoke(cli, ['plugin', 'list'])
        assert result.exit_code == 0
        assert "Installed Theodore Plugins" in result.output
        assert "mcp-perplexity" in result.output
        assert "enabled" in result.output
    
    def test_plugin_info_command(self):
        """Test plugin info command"""
        result = self.runner.invoke(cli, ['plugin', 'info', 'mcp-perplexity'])
        assert result.exit_code == 0
        assert "Plugin Information: mcp-perplexity" in result.output
        assert "Version" in result.output
        assert "Author" in result.output
    
    def test_plugin_install_command(self):
        """Test plugin install command (placeholder)"""
        result = self.runner.invoke(cli, [
            'plugin', 'install', 'new-plugin', '--version', '1.0.0'
        ])
        assert result.exit_code == 0
        assert "Installing plugin: new-plugin" in result.output
        assert "not implemented yet" in result.output
    
    def test_command_help_consistency(self):
        """Test that all commands have proper help"""
        commands_to_test = [
            ['research', '--help'],
            ['research', 'company', '--help'],
            ['research', 'batch', '--help'],
            ['discover', '--help'],
            ['discover', 'similar', '--help'],
            ['discover', 'competitors', '--help'],
            ['export', '--help'],
            ['export', 'companies', '--help'],
            ['export', 'report', '--help'],
            ['config', '--help'],
            ['plugin', '--help']
        ]
        
        for cmd in commands_to_test:
            result = self.runner.invoke(cli, cmd)
            assert result.exit_code == 0, f"Help failed for command: {' '.join(cmd)}"
            assert "Usage:" in result.output
            assert "Examples:" in result.output or "help" in result.output.lower()
    
    def test_error_handling(self):
        """Test error handling for invalid commands"""
        # Invalid command
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        
        # Invalid option
        result = self.runner.invoke(cli, ['research', 'company', '--invalid-option'])
        assert result.exit_code != 0
        
        # Missing required argument
        result = self.runner.invoke(cli, ['research', 'company'])
        assert result.exit_code != 0
    
    def test_option_validation(self):
        """Test option validation"""
        # Invalid output format
        result = self.runner.invoke(cli, [
            'research', 'company', 'Test', '--output', 'invalid'
        ])
        assert result.exit_code != 0
        
        # Invalid confidence range
        result = self.runner.invoke(cli, [
            'discover', 'similar', 'Test', '--min-confidence', '1.5'
        ])
        assert result.exit_code != 0
        
        # Invalid limit range
        result = self.runner.invoke(cli, [
            'discover', 'similar', 'Test', '--limit', '0'
        ])
        assert result.exit_code != 0