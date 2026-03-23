#!/usr/bin/env python3
"""
Session Memory System
======================

In-memory session context for the stock agent.
Tracks conversation history, entities (stocks, analyses), and generates context summaries.

This is a standalone module - integrate into stock_agent_service.py later.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import OrderedDict


class SessionMemory:
    """
    Manages session memory for conversation context.
    
    Features:
    - Full conversation history
    - Entity tracking (stocks, analyses, downloads)
    - Context summarization for LLM prompts
    - Session-scoped (clears when session ends)
    """
    
    def __init__(self, llm_client=None, max_history: int = 50):
        """
        Initialize session memory.
        
        Args:
            llm_client: Optional LLM client for context summarization
            max_history: Maximum conversation turns to keep (default 50)
        """
        self.llm_client = llm_client
        self.max_history = max_history
        
        # Conversation history
        self.history: List[Dict] = []
        
        # Entity registry
        self.entities = {
            'stocks': OrderedDict(),      # {symbol: {name, price, sector, last_updated, analyses}}
            'analyses': [],                # List of {symbol, type, summary, timestamp}
            'downloads': [],               # List of {symbol, period, interval, filepath, timestamp}
        }
        
        # Context summary (LLM-generated)
        self.context_summary: str = ""
        self._turns_since_summary: int = 0
        self._summary_interval: int = 5  # Summarize every 5 turns
        
        # Session metadata
        self.session_start: datetime = datetime.now()
        self.session_id: Optional[str] = None
    
    # ==================== Conversation History ====================
    
    def add_interaction(
        self,
        user_input: str,
        bot_response: str,
        request_type: str = "general",
        success: bool = True,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a conversation turn to history.
        
        Args:
            user_input: User's message
            bot_response: Bot's response
            request_type: Type of request (stock_data, analysis, etc.)
            success: Whether the request was successful
            metadata: Optional additional metadata
        """
        entry = {
            'turn': len(self.history) + 1,
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'bot_response': bot_response,
            'request_type': request_type,
            'success': success,
            'metadata': metadata or {}
        }
        
        self.history.append(entry)
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Track for summarization
        self._turns_since_summary += 1
        
        # Auto-summarize if LLM available and interval reached
        if self.llm_client and self._turns_since_summary >= self._summary_interval:
            self._update_summary()
    
    def get_recent_history(self, n: int = 5) -> List[Dict]:
        """Get the N most recent conversation turns."""
        return self.history[-n:] if self.history else []
    
    # ==================== Entity Tracking ====================
    
    def track_stock(
        self,
        symbol: str,
        name: Optional[str] = None,
        price: Optional[float] = None,
        sector: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> None:
        """
        Track a stock entity that was discussed or analyzed.
        
        Args:
            symbol: Stock ticker symbol
            name: Company name
            price: Current/last price
            sector: Stock sector
            data: Additional data dict
        """
        symbol = symbol.upper()
        
        if symbol not in self.entities['stocks']:
            self.entities['stocks'][symbol] = {
                'name': name,
                'price': price,
                'sector': sector,
                'first_mentioned': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'analyses': [],
                'data': data or {}
            }
        else:
            # Update existing entry
            entry = self.entities['stocks'][symbol]
            if name:
                entry['name'] = name
            if price:
                entry['price'] = price
            if sector:
                entry['sector'] = sector
            if data:
                entry['data'].update(data)
            entry['last_updated'] = datetime.now().isoformat()
    
    def track_analysis(
        self,
        symbol: str,
        analysis_type: str,
        summary: str,
        key_findings: Optional[List[str]] = None
    ) -> None:
        """
        Track an analysis that was performed.
        
        Args:
            symbol: Stock ticker
            analysis_type: Type of analysis (technical, financial, screening)
            summary: Brief summary of findings
            key_findings: List of key points
        """
        symbol = symbol.upper()
        
        analysis_entry = {
            'symbol': symbol,
            'type': analysis_type,
            'summary': summary,
            'key_findings': key_findings or [],
            'timestamp': datetime.now().isoformat()
        }
        
        self.entities['analyses'].append(analysis_entry)
        
        # Also link to the stock entity
        if symbol in self.entities['stocks']:
            self.entities['stocks'][symbol]['analyses'].append({
                'type': analysis_type,
                'summary': summary[:100],  # Brief summary
                'timestamp': datetime.now().isoformat()
            })
    
    def track_download(
        self,
        symbol: str,
        period: str,
        interval: str,
        filepath: Optional[str] = None
    ) -> None:
        """
        Track data that was downloaded.
        
        Args:
            symbol: Stock ticker
            period: Time period (e.g., "2020-2024")
            interval: Data interval (daily, weekly)
            filepath: Path where data was saved
        """
        symbol = symbol.upper()
        
        download_entry = {
            'symbol': symbol,
            'period': period,
            'interval': interval,
            'filepath': filepath,
            'timestamp': datetime.now().isoformat()
        }
        
        self.entities['downloads'].append(download_entry)
    
    def get_stock(self, symbol: str) -> Optional[Dict]:
        """Get tracked data for a stock."""
        return self.entities['stocks'].get(symbol.upper())
    
    def get_mentioned_stocks(self) -> List[str]:
        """Get list of all stocks mentioned in session."""
        return list(self.entities['stocks'].keys())
    
    def get_recent_analyses(self, n: int = 5) -> List[Dict]:
        """Get the N most recent analyses."""
        return self.entities['analyses'][-n:] if self.entities['analyses'] else []
    
    # ==================== Context Generation ====================
    
    def get_context_prompt(self, include_history: bool = True, max_history_turns: int = 3) -> str:
        """
        Generate a context prompt to inject into LLM system messages.
        
        Args:
            include_history: Include recent conversation history
            max_history_turns: Number of recent turns to include
            
        Returns:
            Formatted context string for LLM prompt
        """
        sections = []
        
        # Add context summary if available
        if self.context_summary:
            sections.append(f"CONVERSATION SUMMARY:\n{self.context_summary}")
        
        # Add recent history
        if include_history and self.history:
            recent = self.get_recent_history(max_history_turns)
            if recent:
                history_lines = []
                for entry in recent:
                    # Include full user input (up to 200 chars) and more of bot response (up to 300 chars)
                    user_msg = entry['user_input'][:200] + ("..." if len(entry['user_input']) > 200 else "")
                    bot_msg = entry['bot_response'][:300] + ("..." if len(entry['bot_response']) > 300 else "")
                    history_lines.append(f"User: {user_msg}")
                    history_lines.append(f"You: {bot_msg}")
                sections.append("RECENT CONVERSATION:\n" + "\n".join(history_lines))
        
        # Add tracked stocks
        if self.entities['stocks']:
            stock_lines = []
            for symbol, data in list(self.entities['stocks'].items())[-5:]:  # Last 5 stocks
                line = f"- {symbol}"
                if data.get('name'):
                    line += f" ({data['name']})"
                if data.get('price'):
                    line += f": ${data['price']:.2f}"
                if data.get('analyses'):
                    line += f" [analyzed {len(data['analyses'])}x]"
                stock_lines.append(line)
            sections.append("STOCKS DISCUSSED:\n" + "\n".join(stock_lines))
        
        # Add recent downloads
        if self.entities['downloads']:
            download_lines = []
            for dl in self.entities['downloads'][-3:]:  # Last 3 downloads
                download_lines.append(f"- {dl['symbol']} {dl['interval']} data ({dl['period']})")
            sections.append("DATA DOWNLOADED:\n" + "\n".join(download_lines))
        
        if not sections:
            return ""
        
        return "=== SESSION CONTEXT ===\n" + "\n\n".join(sections) + "\n=== END CONTEXT ===\n"
    
    def _update_summary(self) -> None:
        """Update context summary using LLM."""
        if not self.llm_client or not self.history:
            return
        
        try:
            # Build summary prompt
            recent_history = self.get_recent_history(10)
            history_text = "\n".join([
                f"User: {h['user_input']}\nBot: {h['bot_response'][:200]}..."
                for h in recent_history
            ])
            
            stocks_mentioned = ", ".join(self.get_mentioned_stocks()[-10:])
            
            prompt = f"""Summarize this conversation session in 2-3 sentences.
Focus on: what stocks were discussed, what analyses were done, key findings.

Stocks mentioned: {stocks_mentioned or 'None'}

Recent conversation:
{history_text}

Provide a brief summary (2-3 sentences max):"""
            
            self.context_summary = self.llm_client.call(
                prompt=prompt,
                system_prompt="You are a helpful assistant that creates brief conversation summaries.",
                max_tokens=150,
                temperature=0.3
            ).strip()
            
            self._turns_since_summary = 0
            
        except Exception as e:
            print(f"Warning: Failed to update context summary: {e}")
    
    # ==================== Session Management ====================
    
    def clear(self) -> None:
        """Clear all session memory."""
        self.history = []
        self.entities = {
            'stocks': OrderedDict(),
            'analyses': [],
            'downloads': [],
        }
        self.context_summary = ""
        self._turns_since_summary = 0
        self.session_start = datetime.now()
    
    def set_session_id(self, session_id: str) -> None:
        """Set the session ID."""
        self.session_id = session_id
    
    def get_stats(self) -> Dict:
        """Get session statistics."""
        return {
            'session_id': self.session_id,
            'session_duration_minutes': (datetime.now() - self.session_start).total_seconds() / 60,
            'total_turns': len(self.history),
            'stocks_discussed': len(self.entities['stocks']),
            'analyses_performed': len(self.entities['analyses']),
            'downloads': len(self.entities['downloads']),
            'has_summary': bool(self.context_summary)
        }
    
    def to_dict(self) -> Dict:
        """Export memory state as dictionary."""
        return {
            'session_id': self.session_id,
            'session_start': self.session_start.isoformat(),
            'history': self.history,
            'entities': {
                'stocks': dict(self.entities['stocks']),
                'analyses': self.entities['analyses'],
                'downloads': self.entities['downloads']
            },
            'context_summary': self.context_summary,
            'stats': self.get_stats()
        }


# ==================== Convenience Functions ====================

def create_session_memory(llm_client=None) -> SessionMemory:
    """Create a new session memory instance."""
    return SessionMemory(llm_client=llm_client)


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Demo without LLM
    memory = SessionMemory()
    
    # Simulate a conversation
    memory.add_interaction(
        user_input="Tell me about Apple stock",
        bot_response="Apple (AAPL) is currently trading at $195.50...",
        request_type="stock_analysis",
        success=True
    )
    
    memory.track_stock("AAPL", name="Apple Inc.", price=195.50, sector="Technology")
    memory.track_analysis("AAPL", "technical", "Bullish trend, P/E 28.5", ["Strong momentum", "Above 50-day MA"])
    
    memory.add_interaction(
        user_input="Download weekly data for Microsoft",
        bot_response="Downloaded MSFT weekly data from 2020-2024...",
        request_type="stock_data",
        success=True
    )
    
    memory.track_stock("MSFT", name="Microsoft Corp.", price=420.00, sector="Technology")
    memory.track_download("MSFT", "2020-2024", "weekly", "data/stocks/MSFT_weekly.csv")
    
    # Show context prompt
    print("=" * 60)
    print("GENERATED CONTEXT PROMPT:")
    print("=" * 60)
    print(memory.get_context_prompt())
    
    # Show stats
    print("\nSESSION STATS:")
    print(memory.get_stats())

