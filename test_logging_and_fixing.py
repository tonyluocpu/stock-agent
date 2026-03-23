#!/usr/bin/env python3
"""
Test Logging and Fixing Functionality
======================================

Comprehensive test of:
1. Conversation logging
2. Improvement generation and application
3. Rollback callbacks when fixes fail
"""

import json
import time
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from self_improvement.conversation_logger import ConversationLogger
from self_improvement.session_tracker import SessionTracker
from self_improvement.conversation_analyzer import ConversationAnalyzer
from self_improvement.improvement_generator import ImprovementGenerator
from self_improvement.test_runner import TestRunner
from self_improvement.improvement_applier import ImprovementApplier
from self_improvement.improvement_pipeline import ImprovementPipeline
from llm_config import get_llm_client


# Test directories
TEST_DIR = Path("data/test_logging_fixing")
TEST_CONV_DIR = TEST_DIR / "conversations"
TEST_IMPROV_DIR = TEST_DIR / "improvements"
TEST_BACKUP_DIR = TEST_IMPROV_DIR / "backups"

# Clean up old test data
if TEST_DIR.exists():
    shutil.rmtree(TEST_DIR)
TEST_CONV_DIR.mkdir(parents=True, exist_ok=True)
TEST_IMPROV_DIR.mkdir(parents=True, exist_ok=True)
TEST_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def call(self, prompt: str, system_prompt: str = None, temperature: float = 0.1, max_tokens: int = 1000):
        """Simulate LLM responses."""
        import uuid
        
        if "Analyze this conversation session" in prompt:
            # Return analysis with issues
            return json.dumps({
                "issues": [
                    {
                        "type": "spelling_error",
                        "description": "User misspelled 'apple' as 'appel'",
                        "example_turn": 1,
                        "severity": "high",
                        "suggestion": "Add fuzzy matching for stock symbols"
                    }
                ],
                "overall_score": 70,
                "summary": "Found spelling error issue"
            })
        
        elif "generate a SMART code improvement" in prompt:
            # Return a test improvement
            return json.dumps({
                "id": str(uuid.uuid4()),
                "session_id": "test_session",
                "issue_type": "spelling_error",
                "description": "Add fuzzy matching test",
                "file": "test_target_file.py",
                "function": "test_function",
                "change_type": "modify_logic",
                "code_change": {
                    "before": "if valid_symbols:",
                    "after": "# Fuzzy matching added\nif valid_symbols:"
                },
                "test_cases": ["how is appel doing"]
            })
        
        return "Mock response"


def test_1_conversation_logging():
    """Test 1: Conversation logging functionality."""
    print("\n" + "="*70)
    print("TEST 1: Conversation Logging")
    print("="*70)
    
    logger = ConversationLogger(log_dir=TEST_CONV_DIR)
    
    # Start session
    session_id = logger.start_session()
    assert session_id is not None, "Session ID should be generated"
    print(f"✅ Session started: {session_id}")
    
    # Log multiple interactions
    interactions = [
        ("how is appel doing", "Symbol not found", "stock_analysis", False),
        ("i mean apple", "Apple (AAPL) is trading...", "stock_analysis", True),
        ("what about tesla", "Tesla (TSLA) is...", "stock_analysis", True),
    ]
    
    for user_input, bot_response, req_type, success in interactions:
        logger.log_interaction(
            user_input=user_input,
            bot_response=bot_response,
            request_type=req_type,
            success=success,
            metadata={"response_time": 0.5}
        )
        print(f"  ✅ Logged: {user_input[:40]}...")
    
    # End session
    session_file = logger.end_session(trigger_analysis=False)
    assert session_file is not None, "Session file should be created"
    assert session_file.exists(), "Session file should exist"
    
    # Verify session file content
    with open(session_file, 'r') as f:
        data = json.load(f)
        assert data['session_id'] == session_id, "Session ID should match"
        assert len(data['conversations']) == len(interactions), "All interactions should be logged"
        assert data['total_interactions'] == len(interactions), "Total interactions should match"
    
    print(f"✅ Session saved to: {session_file.name}")
    print(f"✅ Total interactions logged: {len(interactions)}")
    
    return session_file


