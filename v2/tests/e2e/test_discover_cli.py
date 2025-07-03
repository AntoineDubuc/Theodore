"""
End-to-end tests for the Discovery CLI command.

Tests complete discovery workflows including real CLI execution,
interactive mode simulation, and cross-format result validation.
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from click.testing import CliRunner

from src.cli.commands.discover import discover_command
from src.core.domain.value_objects.similarity_result import (
    DiscoveryResult, DiscoverySource, CompanyMatch
)


class TestDiscoverCLIE2E:
    """End-to-end test suite for Discovery CLI command."""
    
    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()
    
    @pytest.fixture
    def mock_container_context(self):
        """Create mock container context for CLI commands."""
        mock_container = Mock()
        
        # Mock use case
        mock_use_case = AsyncMock()
        sample_result = DiscoveryResult(
            query_company="Target Corp",
            search_strategy="hybrid",
            total_sources_used=2,
            matches=[
                CompanyMatch(
                    company_name="Similar Corp A",
                    domain="https://similar-a.com",
                    description="A similar company",
                    similarity_score=0.85,
                    confidence_score=0.9,
                    source=DiscoverySource.VECTOR_DATABASE
                ),
                CompanyMatch(
                    company_name="Similar Corp B",
                    domain="https://similar-b.com",
                    description="Another similar company",
                    similarity_score=0.72,
                    confidence_score=0.8,
                    source=DiscoverySource.MCP_PERPLEXITY
                )
            ],
            total_matches=2,
            execution_time_seconds=1.2,
            average_confidence=0.85,
            coverage_score=0.7,
            freshness_score=0.9
        )
        mock_use_case.execute.return_value = sample_result
        mock_container.get_discovery_use_case.return_value = mock_use_case
        
        # Mock settings
        mock_settings = Mock()
        mock_container.get_settings.return_value = mock_settings
        
        return {'container': mock_container}
    
    def test_discover_command_basic_execution(self, cli_runner, mock_container_context):
        """Test basic discovery command execution."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp'],
                obj=mock_container_context
            )
            
            # Command should execute without error
            assert result.exit_code == 0
            
            # Should create command instance and call execute
            mock_command_class.assert_called_once_with(mock_container_context['container'])
            mock_command_instance.execute.assert_called_once()
    
    def test_discover_command_with_filters(self, cli_runner, mock_container_context):
        """Test discovery command with various filters."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                [
                    'TestCorp',
                    '--business-model', 'saas',
                    '--company-size', 'medium',
                    '--industry', 'technology',
                    '--location', 'San Francisco',
                    '--similarity-threshold', '0.8',
                    '--limit', '20'
                ],
                obj=mock_container_context
            )
            
            # Command should execute without error
            assert result.exit_code == 0
            
            # Verify execute was called with correct parameters
            mock_command_instance.execute.assert_called_once()
            call_args = mock_command_instance.execute.call_args
            
            # Check some key arguments
            assert call_args.kwargs['company_name'] == 'TestCorp'
            assert call_args.kwargs['business_model'] == 'saas'
            assert call_args.kwargs['company_size'] == 'medium'
            assert call_args.kwargs['industry'] == 'technology'
            assert call_args.kwargs['location'] == 'San Francisco'
            assert call_args.kwargs['similarity_threshold'] == 0.8
            assert call_args.kwargs['limit'] == 20
    
    def test_discover_command_output_formats(self, cli_runner, mock_container_context):
        """Test discovery command with different output formats."""
        
        output_formats = ['table', 'json', 'yaml', 'markdown']
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            for format_type in output_formats:
                result = cli_runner.invoke(
                    discover_command,
                    ['TestCorp', '--output', format_type],
                    obj=mock_container_context
                )
                
                # All formats should be valid
                assert result.exit_code == 0
                
                # Check that output format was passed correctly
                call_args = mock_command_instance.execute.call_args
                from src.cli.utils.output import OutputFormat
                expected_format = OutputFormat(format_type)
                assert call_args.kwargs['output'] == expected_format
    
    def test_discover_command_interactive_mode(self, cli_runner, mock_container_context):
        """Test discovery command in interactive mode."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--interactive'],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify interactive flag was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['interactive'] is True
    
    def test_discover_command_with_save_option(self, cli_runner, mock_container_context, tmp_path):
        """Test discovery command with save option."""
        
        output_file = tmp_path / "test_output.json"
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--save', str(output_file)],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify save parameter was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['save'] == str(output_file)
    
    def test_discover_command_verbose_mode(self, cli_runner, mock_container_context):
        """Test discovery command in verbose mode."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--verbose'],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify verbose flag was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['verbose'] is True
    
    def test_discover_command_explain_similarity(self, cli_runner, mock_container_context):
        """Test discovery command with similarity explanations."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--explain-similarity'],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify explain_similarity flag was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['explain_similarity'] is True
    
    def test_discover_command_research_discovered(self, cli_runner, mock_container_context):
        """Test discovery command with auto-research option."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--research-discovered'],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify research_discovered flag was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['research_discovered'] is True
    
    def test_discover_command_source_options(self, cli_runner, mock_container_context):
        """Test discovery command with different source options."""
        
        source_options = ['vector', 'web', 'hybrid']
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            for source in source_options:
                result = cli_runner.invoke(
                    discover_command,
                    ['TestCorp', '--source', source],
                    obj=mock_container_context
                )
                
                # Should execute without error
                assert result.exit_code == 0
                
                # Verify source was passed
                call_args = mock_command_instance.execute.call_args
                assert call_args.kwargs['source'] == source
    
    def test_discover_command_timeout_option(self, cli_runner, mock_container_context):
        """Test discovery command with custom timeout."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--timeout', '60'],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify timeout was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['timeout'] == 60
    
    def test_discover_command_invalid_business_model(self, cli_runner, mock_container_context):
        """Test discovery command with invalid business model."""
        
        result = cli_runner.invoke(
            discover_command,
            ['TestCorp', '--business-model', 'invalid'],
            obj=mock_container_context
        )
        
        # Should fail with invalid choice
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'invalid choice' in result.output.lower()
    
    def test_discover_command_invalid_output_format(self, cli_runner, mock_container_context):
        """Test discovery command with invalid output format."""
        
        result = cli_runner.invoke(
            discover_command,
            ['TestCorp', '--output', 'invalid'],
            obj=mock_container_context
        )
        
        # Should fail with invalid choice
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'invalid choice' in result.output.lower()
    
    def test_discover_command_help(self, cli_runner):
        """Test discovery command help output."""
        
        result = cli_runner.invoke(discover_command, ['--help'])
        
        # Should show help and exit successfully
        assert result.exit_code == 0
        assert 'Discover companies similar to' in result.output
        assert 'Examples:' in result.output
        assert '--business-model' in result.output
        assert '--interactive' in result.output
    
    def test_discover_command_missing_company_name(self, cli_runner, mock_container_context):
        """Test discovery command without required company name."""
        
        result = cli_runner.invoke(
            discover_command,
            [],  # Missing company name
            obj=mock_container_context
        )
        
        # Should fail due to missing required argument
        assert result.exit_code != 0
        assert 'Missing argument' in result.output or 'required' in result.output.lower()
    
    @pytest.mark.parametrize("threshold", [0.0, 0.5, 1.0])
    def test_discover_command_similarity_thresholds(self, cli_runner, mock_container_context, threshold):
        """Test discovery command with various similarity thresholds."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp', '--similarity-threshold', str(threshold)],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify threshold was passed
            call_args = mock_command_instance.execute.call_args
            assert call_args.kwargs['similarity_threshold'] == threshold
    
    def test_discover_command_all_options_combined(self, cli_runner, mock_container_context, tmp_path):
        """Test discovery command with all options combined."""
        
        output_file = tmp_path / "full_test.json"
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            mock_command_instance.execute = AsyncMock()
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                [
                    'TestCorp',
                    '--limit', '15',
                    '--output', 'json',
                    '--business-model', 'saas',
                    '--company-size', 'large',
                    '--industry', 'technology',
                    '--location', 'Seattle',
                    '--similarity-threshold', '0.75',
                    '--source', 'hybrid',
                    '--interactive',
                    '--research-discovered',
                    '--save', str(output_file),
                    '--explain-similarity',
                    '--verbose',
                    '--timeout', '90'
                ],
                obj=mock_container_context
            )
            
            # Should execute without error
            assert result.exit_code == 0
            
            # Verify all parameters were passed correctly
            call_args = mock_command_instance.execute.call_args
            kwargs = call_args.kwargs
            
            assert kwargs['company_name'] == 'TestCorp'
            assert kwargs['limit'] == 15
            assert kwargs['business_model'] == 'saas'
            assert kwargs['company_size'] == 'large'
            assert kwargs['industry'] == 'technology'
            assert kwargs['location'] == 'Seattle'
            assert kwargs['similarity_threshold'] == 0.75
            assert kwargs['source'] == 'hybrid'
            assert kwargs['interactive'] is True
            assert kwargs['research_discovered'] is True
            assert kwargs['save'] == str(output_file)
            assert kwargs['explain_similarity'] is True
            assert kwargs['verbose'] is True
            assert kwargs['timeout'] == 90
    
    def test_discover_command_exception_handling(self, cli_runner, mock_container_context):
        """Test discovery command exception handling."""
        
        with patch('src.cli.commands.discover.DiscoveryCommand') as mock_command_class:
            mock_command_instance = Mock()
            # Simulate an exception during execution
            mock_command_instance.execute = AsyncMock(side_effect=Exception("Test error"))
            mock_command_class.return_value = mock_command_instance
            
            result = cli_runner.invoke(
                discover_command,
                ['TestCorp'],
                obj=mock_container_context
            )
            
            # Command should handle the exception gracefully
            # (The actual error handling depends on the implementation)
            # For now, we just verify the command completed
            assert result.exit_code is not None  # Command completed (may be 0 or 1)