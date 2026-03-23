#!/usr/bin/env python3
"""
Improvement Generator
=====================

Generates smart (non-hardcoded) code improvements based on conversation analysis.
"""

import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ImprovementGenerator:
    """
    Generates code improvements based on conversation analysis.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the improvement generator.
        
        Args:
            llm_client: LLM client for generating improvements
        """
        self.llm_client = llm_client
        self.codebase_context = self._load_codebase_context()
        self.improvement_history_file = Path("data/improvements/history.json")
        self._load_improvement_history()
    
    def _load_codebase_context(self) -> str:
        """Load relevant codebase context for LLM."""
        context_parts = []
        
        # Load key files
        key_files = [
            'stock_agent_service.py',
            'llm_config.py',
            'api_interface.py'
        ]
        
        for filename in key_files:
            file_path = Path(filename)
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Truncate to first 2000 chars to avoid token limits
                        context_parts.append(f"\n=== {filename} ===\n{content[:2000]}")
                except:
                    pass
        
        return "\n".join(context_parts)
    
    def _load_improvement_history(self):
        """Load improvement history to check cooldowns."""
        if self.improvement_history_file.exists():
            try:
                with open(self.improvement_history_file, 'r') as f:
                    self.improvement_history = json.load(f)
            except:
                self.improvement_history = {'improvements': []}
        else:
            self.improvement_history = {'improvements': []}
    
    def _save_improvement_history(self):
        """Save improvement history."""
        self.improvement_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.improvement_history_file, 'w') as f:
            json.dump(self.improvement_history, f, indent=2)
    
    def generate_improvements(self, issues: List[Dict], session_id: str) -> List[Dict]:
        """
        Generate code improvements for identified issues.
        
        Args:
            issues: List of issues from conversation analyzer
            session_id: Session ID for tracking
            
        Returns:
            List of improvement proposals
        """
        improvements = []
        
        # Filter issues by severity and check cooldowns
        high_priority_issues = [i for i in issues if i.get('severity') == 'high']
        medium_priority_issues = [i for i in issues if i.get('severity') == 'medium']
        
        # Limit: Max 3 improvements per session
        # Priority: High severity first, then medium
        issues_to_process = (high_priority_issues + medium_priority_issues)[:3]
        
        logic_changes = 0
        max_logic_changes = 1  # Max 1 logic change per session
        
        for issue in issues_to_process:
            # Check cooldown (24 hours for same issue type)
            if self._is_in_cooldown(issue):
                continue
            
            # Check logic change limit
            suggestion = issue.get('suggestion', '')
            if 'logic_change' in suggestion.lower() and logic_changes >= max_logic_changes:
                continue
            
            improvement = self._generate_improvement(issue, session_id)
            if improvement:
                improvements.append(improvement)
                if 'logic_change' in suggestion.lower():
                    logic_changes += 1
        
        return improvements
    
    def _is_in_cooldown(self, issue: Dict) -> bool:
        """Check if issue type is in cooldown period (24 hours)."""
        issue_type = issue.get('type', '')
        issue_desc = issue.get('description', '')[:100]  # First 100 chars as identifier
        
        # Check last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for improvement in self.improvement_history.get('improvements', []):
            if improvement.get('issue_type') == issue_type:
                improvement_time = datetime.fromisoformat(improvement.get('timestamp', '2000-01-01'))
                if improvement_time > cutoff_time:
                    return True
        
        return False
    
    def _generate_improvement(self, issue: Dict, session_id: str) -> Optional[Dict]:
        """Generate a specific improvement for an issue."""
        prompt = f"""Based on this conversation issue, generate a SMART code improvement:

ISSUE:
Type: {issue.get('type')}
Description: {issue.get('description')}
Example:
User: {issue.get('example', {}).get('user', '')}
Bot: {issue.get('example', {}).get('bot', '')}
Suggestion: {issue.get('suggestion')}
Details: {issue.get('details', '')}

CODEBASE CONTEXT:
{self.codebase_context}

CRITICAL REQUIREMENTS:
1. Generate PATTERN-BASED fixes, NOT hardcoded responses
2. For spelling errors (missing letters, wrong spelling, capitalization):
   - Use fuzzy matching or LLM fallback
   - NEVER hardcode specific misspellings
   - Example: Use difflib.get_close_matches() or call LLM if needed
3. For off-topic responses:
   - Improve prompts or add better intent detection
   - Add pattern matching for common variations
4. For user confusion:
   - Improve context handling or add clarification logic
5. Make changes that apply to similar cases, not just the specific example

Return as JSON:
{{
    "file": "path/to/file.py",
    "function": "function_name",
    "change_type": "prompt_improvement|pattern_addition|logic_change",
    "description": "What this improvement does",
    "code_change": {{
        "before": "exact code before (with context lines)",
        "after": "exact code after (with context lines)",
        "explanation": "Why this change fixes the issue"
    }},
    "test_cases": ["example input that should work better"],
    "line_numbers": {{
        "start": 123,
        "end": 145
    }}
}}"""
        
        try:
            response = self.llm_client.call(
                prompt=prompt,
                system_prompt="You are an expert Python developer. Generate smart, pattern-based code improvements.",
                temperature=0.2,
                max_tokens=3000
            )
            
            improvement = self._parse_improvement(response, issue, session_id)
            return improvement
            
        except Exception as e:
            print(f"ERROR generating improvement: {e}")
            return None
    
    def _parse_improvement(self, response_text: str, issue: Dict, session_id: str) -> Optional[Dict]:
        """Parse LLM improvement response."""
        try:
            # Extract JSON
            response_text = response_text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            # Try to fix truncated JSON (common issue with LLM responses)
            if not response_text.endswith('}'):
                # Find the last complete JSON object
                last_brace = response_text.rfind('}')
                if last_brace > 0:
                    partial = response_text[:last_brace + 1]
                    # Try to close any open structures
                    open_braces = partial.count('{') - partial.count('}')
                    open_brackets = partial.count('[') - partial.count(']')
                    if open_braces > 0:
                        partial += '}' * open_braces
                    if open_brackets > 0:
                        partial += ']' * open_brackets
                    response_text = partial
            
            improvement = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['file', 'function', 'change_type', 'code_change']
            if not all(field in improvement for field in required_fields):
                print(f"ERROR: Missing required fields in improvement")
                return None
            
            # Add metadata
            improvement['issue'] = issue
            improvement['session_id'] = session_id
            improvement['timestamp'] = datetime.now().isoformat()
            improvement['id'] = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
            
            return improvement
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse improvement JSON: {e}")
            print(f"Response length: {len(response_text)}")
            print(f"Response preview: {response_text[:200]}...")
            # Try to extract partial JSON if possible
            try:
                # Look for any valid JSON object
                start_idx = response_text.find('{')
                if start_idx >= 0:
                    # Try to find a complete object
                    brace_count = 0
                    end_idx = start_idx
                    for i in range(start_idx, len(response_text)):
                        if response_text[i] == '{':
                            brace_count += 1
                        elif response_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx > start_idx:
                        partial_json = response_text[start_idx:end_idx]
                        improvement = json.loads(partial_json)
                        # Add metadata even if incomplete
                        improvement['issue'] = issue
                        improvement['session_id'] = session_id
                        improvement['timestamp'] = datetime.now().isoformat()
                        improvement['id'] = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
                        print("⚠️  Using partial JSON (may be incomplete)")
                        return improvement
            except:
                pass
            return None
    
    def record_improvement(self, improvement: Dict, applied: bool):
        """Record an improvement in history."""
        self.improvement_history['improvements'].append({
            'id': improvement.get('id'),
            'issue_type': improvement.get('issue', {}).get('type'),
            'change_type': improvement.get('change_type'),
            'timestamp': improvement.get('timestamp'),
            'applied': applied
        })
        self._save_improvement_history()