def test_2_rollback_functionality():
    """Test 2: Rollback functionality when improvements fail."""
    print("\n" + "="*70)
    print("TEST 2: Rollback Functionality")
    print("="*70)
    
    # Create a test file to modify
    test_file = TEST_DIR / "test_target_file.py"
    original_content = """def test_function():
    if valid_symbols:
        return True
    return False
"""
    
    # Write original file
    test_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_file, 'w') as f:
        f.write(original_content)
    
    print(f"✅ Created test file: {test_file.name}")
    
    # Create applier
    applier = ImprovementApplier(backup_dir=TEST_BACKUP_DIR)
    
    # Create a bad improvement (will cause syntax error)
    bad_improvement = {
        "id": "test_bad_improvement",
        "file": str(test_file),
        "function": "test_function",
        "change_type": "modify_logic",
        "code_change": {
            "before": "if valid_symbols:",
            "after": "if valid_symbols:\n    # Syntax error here\n    return  # Missing value"
        }
    }
    
    # Create test runner
    test_runner = TestRunner()
    
    # Try to apply (should fail and rollback)
    print("  Attempting to apply bad improvement...")
    success, error = applier.apply_improvement(bad_improvement, test_runner)
    
    assert not success, "Bad improvement should fail"
    assert error is not None, "Error message should be provided"
    print(f"  ✅ Improvement correctly rejected: {error}")
    
    # Verify file was rolled back
    with open(test_file, 'r') as f:
        rolled_back_content = f.read()
    
    assert rolled_back_content == original_content, "File should be rolled back to original"
    print(f"  ✅ File successfully rolled back to original content")
    
    # Verify backup exists
    backups = list(TEST_BACKUP_DIR.glob("*.backup"))
    assert len(backups) > 0, "Backup should be created"
    print(f"  ✅ Backup created: {backups[0].name}")
    
    # Test manual rollback
    print("\n  Testing manual rollback...")
    rollback_success, rollback_error = applier.rollback_improvement("test_bad_improvement")
    if rollback_success:
        print(f"  ✅ Manual rollback successful")
    else:
        print(f"  ⚠️  Manual rollback: {rollback_error}")
    
    return True


def test_3_improvement_pipeline():
    """Test 3: Full improvement pipeline with rollback."""
    print("\n" + "="*70)
    print("TEST 3: Full Improvement Pipeline")
    print("="*70)
    
    # Create mock session
    logger = ConversationLogger(log_dir=TEST_CONV_DIR)
    session_id = logger.start_session()
    
    logger.log_interaction(
        "how is appel doing",
        "Symbol not found",
        "stock_analysis",
        False,
        {"error": "Symbol not found"}
    )
    
    session_file = logger.end_session(trigger_analysis=False)
    print(f"✅ Created test session: {session_file.name}")
    
    # Initialize pipeline with mock LLM
    mock_llm = MockLLMClient()
    pipeline = ImprovementPipeline(mock_llm)
    
    # Override directories for testing
    pipeline.analyzer.analysis_dir = TEST_IMPROV_DIR
    pipeline.generator.history_file = TEST_IMPROV_DIR / "history.json"
    pipeline.applier.backup_dir = TEST_BACKUP_DIR
    pipeline.applier.history_file = TEST_IMPROV_DIR / "applied_history.json"
    
    # Process session (synchronously for testing)
    print("  Processing session through pipeline...")
    pipeline.process_session(session_file, async_mode=False)
    
    # Check if improvements were attempted
    history_file = TEST_IMPROV_DIR / "applied_history.json"
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
            print(f"  ✅ Improvement history created: {len(history.get('applied', []))} records")
    
    print("  ✅ Pipeline completed")
    
    return True


