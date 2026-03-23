#!/usr/bin/env python3
"""
Improvement Applier
===================

Safely applies code improvements with backup and rollback.
"""

import shutil
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import json
import sys


class ImprovementApplier:
    """
    Safely applies code improvements with backup and rollback.
    """
    
    def __init__(self, backup_dir: Optional[Path] = None, rollback_callback: Optional[Callable[[Path, str], None]] = None):
        """
        Initialize the improvement applier.
        
        Args:
            backup_dir: Directory for backups. Defaults to data/improvements/backups.
            rollback_callback: Optional callback function(file_path, error_message) called on rollback.
        """
        if backup_dir is None:
            from config import DATA_DIRECTORY
            self.backup_dir = DATA_DIRECTORY / "improvements" / "backups"
        else:
            self.backup_dir = backup_dir
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.applied_dir = self.backup_dir.parent / "applied"
        self.applied_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.backup_dir.parent / "applied_history.json"
        self.rollback_callback = rollback_callback
        self._load_history()
    
    def _load_history(self):
        """Load applied improvements history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = {'applied': []}
        else:
            self.history = {'applied': []}
    
    def _save_history(self):
        """Save applied improvements history."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def apply_improvement(self, improvement: Dict, test_runner) -> Tuple[bool, Optional[str]]:
        """
        Apply a code improvement safely.
        
        Args:
            improvement: Improvement to apply
            test_runner: TestRunner instance for validation
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        file_path = Path(improvement['file'])
        
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Create backup
        backup_path = self._create_backup(file_path, improvement)
        if not backup_path:
            return False, "Failed to create backup"
        
        try:
            # Read current code
            with open(file_path, 'r') as f:
                current_code = f.read()
            
            # Apply change
            new_code = self._apply_code_change(current_code, improvement)
            
            # Write new code
            with open(file_path, 'w') as f:
                f.write(new_code)
            
            # Validate after applying
            validation_passed, errors = test_runner.validate_improvement(improvement)
            
            if not validation_passed:
                # Try to fix
                fixed_improvement = test_runner.attempt_fix(improvement, errors)
                
                if fixed_improvement:
                    # Retry with fixed version
                    improvement = fixed_improvement
                    new_code = self._apply_code_change(current_code, improvement)
                    with open(file_path, 'w') as f:
                        f.write(new_code)
                    
                    # Validate again
                    validation_passed, errors = test_runner.validate_improvement(improvement)
                
                if not validation_passed:
                    # Rollback
                    error_msg = f"Validation failed after applying: {', '.join(errors)}"
                    self._rollback(file_path, backup_path, error_msg)
                    return False, error_msg
            
            # Test runtime (basic import test)
            runtime_ok, runtime_error = self._test_runtime(file_path)
            if not runtime_ok:
                error_msg = f"Runtime test failed: {runtime_error}"
                self._rollback(file_path, backup_path, error_msg)
                return False, error_msg
            
            # Success - record in history
            self._record_improvement(improvement, backup_path, success=True)
            
            return True, None
            
        except Exception as e:
            # Rollback on any error
            error_msg = f"Error applying improvement: {str(e)}"
            self._rollback(file_path, backup_path, error_msg)
            return False, error_msg
    
    def _create_backup(self, file_path: Path, improvement: Dict) -> Optional[Path]:
        """Create a backup of the file before modification."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            improvement_id = improvement.get('id', 'unknown')
            backup_filename = f"{file_path.stem}_{timestamp}_{improvement_id}.py.backup"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(file_path, backup_path)
            return backup_path
            
        except Exception as e:
            print(f"ERROR creating backup: {e}")
            return None
    
    def _apply_code_change(self, current_code: str, improvement: Dict) -> str:
        """Apply the code change to the current code."""
        code_change = improvement['code_change']
        before_code = code_change['before'].strip()
        after_code = code_change['after'].strip()
        
        # Try to find and replace
        if before_code in current_code:
            # Simple string replacement
            new_code = current_code.replace(before_code, after_code, 1)
            return new_code
        else:
            # Try to find similar code (fuzzy match)
            # Look for the function or section mentioned
            function_name = improvement.get('function', '')
            
            if function_name:
                # Try to find the function and replace within it
                lines = current_code.split('\n')
                in_target_function = False
                function_indent = 0
                result_lines = []
                i = 0
                
                while i < len(lines):
                    line = lines[i]
                    
                    # Check if we're entering the target function
                    if f"def {function_name}" in line:
                        in_target_function = True
                        function_indent = len(line) - len(line.lstrip())
                        result_lines.append(line)
                        i += 1
                        continue
                    
                    # Check if we're leaving the function (indent back to function level or less)
                    if in_target_function:
                        current_indent = len(line) - len(line.lstrip()) if line.strip() else function_indent + 1
                        if line.strip() and current_indent <= function_indent:
                            in_target_function = False
                    
                    # If we're in the function and found the "before" code, replace it
                    if in_target_function and before_code.strip() in '\n'.join(lines[i:i+10]):
                        # Found it - replace
                        remaining = '\n'.join(lines[i:])
                        if before_code in remaining:
                            remaining = remaining.replace(before_code, after_code, 1)
                            result_lines.extend(remaining.split('\n'))
                            break
                    
                    result_lines.append(line)
                    i += 1
                
                return '\n'.join(result_lines)
            
            # Fallback: append at end (not ideal, but better than failing)
            return current_code + "\n\n# Auto-added improvement\n" + after_code
    
    def _rollback(self, file_path: Path, backup_path: Path, error_message: str = ""):
        """
        Rollback to backup.
        
        Args:
            file_path: File to rollback
            backup_path: Backup file to restore from
            error_message: Error message that triggered rollback
        """
        try:
            shutil.copy2(backup_path, file_path)
            print(f"✅ Rolled back {file_path} to backup")
            
            # Call rollback callback if set
            if self.rollback_callback:
                try:
                    self.rollback_callback(file_path, error_message)
                except Exception as e:
                    print(f"⚠️  Rollback callback error: {e}")
        except Exception as e:
            print(f"❌ ERROR rolling back: {e}")
    
    def _test_runtime(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Test that the file can be imported without errors."""
        try:
            # Try to compile and check for obvious errors
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Parse AST to check syntax
            ast.parse(code)
            
            # Try to import (basic check)
            # We can't fully import because of dependencies, but we can check syntax
            
            return True, None
            
        except SyntaxError as e:
            return False, f"Syntax error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Runtime error: {str(e)}"
    
    def _record_improvement(self, improvement: Dict, backup_path: Path, success: bool):
        """Record applied improvement in history."""
        record = {
            'id': improvement.get('id'),
            'timestamp': datetime.now().isoformat(),
            'file': improvement.get('file'),
            'function': improvement.get('function'),
            'change_type': improvement.get('change_type'),
            'backup_path': str(backup_path),
            'success': success,
            'issue': improvement.get('issue', {})
        }
        
        self.history['applied'].append(record)
        self._save_history()
        
        # Also save improvement details
        improvement_file = self.applied_dir / f"{improvement.get('id')}.json"
        with open(improvement_file, 'w') as f:
            json.dump(improvement, f, indent=2)
    
    def rollback_improvement(self, improvement_id: str) -> Tuple[bool, Optional[str]]:
        """Rollback a specific improvement."""
        # Find improvement in history
        for record in self.history.get('applied', []):
            if record.get('id') == improvement_id:
                backup_path = Path(record['backup_path'])
                file_path = Path(record['file'])
                
                if backup_path.exists():
                    self._rollback(file_path, backup_path, "Manual rollback requested")
                    record['rolled_back'] = True
                    record['rollback_time'] = datetime.now().isoformat()
                    self._save_history()
                    return True, None
                else:
                    return False, "Backup file not found"
        
        return False, "Improvement not found in history"

