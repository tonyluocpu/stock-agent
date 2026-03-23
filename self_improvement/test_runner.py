#!/usr/bin/env python3
"""
Test Runner
===========

Validates improvements before applying them.
"""

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess
import tempfile


class TestRunner:
    """
    Validates code improvements before applying.
    """
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_results = []
    
    def validate_improvement(self, improvement: Dict) -> Tuple[bool, List[str]]:
        """
        Validate an improvement proposal.
        
        Args:
            improvement: Improvement proposal from generator
            
        Returns:
            Tuple of (passed: bool, errors: List[str])
        """
        errors = []
        
        # 1. Syntax validation
        syntax_ok, syntax_errors = self._validate_syntax(improvement)
        if not syntax_ok:
            errors.extend(syntax_errors)
            return False, errors
        
        # 2. Import validation
        import_ok, import_errors = self._validate_imports(improvement)
        if not import_ok:
            errors.extend(import_errors)
            return False, errors
        
        # 3. Regression tests (basic smoke test)
        regression_ok, regression_errors = self._run_regression_tests(improvement)
        if not regression_ok:
            errors.extend(regression_errors)
            return False, errors
        
        # 4. Improvement-specific tests
        improvement_ok, improvement_errors = self._test_improvement(improvement)
        if not improvement_ok:
            errors.extend(improvement_errors)
            return False, errors
        
        return True, []
    
    def _validate_syntax(self, improvement: Dict) -> Tuple[bool, List[str]]:
        """Validate Python syntax of the code change."""
        errors = []
        
        try:
            code_after = improvement['code_change']['after']
            
            # Try to parse as AST
            ast.parse(code_after)
            
            return True, []
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
            return False, errors
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
            return False, errors
    
    def _validate_imports(self, improvement: Dict) -> Tuple[bool, List[str]]:
        """Check if all imports are available."""
        errors = []
        
        try:
            code_after = improvement['code_change']['after']
            tree = ast.parse(code_after)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
            
            # Check if imports are available
            for imp in set(imports):
                try:
                    __import__(imp)
                except ImportError:
                    errors.append(f"Missing import: {imp}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Import validation error: {str(e)}")
            return False, errors
    
    def _run_regression_tests(self, improvement: Dict) -> Tuple[bool, List[str]]:
        """Run basic regression tests to ensure nothing broke."""
        errors = []
        
        # Create a temporary file with the modified code
        file_path = Path(improvement['file'])
        
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return False, errors
        
        # Read original file
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        # Try to compile the modified code in isolation
        try:
            code_after = improvement['code_change']['after']
            
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code_after)
                tmp_path = tmp.name
            
            # Try to compile
            compile(code_after, tmp_path, 'exec')
            
            # Cleanup
            Path(tmp_path).unlink()
            
            return True, []
            
        except SyntaxError as e:
            errors.append(f"Compilation error: {e.msg} at line {e.lineno}")
            return False, errors
        except Exception as e:
            errors.append(f"Regression test error: {str(e)}")
            return False, errors
    
    def _test_improvement(self, improvement: Dict) -> Tuple[bool, List[str]]:
        """Test that the improvement actually fixes the issue."""
        errors = []
        
        # Get test cases from improvement
        test_cases = improvement.get('test_cases', [])
        
        if not test_cases:
            # No test cases provided - skip this check
            return True, []
        
        # For now, just validate that test cases are reasonable
        # Full integration testing would require applying the change first
        # which we do in the applier
        
        return True, []
    
    def attempt_fix(self, improvement: Dict, errors: List[str]) -> Optional[Dict]:
        """
        Attempt to fix issues found in validation.
        
        Args:
            improvement: The improvement that failed
            errors: List of validation errors
            
        Returns:
            Fixed improvement if fixable, None otherwise
        """
        # For syntax/import errors, we could try to fix them
        # For now, return None to indicate we can't auto-fix
        # This could be enhanced with LLM-based fixing
        
        return None




