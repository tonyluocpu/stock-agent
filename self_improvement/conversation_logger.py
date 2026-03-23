#!/usr/bin/env python3
"""
Conversation Logger
===================

Records all user-bot interactions for later analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid


class ConversationLogger:
    """
    Logs all conversations to disk for later analysis.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the conversation logger.
        
        Args:
            log_dir: Directory to store conversation logs. Defaults to data/conversations.
        """
        if log_dir is None:
            from config import DATA_DIRECTORY
            self.log_dir = DATA_DIRECTORY / "conversations"
        else:
            self.log_dir = log_dir
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session state
        self.current_session_id = None
        self.session_start_time = None
        self.session_log: List[Dict] = []
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new conversation session.
        
        Args:
            session_id: Optional session ID. If None, generates a new UUID.
            
        Returns:
            The session ID.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.current_session_id = session_id
        self.session_start_time = datetime.now()
        self.session_log = []
        
        return session_id
    
    def log_interaction(self, 
                       user_input: str, 
                       bot_response: str,
                       request_type: str,
                       success: bool,
                       metadata: Optional[Dict] = None) -> None:
        """
        Log a single user-bot interaction.
        
        Args:
            user_input: What the user said
            bot_response: What the bot responded
            request_type: Type of request (stock_data, stock_analysis, etc.)
            success: Whether the request was successful
            metadata: Optional metadata (response_time, error, etc.)
        """
        if not self.current_session_id:
            # Auto-start session if not started
            self.start_session()
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'bot_response': bot_response,
            'request_type': request_type,
            'success': success,
        }
        
        # Add metadata if provided
        if metadata:
            entry['metadata'] = metadata
        
        self.session_log.append(entry)
    
    def end_session(self, trigger_analysis: bool = True) -> Optional[Path]:
        """
        End the current session and save to disk.
        
        Args:
            trigger_analysis: Whether to trigger analysis after saving.
            
        Returns:
            Path to the saved session file, or None if no session was active.
        """
        if not self.current_session_id or not self.session_log:
            return None
        
        # Save session to disk
        timestamp_str = self.session_start_time.strftime('%Y%m%d_%H%M%S')
        session_file = self.log_dir / f"session_{self.current_session_id}_{timestamp_str}.json"
        
        session_data = {
            'session_id': self.current_session_id,
            'start_time': self.session_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_interactions': len(self.session_log),
            'conversations': self.session_log
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Reset session state
        session_id = self.current_session_id
        self.current_session_id = None
        self.session_start_time = None
        self.session_log = []
        
        return session_file
    
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self.current_session_id
    
    def get_session_log(self) -> List[Dict]:
        """Get the current session log."""
        return self.session_log.copy()
    
    def has_active_session(self) -> bool:
        """Check if there's an active session."""
        return self.current_session_id is not None




