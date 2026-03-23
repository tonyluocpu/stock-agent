#!/usr/bin/env python3
"""
Session Tracker
===============

Tracks frontend sessions using heartbeat mechanism.
Detects when frontend disconnects.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from pathlib import Path


class SessionTracker:
    """
    Tracks frontend sessions using heartbeat mechanism.
    """
    
    def __init__(self, 
                 heartbeat_timeout: int = 240,
                 heartbeat_interval: int = 120):
        """
        Initialize the session tracker.
        
        Args:
            heartbeat_timeout: Seconds before considering session dead (default: 60)
            heartbeat_interval: How often to check for timeouts (default: 30)
        """
        self.heartbeat_timeout = heartbeat_timeout
        self.heartbeat_interval = heartbeat_interval
        
        # Active sessions: {session_id: last_heartbeat_time}
        self.active_sessions: Dict[str, datetime] = {}
        
        # Callback when session ends
        self.session_end_callback: Optional[Callable[[str], None]] = None
        
        # Background thread for checking timeouts
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_running = False
    
    def register_heartbeat(self, session_id: str) -> None:
        """
        Register a heartbeat from a session.
        
        Args:
            session_id: The session ID sending the heartbeat
        """
        self.active_sessions[session_id] = datetime.now()
    
    def start_session(self, session_id: str) -> None:
        """
        Start tracking a new session.
        
        Args:
            session_id: The session ID to track
        """
        self.register_heartbeat(session_id)
        
        # Start monitor thread if not already running
        if not self._monitor_running:
            self._start_monitor()
    
    def end_session(self, session_id: str) -> None:
        """
        Explicitly end a session.
        
        Args:
            session_id: The session ID to end
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            if self.session_end_callback:
                self.session_end_callback(session_id)
    
    def set_session_end_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback to be called when a session ends.
        
        Args:
            callback: Function that takes session_id as argument
        """
        self.session_end_callback = callback
    
    def _start_monitor(self) -> None:
        """Start the background monitor thread."""
        if self._monitor_running:
            return
        
        self._monitor_running = True
        
        def monitor_loop():
            while self._monitor_running:
                try:
                    self._check_timeouts()
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    print(f"ERROR in session monitor: {e}")
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _check_timeouts(self) -> None:
        """Check for timed-out sessions."""
        now = datetime.now()
        timed_out_sessions = []
        
        for session_id, last_heartbeat in self.active_sessions.items():
            time_since_heartbeat = (now - last_heartbeat).total_seconds()
            if time_since_heartbeat > self.heartbeat_timeout:
                timed_out_sessions.append(session_id)
        
        # End timed-out sessions
        for session_id in timed_out_sessions:
            self.end_session(session_id)
    
    def stop_monitor(self) -> None:
        """Stop the monitor thread."""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def get_active_sessions(self) -> Dict[str, datetime]:
        """Get all active sessions."""
        return self.active_sessions.copy()
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if a session is currently active."""
        return session_id in self.active_sessions