def test_4_callback_verification():
    """Test 4: Verify callbacks are called on rollback."""
    print("\n" + "="*70)
    print("TEST 4: Rollback Callback Verification")
    print("="*70)
    
    callback_called = {"value": False}
    rollback_error = {"value": None}
    
    def rollback_callback(file_path, error):
        """Callback to verify rollback."""
        callback_called["value"] = True
        rollback_error["value"] = error
        print(f"  🔔 Callback triggered: {file_path} - {error}")
    
    # Create test file
    test_file = TEST_DIR / "test_callback_file.py"
    original_content = "def test(): pass\n"
    
    with open(test_file, 'w') as f:
        f.write(original_content)
    
    # Create applier with callback
    def callback_func(file_path, error_msg):
        callback_called["value"] = True
        rollback_error["value"] = error_msg
    
    applier = ImprovementApplier(backup_dir=TEST_BACKUP_DIR, rollback_callback=callback_func)
    
    # Create bad improvement that will cause syntax error
    # Using invalid syntax: incomplete if statement
    bad_improvement = {
        "id": "test_callback_improvement",
        "file": str(test_file),
        "function": "test",
        "change_type": "modify_logic",
        "code_change": {
            "before": "def test(): pass",
            "after": "def test():\n    if True  # Missing colon - syntax error"
        }
    }
    
    test_runner = TestRunner()
    
    # Apply (should fail and rollback)
    success, error = applier.apply_improvement(bad_improvement, test_runner)
    
    assert not success, "Should fail"
    print(f"  ✅ Rollback occurred: {error}")
    
    # Verify callback was called
    assert callback_called["value"], "Rollback callback should have been called"
    assert rollback_error["value"] is not None, "Rollback error should be set"
    print(f"  ✅ Callback was triggered with error: {rollback_error['value'][:50]}...")
    
    # Verify file was restored
    with open(test_file, 'r') as f:
        content = f.read()
    assert content == original_content, "File should be restored"
    print(f"  ✅ File restored to original")
    
    return True


def test_5_error_handling():
    """Test 5: Error handling in all components."""
    print("\n" + "="*70)
    print("TEST 5: Error Handling")
    print("="*70)
    
    # Test logger with invalid data
    logger = ConversationLogger(log_dir=TEST_CONV_DIR)
    session_id = logger.start_session()
    
    try:
        logger.log_interaction("", "", "", True, {})
        print("  ✅ Logger handles empty strings")
    except Exception as e:
        print(f"  ⚠️  Logger error: {e}")
    
    # Test applier with non-existent file
    applier = ImprovementApplier(backup_dir=TEST_BACKUP_DIR)
    bad_improvement = {
        "id": "test_nonexistent",
        "file": "nonexistent_file.py",
        "function": "test",
        "change_type": "modify_logic",
        "code_change": {"before": "x", "after": "y"}
    }
    
    test_runner = TestRunner()
    success, error = applier.apply_improvement(bad_improvement, test_runner)
    assert not success, "Should fail for non-existent file"
    assert "not found" in error.lower(), "Error should mention file not found"
    print(f"  ✅ Applier correctly handles non-existent file: {error}")
    
    # Test analyzer with empty session
    mock_llm = MockLLMClient()
    analyzer = ConversationAnalyzer(mock_llm)
    analyzer.analysis_dir = TEST_IMPROV_DIR
    
    empty_session = TEST_DIR / "empty_session.json"
    with open(empty_session, 'w') as f:
        json.dump({"conversations": []}, f)
    
    should_analyze = analyzer.should_analyze_session(empty_session)
    assert not should_analyze, "Empty session should not be analyzed"
    print(f"  ✅ Analyzer correctly skips empty sessions")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Logging and Fixing Functionality")
    print("="*70)
    
    results = {}
    
    try:
        results['test_1'] = test_1_conversation_logging()
        print("✅ TEST 1 PASSED")
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['test_1'] = False
    
    try:
        results['test_2'] = test_2_rollback_functionality()
        print("✅ TEST 2 PASSED")
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['test_2'] = False
    
    try:
        results['test_3'] = test_3_improvement_pipeline()
        print("✅ TEST 3 PASSED")
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['test_3'] = False
    
    try:
        results['test_4'] = test_4_callback_verification()
        print("✅ TEST 4 PASSED")
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['test_4'] = False
    
    try:
        results['test_5'] = test_5_error_handling()
        print("✅ TEST 5 PASSED")
    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['test_5'] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

