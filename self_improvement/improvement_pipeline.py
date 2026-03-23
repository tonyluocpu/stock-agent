#!/usr/bin/env python3
"""
Improvement Pipeline
====================

Orchestrates the full self-improvement pipeline:
1. Analyze conversation
2. Generate improvements
3. Test improvements
4. Apply improvements
"""

import threading
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from .conversation_analyzer import ConversationAnalyzer
    from .improvement_generator import ImprovementGenerator
    from .test_runner import TestRunner
    from .improvement_applier import ImprovementApplier
except ImportError:
    # Handle relative imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from self_improvement.conversation_analyzer import ConversationAnalyzer
    from self_improvement.improvement_generator import ImprovementGenerator
    from self_improvement.test_runner import TestRunner
    from self_improvement.improvement_applier import ImprovementApplier


class ImprovementPipeline:
    """
    Orchestrates the self-improvement pipeline.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the improvement pipeline.
        
        Args:
            llm_client: LLM client for analysis and generation
        """
        self.llm_client = llm_client
        self.analyzer = ConversationAnalyzer(llm_client)
        self.generator = ImprovementGenerator(llm_client)
        self.test_runner = TestRunner()
        self.applier = ImprovementApplier()
        
        self.pipeline_active = False
    
    def process_session(self, session_file: Path, async_mode: bool = True):
        """
        Process a session file through the improvement pipeline.
        
        Args:
            session_file: Path to session JSON file
            async_mode: If True, runs in background thread
        """
        if async_mode:
            thread = threading.Thread(
                target=self._process_session_sync,
                args=(session_file,),
                daemon=True
            )
            thread.start()
        else:
            self._process_session_sync(session_file)
    
    def _process_session_sync(self, session_file: Path):
        """Process session synchronously."""
        try:
            self.pipeline_active = True
            print(f"\n🔍 Starting improvement pipeline for {session_file.name}")
            
            # STEP 1: Check if session should be analyzed (must be first)
            print("\n[STEP 1/5] Checking if session should be analyzed...")
            if not self.analyzer.should_analyze_session(session_file):
                print("⏭️  Skipping session - too few interactions")
                return
            print("✅ Session meets analysis criteria")
            
            # STEP 2: Analyze conversation (MUST happen before improvements)
            print("\n[STEP 2/5] Analyzing conversation...")
            analysis = self.analyzer.analyze_session(session_file)
            
            if not analysis.get('issues'):
                print("✅ No issues found in conversation")
                return
            
            issues = analysis['issues']
            print(f"✅ Analysis complete - Found {len(issues)} issues")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. [{issue.get('severity', 'unknown').upper()}] {issue.get('type', 'unknown')}: {issue.get('description', '')[:60]}...")
            
            # Step 3: Generate improvements (ONLY after analysis is complete)
            print("\n[STEP 3/5] Generating improvements...")
            session_id = session_file.stem.split('_')[1] if '_' in session_file.stem else 'unknown'
            improvements = self.generator.generate_improvements(issues, session_id)
            
            if not improvements:
                print("⏭️  No improvements generated (cooldown or limits)")
                return
            
            print(f"✅ Generated {len(improvements)} improvements")
            
            # Step 4: Test and apply improvements (ONLY after generation is complete)
            print("\n[STEP 4/5] Testing and applying improvements...")
            applied_count = 0
            failed_count = 0
            rollback_count = 0
            
            for i, improvement in enumerate(improvements, 1):
                print(f"\n  [{i}/{len(improvements)}] Processing improvement: {improvement.get('id', 'unknown')[:20]}...")
                
                # Validate improvement
                passed, errors = self.test_runner.validate_improvement(improvement)
                
                if not passed:
                    print(f"    ❌ Validation failed: {', '.join(errors)}")
                    
                    # Try to fix
                    fixed = self.test_runner.attempt_fix(improvement, errors)
                    if fixed:
                        print("    🔧 Attempting fix...")
                        improvement = fixed
                        passed, errors = self.test_runner.validate_improvement(improvement)
                    
                    if not passed:
                        print(f"    ❌ Still failing after fix attempt - skipping")
                        failed_count += 1
                        continue
                
                # Apply improvement
                print(f"    ✅ Validation passed, applying...")
                success, error = self.applier.apply_improvement(improvement, self.test_runner)
                
                if success:
                    print(f"    ✅ Successfully applied improvement!")
                    applied_count += 1
                    self.generator.record_improvement(improvement, applied=True)
                else:
                    print(f"    ❌ Failed to apply: {error}")
                    failed_count += 1
                    rollback_count += 1  # Track rollbacks
                    self.generator.record_improvement(improvement, applied=False)
            
            # Step 5: Summary (BEFORE cleanup - cleanup happens in finally)
            print("\n[STEP 5/5] Pipeline summary:")
            print(f"   ✅ Applied: {applied_count}")
            print(f"   ❌ Failed: {failed_count}")
            if rollback_count > 0:
                print(f"   🔄 Rollbacks: {rollback_count}")
            print(f"\n📊 Pipeline complete: {applied_count} applied, {failed_count} failed")
            
        except Exception as e:
            print(f"❌ ERROR in improvement pipeline: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup old logs ONLY after everything is done (including rollbacks)
            # This ensures we don't delete logs if something goes wrong
            try:
                self._cleanup_old_logs()
            except Exception as cleanup_error:
                print(f"⚠️  Error during log cleanup: {cleanup_error}")
            finally:
                self.pipeline_active = False
    
    def _cleanup_old_logs(self):
        """
        Clean up old conversation logs AFTER all processing is complete.
        This runs in the finally block to ensure it happens even if errors occur,
        but only after all improvements and rollbacks are done.
        """
        try:
            from config import DATA_DIRECTORY
            conv_dir = DATA_DIRECTORY / "conversations"
            
            if not conv_dir.exists():
                return
            
            # Keep only the most recent 10 sessions
            # This ensures we don't delete logs if something went wrong
            sessions = sorted(conv_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(sessions) > 10:
                sessions_to_delete = sessions[10:]
                deleted_count = 0
                for session_file in sessions_to_delete:
                    try:
                        session_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not delete {session_file.name}: {e}")
                
                if deleted_count > 0:
                    print(f"\n🧹 Cleanup: Deleted {deleted_count} old conversation logs (kept 10 most recent)")
        except Exception as e:
            print(f"⚠️  Error during log cleanup: {e}")
    
    def is_active(self) -> bool:
        """Check if pipeline is currently processing."""
        return self.pipeline_active

