#!/usr/bin/env python3
"""
Conversation Analyzer
=====================

Uses LLM to analyze conversations and identify issues.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ConversationAnalyzer:
    """
    Analyzes conversations to identify issues and improvement opportunities.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the conversation analyzer.
        
        Args:
            llm_client: LLM client for analysis
        """
        self.llm_client = llm_client
        self.analysis_dir = Path("data/improvements")
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_session(self, session_file: Path) -> Dict:
        """
        Analyze a conversation session and identify issues.
        
        Args:
            session_file: Path to session JSON file
            
        Returns:
            Dict with identified issues and analysis
        """
        # Load session data
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        conversations = session_data['conversations']
        
        if not conversations:
            return {
                'issues': [],
                'overall_score': 100,
                'summary': 'No conversations to analyze'
            }
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(conversations)
        
        # Get LLM analysis
        analysis_text = self.llm_client.call(
            prompt=prompt,
            system_prompt="You are an expert at analyzing conversation quality and identifying issues.",
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse analysis
        analysis = self._parse_analysis(analysis_text, conversations)
        
        # Ensure analysis directory exists
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Save analysis
        analysis_file = self.analysis_dir / f"analysis_{session_data['session_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                'session_id': session_data['session_id'],
                'session_file': str(session_file),
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        return analysis
    
    def _build_analysis_prompt(self, conversations: List[Dict]) -> str:
        """Build the analysis prompt for LLM."""
        formatted_convs = []
        for i, conv in enumerate(conversations, 1):
            response_time = conv.get('metadata', {}).get('response_time', 'unknown')
            success = conv.get('success', True)
            
            formatted_convs.append(f"""
Turn {i}:
User: {conv['user_input']}
Bot: {conv['bot_response']}
Request Type: {conv.get('request_type', 'unknown')}
Success: {success}
Response Time: {response_time}s
""")
        
        prompt = f"""Analyze this conversation session and identify issues:

CONVERSATIONS:
{''.join(formatted_convs)}

Identify issues focusing on:

1. **OFF-TOPIC RESPONSES** (HIGH PRIORITY):
   - Bot responds with something unrelated to user's question
   - Bot gives generic/unhelpful responses when specific answer is expected
   - Bot seems to misunderstand the core intent
   - NOTE: "I don't know" or "I don't have that functionality" are OK if accurate

2. **USER CONFUSION**:
   - User asks follow-up questions indicating misunderstanding
   - User has to clarify or rephrase multiple times
   - User seems frustrated (check if responses reference previous conversation context)
   - NOTE: Check if bot maintains conversation context - if not, flag as issue

3. **ERRORS OR FAILURES**:
   - Technical errors in responses
   - Failed requests that should have succeeded
   - Missing data when data should be available

4. **MISSING FUNCTIONALITY**:
   - User asks for something we can't do (but should be able to)
   - Feature gaps that cause user frustration

5. **SLOW RESPONSES**:
   - Response time >= 30 seconds
   - User had to wait too long
   - NOTE: Some operations (like screening) are expected to be slow - don't flag those

For each issue, provide:
- Issue type (off_topic|user_confusion|error|missing_functionality|slow_response)
- Description
- Example conversation turn where it occurred
- Severity (high|medium|low)
- Suggested improvement type (prompt_improvement|pattern_addition|logic_change)

Return as JSON:
{{
    "issues": [
        {{
            "type": "off_topic|user_confusion|error|missing_functionality|slow_response",
            "description": "Clear description of the issue",
            "example": {{
                "user": "exact user input",
                "bot": "exact bot response",
                "turn_number": 1
            }},
            "severity": "high|medium|low",
            "suggestion": "What type of fix would help (prompt_improvement|pattern_addition|logic_change)",
            "details": "Additional context about why this is an issue"
        }}
    ],
    "overall_score": 0-100,
    "summary": "Overall assessment of conversation quality"
}}"""
        
        return prompt
    
    def _parse_analysis(self, analysis_text: str, conversations: List[Dict]) -> Dict:
        """Parse LLM analysis response."""
        try:
            # Try to extract JSON from response
            analysis_text = analysis_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0]
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0]
            
            # Try to fix truncated JSON (common issue with LLM responses)
            # If JSON is incomplete, try to extract what we can
            if not analysis_text.endswith('}'):
                # Find the last complete JSON object
                last_brace = analysis_text.rfind('}')
                if last_brace > 0:
                    # Try to complete the JSON structure
                    partial = analysis_text[:last_brace + 1]
                    # Check if we have a complete issues array
                    if '"issues"' in partial and ']' in partial:
                        # Try to close any open structures
                        open_braces = partial.count('{') - partial.count('}')
                        if open_braces > 0:
                            partial += '}' * open_braces
                        analysis_text = partial
            
            # Parse JSON
            analysis = json.loads(analysis_text)
            
            # Validate structure
            if 'issues' not in analysis:
                analysis['issues'] = []
            if 'overall_score' not in analysis:
                analysis['overall_score'] = 50
            if 'summary' not in analysis:
                analysis['summary'] = 'Analysis completed'
            
            # Filter issues based on response times
            filtered_issues = []
            for issue in analysis['issues']:
                # Check if slow response issue is valid
                if issue.get('type') == 'slow_response':
                    turn_num = issue.get('example', {}).get('turn_number', 1)
                    if turn_num <= len(conversations):
                        conv = conversations[turn_num - 1]
                        response_time = conv.get('metadata', {}).get('response_time', 0)
                        request_type = conv.get('request_type', '')
                        
                        # Only flag if >= 30s and not expected to be slow
                        if response_time >= 30 and request_type != 'stock_screening':
                            filtered_issues.append(issue)
                else:
                    filtered_issues.append(issue)
            
            analysis['issues'] = filtered_issues
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse analysis JSON: {e}")
            print(f"Response was: {analysis_text[:500]}")
            return {
                'issues': [],
                'overall_score': 50,
                'summary': 'Failed to parse analysis',
                'error': str(e)
            }
    
    def should_analyze_session(self, session_file: Path) -> bool:
        """
        Check if a session should be analyzed.
        
        Args:
            session_file: Path to session file
            
        Returns:
            True if session should be analyzed
        """
        # Only analyze sessions with at least 2 interactions
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        return session_data.get('total_interactions', 0) >= 2

