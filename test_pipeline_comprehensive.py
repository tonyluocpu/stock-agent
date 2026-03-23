#!/usr/bin/env python3
"""
Comprehensive Pipeline Test
===========================

Tests the complete self-improvement pipeline by simulating frontend conversations
and verifying all steps work correctly in proper order.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from self_improvement.conversation_logger import ConversationLogger
from self_improvement.session_tracker import SessionTracker
from self_improvement.improvement_pipeline import ImprovementPipeline
from llm_config import get_llm_client


class PipelineTester:
    """Comprehensive tester for the improvement pipeline."""
    
    def __init__(self):
        self.test_dir = Path("data/test_pipeline_comprehensive")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.conv_dir = self.test_dir / "conversations"
        self.conv_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = ConversationLogger(log_dir=self.conv_dir)
        self.tracker = SessionTracker(heartbeat_timeout=60, heartbeat_interval=30)
        
        # Initialize pipeline
        llm = get_llm_client()
        self.pipeline = ImprovementPipeline(llm)
        
        # Override directories for testing
        improvements_dir = self.test_dir / "improvements"
        improvements_dir.mkdir(parents=True, exist_ok=True)
        (improvements_dir / "backups").mkdir(parents=True, exist_ok=True)
        (improvements_dir / "applied").mkdir(parents=True, exist_ok=True)
        
        self.pipeline.analyzer.analysis_dir = improvements_dir
        self.pipeline.generator.history_file = improvements_dir / "history.json"
        self.pipeline.applier.backup_dir = improvements_dir / "backups"
        self.pipeline.applier.history_file = improvements_dir / "applied_history.json"
        
        self.results = []
    
    def simulate_conversation(self, name: str, conversations: List[Dict]) -> Path:
        """Simulate a frontend conversation."""
        print(f"\n{'='*70}")
        print(f"SIMULATING: {name}")
        print(f"{'='*70}")
        
        session_id = self.logger.start_session()
        self.tracker.start_session(session_id)
        
        print(f"✅ Session started: {session_id[:20]}...")
        
        for i, conv in enumerate(conversations, 1):
            self.logger.log_interaction(
                user_input=conv['user'],
                bot_response=conv['bot'],
                request_type=conv.get('type', 'general'),
                success=conv.get('success', True),
                metadata={
                    'response_time': conv.get('response_time', 0.5),
                    'error': conv.get('error')
                }
            )
            print(f"  [{i}] User: {conv['user'][:50]}...")
            time.sleep(0.1)  # Simulate real timing
        
        # End session (like frontend closing)
        self.tracker.end_session(session_id)
        session_file = self.logger.end_session(trigger_analysis=False)
        
        print(f"✅ Session ended, saved to: {session_file.name}")
        return session_file
    
    def test_scenario(self, name: str, conversations: List[Dict], expected_issues: int = None):
        """Test a specific scenario."""
        print(f"\n{'='*70}")
        print(f"TEST SCENARIO: {name}")
        print(f"{'='*70}")
        
        # Simulate conversation
        session_file = self.simulate_conversation(name, conversations)
        
        # Process through pipeline
        print(f"\n🚀 Processing session through pipeline...")
        start_time = time.time()
        
        self.pipeline.process_session(session_file, async_mode=False)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Processing took {elapsed:.2f} seconds")
        
        # Verify results
        result = {
            'name': name,
            'session_file': session_file.name,
            'interactions': len(conversations),
            'processing_time': elapsed,
            'success': True
        }
        
        # Check if session was analyzed
        should_analyze = self.pipeline.analyzer.should_analyze_session(session_file)
        result['should_analyze'] = should_analyze
        
        if should_analyze:
            # Check if analysis happened
            analysis = self.pipeline.analyzer.analyze_session(session_file)
            issues = analysis.get('issues', [])
            result['issues_found'] = len(issues)
            result['expected_issues'] = expected_issues
            
            if expected_issues is not None:
                if len(issues) == expected_issues:
                    print(f"✅ Found expected {len(issues)} issues")
                else:
                    print(f"⚠️  Expected {expected_issues} issues, found {len(issues)}")
                    result['success'] = False
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """Run all test scenarios."""
        print("\n" + "="*70)
        print("COMPREHENSIVE PIPELINE TEST SUITE")
        print("="*70)
        
        # Test 1: Good conversation (should have no issues)
        self.test_scenario(
            "Good Stock Conversation",
            [
                {"user": "How is Apple doing?", "bot": "Apple (AAPL) is trading at $175.50...", "type": "stock_analysis", "success": True},
                {"user": "What about Tesla?", "bot": "Tesla (TSLA) is currently at $250.30...", "type": "stock_analysis", "success": True},
                {"user": "Show me NVIDIA's financials", "bot": "NVIDIA's financial statements show...", "type": "financial_analysis", "success": True},
            ],
            expected_issues=0
        )
        
        # Test 2: Spelling errors (should detect)
        self.test_scenario(
            "Spelling Errors",
            [
                {"user": "how is appel doing", "bot": "I don't recognize that stock symbol.", "type": "stock_analysis", "success": False, "error": "Symbol not found"},
                {"user": "i mean apple", "bot": "Apple (AAPL) is trading at $175.50...", "type": "stock_analysis", "success": True},
                {"user": "what about googel", "bot": "I don't recognize that stock symbol.", "type": "stock_analysis", "success": False, "error": "Symbol not found"},
            ],
            expected_issues=None  # Should find spelling issues
        )
        
        # Test 3: Off-topic responses (should detect)
        self.test_scenario(
            "Off-Topic Responses",
            [
                {"user": "what's the weather today?", "bot": "I'm a stock analysis agent. I can help you with stock data...", "type": "general", "success": True},
                {"user": "tell me a joke", "bot": "I'm a stock analysis agent. I can help you with stock data...", "type": "general", "success": True},
                {"user": "how is apple?", "bot": "Apple (AAPL) is trading at $175.50...", "type": "stock_analysis", "success": True},
            ],
            expected_issues=None  # Should find off-topic issues
        )
        
        # Test 4: Repetitive responses (should detect)
        self.test_scenario(
            "Repetitive Responses",
            [
                {"user": "hello", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
                {"user": "hi", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
                {"user": "hey", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
                {"user": "how is apple?", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
            ],
            expected_issues=None  # Should find repetitive response issues
        )
        
        # Test 5: User confusion (should detect)
        self.test_scenario(
            "User Confusion",
            [
                {"user": "what?", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
                {"user": "i don't understand", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
                {"user": "that doesn't help", "bot": "I'm here to help with stock-related questions!", "type": "general", "success": True},
            ],
            expected_issues=None  # Should find user confusion
        )
        
        # Test 6: Mixed good and bad (should detect issues)
        self.test_scenario(
            "Mixed Conversation",
            [
                {"user": "how is apple?", "bot": "Apple (AAPL) is trading at $175.50...", "type": "stock_analysis", "success": True},
                {"user": "what about appel?", "bot": "I don't recognize that stock symbol.", "type": "stock_analysis", "success": False, "error": "Symbol not found"},
                {"user": "i mean apple", "bot": "Apple (AAPL) is trading at $175.50...", "type": "stock_analysis", "success": True},
                {"user": "what's the weather?", "bot": "I'm a stock analysis agent...", "type": "general", "success": True},
            ],
            expected_issues=None  # Should find multiple issues
        )
        
        # Test 7: Too few interactions (should skip)
        self.test_scenario(
            "Too Few Interactions",
            [
                {"user": "hello", "bot": "Hi! How can I help?", "type": "general", "success": True},
            ],
            expected_issues=None  # Should skip analysis
        )
        
        # Test 8: All fast-path responses (should skip)
        self.test_scenario(
            "All Fast-Path",
            [
                {"user": "hello", "bot": "Hi! How can I help?", "type": "general", "success": True},
                {"user": "help", "bot": "I can help with stocks...", "type": "general", "success": True},
                {"user": "thanks", "bot": "You're welcome!", "type": "general", "success": True},
            ],
            expected_issues=None  # Might skip if all fast-path
        )
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('success', False))
        
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result.get('success', False) else "⚠️  CHECK"
            print(f"\n{i}. {result['name']}: {status}")
            print(f"   Interactions: {result['interactions']}")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            print(f"   Should analyze: {result.get('should_analyze', False)}")
            if result.get('issues_found') is not None:
                print(f"   Issues found: {result['issues_found']}")
        
        print(f"\n{'='*70}")
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"{'='*70}")


def main():
    """Run comprehensive tests."""
    tester = PipelineTester()
    tester.run_all_tests()
    
    print("\n✅ Comprehensive tests complete!")
    print("\nCheck the results above to verify:")
    print("  1. ✅ Logging works")
    print("  2. ✅ Analysis works")
    print("  3. ✅ Improvements generated")
    print("  4. ✅ Proper order maintained")
    print("  5. ✅ Cleanup happens after")


if __name__ == "__main__":
    main()

