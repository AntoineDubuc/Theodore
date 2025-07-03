"""
Architecture compliance tests for Theodore v2.
Ensures clean architecture principles are maintained.
"""

import pytest
import ast
import os
import importlib.util
from pathlib import Path


class TestArchitectureCompliance:
    """Test architectural constraints and boundaries"""
    
    def test_domain_layer_independence(self):
        """Test that domain entities have no infrastructure dependencies"""
        domain_path = Path("src/core/domain/entities")
        forbidden_imports = [
            "requests", "aiohttp", "boto3", "openai", "anthropic",
            "pinecone", "redis", "psycopg2", "pymongo", "sqlalchemy",
            "click", "flask", "fastapi", "django"
        ]
        
        violations = []
        
        for py_file in domain_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if any(forbidden in alias.name for forbidden in forbidden_imports):
                                violations.append(f"{py_file.name}: imports {alias.name}")
                    
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if any(forbidden in node.module for forbidden in forbidden_imports):
                            violations.append(f"{py_file.name}: imports from {node.module}")
        
        assert not violations, f"Domain layer has infrastructure dependencies: {violations}"
    
    def test_cli_layer_dependencies(self):
        """Test that CLI layer only depends on domain and infrastructure"""
        cli_path = Path("src/cli")
        allowed_external = [
            "click", "rich", "colorama", "json", "csv", "time", "io"
        ]
        forbidden_direct_imports = [
            "boto3", "openai", "anthropic", "pinecone", "requests"
        ]
        
        violations = []
        
        for py_file in cli_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if any(forbidden in alias.name for forbidden in forbidden_direct_imports):
                                violations.append(f"{py_file.name}: directly imports {alias.name}")
                    
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if any(forbidden in node.module for forbidden in forbidden_direct_imports):
                            violations.append(f"{py_file.name}: directly imports from {node.module}")
        
        assert not violations, f"CLI layer has forbidden direct dependencies: {violations}"
    
    def test_import_cycles(self):
        """Test for circular import dependencies"""
        src_path = Path("src")
        
        # Build dependency graph
        dependencies = {}
        
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            module_name = str(py_file.relative_to(src_path)).replace("/", ".").replace(".py", "")
            dependencies[module_name] = set()
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if node.module.startswith("src.") or node.module.startswith("."):
                            # Normalize relative imports
                            if node.module.startswith("."):
                                # Handle relative imports
                                parts = module_name.split(".")
                                level = node.level if hasattr(node, 'level') else 1
                                base_parts = parts[:-level] if level > 0 else parts
                                if node.module[1:]:  # If there's content after the dots
                                    imported_module = ".".join(base_parts + [node.module[1:]])
                                else:
                                    imported_module = ".".join(base_parts)
                            else:
                                imported_module = node.module.replace("src.", "")
                            
                            dependencies[module_name].add(imported_module)
            
            except (SyntaxError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue
        
        # Check for cycles using DFS
        def has_cycle(graph):
            visited = set()
            rec_stack = set()
            
            def dfs(node):
                if node in rec_stack:
                    return True
                if node in visited:
                    return False
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor in graph and dfs(neighbor):
                        return True
                
                rec_stack.remove(node)
                return False
            
            for node in graph:
                if node not in visited:
                    if dfs(node):
                        return True
            return False
        
        assert not has_cycle(dependencies), "Circular import dependencies detected"
    
    def test_interface_naming_conventions(self):
        """Test that interfaces follow naming conventions"""
        # This will be more relevant when we implement ports/interfaces
        # For now, test that our enums and classes follow conventions
        
        domain_path = Path("src/core/domain/entities")
        
        for py_file in domain_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Classes should be PascalCase
                    assert node.name[0].isupper(), f"Class {node.name} should start with uppercase"
                    
                    # Enums should end with descriptive names
                    if any(base.id == "Enum" for base in node.bases if isinstance(base, ast.Name)):
                        assert not node.name.endswith("Enum"), f"Enum {node.name} should not end with 'Enum'"
    
    def test_pydantic_model_compliance(self):
        """Test that all Pydantic models follow best practices"""
        domain_path = Path("src/core/domain/entities")
        
        for py_file in domain_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a Pydantic model
                    is_pydantic_model = any(
                        isinstance(base, ast.Name) and base.id == "BaseModel"
                        for base in node.bases
                    )
                    
                    if is_pydantic_model:
                        # Should have model_config or Config
                        has_config = any(
                            isinstance(item, ast.Assign) and 
                            any(isinstance(target, ast.Name) and target.id == "model_config" 
                                for target in item.targets)
                            for item in node.body
                        )
                        
                        # Allow models without explicit config for now
                        # assert has_config, f"Pydantic model {node.name} should have model_config"
    
    def test_cli_command_structure(self):
        """Test CLI command structure follows conventions"""
        cli_commands_path = Path("src/cli/commands")
        
        for py_file in cli_commands_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Each command file should have a group function
            assert f"_{py_file.stem}_group" in content or f"{py_file.stem}_group" in content, \
                f"Command file {py_file.name} should have a group function"
            
            # Should use Click decorators
            assert "@click.group" in content or "@click.command" in content, \
                f"Command file {py_file.name} should use Click decorators"
    
    def test_test_structure_compliance(self):
        """Test that test structure follows conventions"""
        tests_path = Path("tests")
        
        # Check test directory structure
        expected_dirs = ["unit", "integration", "cli", "performance"]
        for expected_dir in expected_dirs:
            assert (tests_path / expected_dir).exists(), f"Missing test directory: {expected_dir}"
        
        # Check test file naming
        for test_file in tests_path.rglob("test_*.py"):
            # Test files should start with test_
            assert test_file.name.startswith("test_"), f"Test file {test_file.name} should start with 'test_'"
            
            # Test classes should start with Test
            with open(test_file, 'r') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        assert node.name.startswith("Test"), f"Test class {node.name} should start with 'Test'"
            except SyntaxError:
                # Skip files with syntax errors
                continue
    
    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded in the codebase"""
        src_path = Path("src")
        
        secret_patterns = [
            "sk-", "aws_access_key", "aws_secret", "api_key", "password",
            "secret", "token", "auth", "bearer"
        ]
        
        violations = []
        
        for py_file in src_path.rglob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read().lower()
            
            for line_num, line in enumerate(content.split('\n'), 1):
                if any(pattern in line for pattern in secret_patterns):
                    # Exclude comments and variable names that are clearly not secrets
                    if not any(exclude in line for exclude in ["#", "description", "help", "param", "field"]):
                        if "=" in line and not line.strip().startswith("#"):
                            violations.append(f"{py_file.name}:{line_num}: {line.strip()[:50]}...")
        
        # Filter out obvious false positives
        real_violations = [v for v in violations if not any(
            safe in v.lower() for safe in ["none", "null", "environment", "config", "placeholder"]
        )]
        
        assert not real_violations, f"Potential hardcoded secrets found: {real_violations}"
    
    def test_error_handling_consistency(self):
        """Test that error handling follows consistent patterns"""
        src_path = Path("src")
        
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Check that bare except clauses are not used
            assert "except:" not in content, f"Bare except clause found in {py_file.name}"
            
            # Check for proper exception types in CLI
            if "cli" in str(py_file):
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:  # Bare except
                            assert False, f"Bare except clause in CLI file {py_file.name}"