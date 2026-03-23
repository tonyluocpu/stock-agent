#!/usr/bin/env python3
"""
API Interface for Stock Agent
==============================

Simple REST API interface for frontend integration.
Can be extended to Flask/FastAPI later.

Usage:
    python api_interface.py
    
Then send POST requests to:
    http://localhost:5001/api/chat
    Body: {"message": "Apple weekly data 2020-2024"}
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import time
import atexit

try:
    from stock_agent_service import StockAgentService
    from llm_config import load_config, get_llm_client
    from self_improvement import ConversationLogger, SessionTracker
    from self_improvement.improvement_pipeline import ImprovementPipeline
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize service
service = None

# Initialize self-improvement components
conversation_logger = ConversationLogger()
session_tracker = SessionTracker()

# Initialize improvement pipeline (will be set up after service init)
improvement_pipeline = None

# Set up session end callback
def on_session_end(session_id: str):
    """Called when a session ends."""
    print(f"\n📊 Session {session_id} ended, saving conversation...")
    session_file = conversation_logger.end_session(trigger_analysis=False)
    if session_file:
        print(f"✅ Conversation saved to {session_file}")
        # Trigger improvement pipeline IMMEDIATELY (synchronous)
        if improvement_pipeline:
            print(f"🚀 Processing session immediately: {session_file.name}")
            improvement_pipeline.process_session(session_file, async_mode=False)
            print(f"✅ Session processing complete\n")
        else:
            print("⚠️  Improvement pipeline not initialized yet")

session_tracker.set_session_end_callback(on_session_end)

# Cleanup on shutdown
def cleanup():
    """Save any active sessions before shutdown."""
    print("\n🛑 Shutting down, saving active sessions...")
    for session_id in list(session_tracker.get_active_sessions().keys()):
        conversation_logger.end_session(trigger_analysis=False)
    session_tracker.stop_monitor()

atexit.register(cleanup)

def init_service():
    """Initialize the service."""
    global service, improvement_pipeline
    try:
        service = StockAgentService()
        print("✅ Stock Agent Service initialized!")
        config = load_config()
        print(f"   LLM Provider: {config.get('llm_provider', 'unknown')}")
        
        # Initialize improvement pipeline
        try:
            llm_client = get_llm_client()
            improvement_pipeline = ImprovementPipeline(llm_client)
            
            # Set up rollback callback for logging
            def rollback_callback(file_path, error_message):
                """Callback when an improvement is rolled back."""
                print(f"⚠️  Improvement rolled back: {file_path}")
                print(f"   Reason: {error_message}")
            
            improvement_pipeline.applier.rollback_callback = rollback_callback
            print("✅ Self-improvement pipeline initialized with rollback callbacks!")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize improvement pipeline: {e}")
            improvement_pipeline = None
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize service: {e}")
        return False


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Stock Agent API"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for processing user requests.
    
    Request body:
        {
            "message": "User input text",
            "context": [optional conversation context],
            "session_id": [optional session ID]
        }
    
    Response:
        {
            "type": "stock_data|stock_analysis|financial_analysis|general",
            "response": "Response text",
            "success": true/false,
            "data": {...}  // Optional structured data
            "session_id": "session UUID"  // Session ID for heartbeat
        }
    """
    if not service:
        return jsonify({
            "error": "Service not initialized",
            "success": False
        }), 500
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing 'message' field",
                "success": False
            }), 400
        
        user_input = data['message']
        context = data.get('context', None)
        session_id = data.get('session_id', None)
        
        # Handle session tracking
        if session_id:
            # Existing session - register heartbeat
            session_tracker.register_heartbeat(session_id)
            if not conversation_logger.has_active_session():
                conversation_logger.start_session(session_id)
            elif conversation_logger.get_current_session_id() != session_id:
                # Session changed, end old one and start new
                conversation_logger.end_session(trigger_analysis=False)
                conversation_logger.start_session(session_id)
        else:
            # New session - start tracking
            session_id = conversation_logger.start_session()
            session_tracker.start_session(session_id)
        
        # Track response time
        start_time = time.time()
        
        # Process request
        result = service.process_request(user_input, context)
        
        response_time = time.time() - start_time
        
        # Log interaction
        conversation_logger.log_interaction(
            user_input=user_input,
            bot_response=result.get('response', ''),
            request_type=result.get('type', 'general'),
            success=result.get('success', False),
            metadata={
                'response_time': response_time,
                'error': result.get('error') if not result.get('success') else None
            }
        )
        
        # Add to context
        if result.get('success'):
            service.add_to_context(
                user_input,
                result.get('response', ''),
                result.get('type', 'general')
            )
        
        # Add session_id to response
        result['session_id'] = session_id
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/context', methods=['GET'])
def get_context():
    """Get current conversation context."""
    if not service:
        return jsonify({"error": "Service not initialized"}), 500
    
    return jsonify({
        "context": service.get_context(),
        "success": True
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration (without sensitive data)."""
    config = load_config()
    safe_config = {
        "llm_provider": config.get("llm_provider"),
        "free_backend": config.get("free_backend") if config.get("llm_provider") == "free" else None,
        "openrouter_model": config.get("openrouter_model") if config.get("llm_provider") == "openrouter" else None
    }
    return jsonify(safe_config)


@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Start a new session."""
    session_id = conversation_logger.start_session()
    session_tracker.start_session(session_id)
    return jsonify({
        "session_id": session_id,
        "success": True
    })


@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    """Heartbeat endpoint to keep session alive."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({
            "error": "Missing 'session_id' field",
            "success": False
        }), 400
    
    session_tracker.register_heartbeat(session_id)
    
    return jsonify({
        "success": True,
        "session_active": session_tracker.is_session_active(session_id)
    })


@app.route('/api/session/end', methods=['POST'])
def end_session():
    """Explicitly end a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({
            "error": "Missing 'session_id' field",
            "success": False
        }), 400
    
    session_tracker.end_session(session_id)
    session_file = conversation_logger.end_session(trigger_analysis=False)
    
    # Clear session memory
    if service:
        memory_stats = service.get_memory_stats()
        service.clear_memory()
        print(f"📝 Session memory cleared: {memory_stats.get('total_turns', 0)} turns, {memory_stats.get('stocks_discussed', 0)} stocks")
    
    # Trigger improvement pipeline IMMEDIATELY (synchronous) if session file exists
    if session_file and improvement_pipeline:
        print(f"\n🚀 Processing session immediately: {session_file.name}")
        improvement_pipeline.process_session(session_file, async_mode=False)
        print(f"✅ Session processing complete\n")
    
    return jsonify({
        "success": True,
        "session_file": str(session_file) if session_file else None
    })


@app.route('/api/memory', methods=['GET'])
def get_memory():
    """Get current session memory state."""
    if not service:
        return jsonify({"error": "Service not initialized"}), 500
    
    memory = service.get_memory()
    return jsonify({
        "stats": memory.get_stats(),
        "stocks_discussed": memory.get_mentioned_stocks(),
        "recent_analyses": memory.get_recent_analyses(5),
        "recent_history": [
            {"turn": h['turn'], "user": h['user_input'][:50], "type": h['request_type']}
            for h in memory.get_recent_history(5)
        ],
        "context_prompt": memory.get_context_prompt(),
        "success": True
    })


@app.route('/api/memory/stocks', methods=['GET'])
def get_memory_stocks():
    """Get all stocks tracked in session memory."""
    if not service:
        return jsonify({"error": "Service not initialized"}), 500
    
    memory = service.get_memory()
    stocks = {}
    for symbol in memory.get_mentioned_stocks():
        stock_data = memory.get_stock(symbol)
        if stock_data:
            stocks[symbol] = {
                'name': stock_data.get('name'),
                'price': stock_data.get('price'),
                'sector': stock_data.get('sector'),
                'analyses_count': len(stock_data.get('analyses', [])),
                'first_mentioned': stock_data.get('first_mentioned'),
                'last_updated': stock_data.get('last_updated')
            }
    
    return jsonify({
        "stocks": stocks,
        "count": len(stocks),
        "success": True
    })


@app.route('/api/memory/clear', methods=['POST'])
def clear_memory():
    """Clear session memory (for testing/reset)."""
    if not service:
        return jsonify({"error": "Service not initialized"}), 500
    
    stats_before = service.get_memory_stats()
    service.clear_memory()
    
    return jsonify({
        "success": True,
        "cleared": stats_before,
        "message": f"Cleared {stats_before.get('total_turns', 0)} turns, {stats_before.get('stocks_discussed', 0)} stocks"
    })


@app.route('/api/improvements', methods=['GET'])
def get_improvements():
    """Get list of applied improvements."""
    if not improvement_pipeline:
        return jsonify({
            "error": "Improvement pipeline not initialized",
            "success": False
        }), 500
    
    history = improvement_pipeline.applier.history
    return jsonify({
        "improvements": history.get('applied', []),
        "success": True
    })


@app.route('/api/improvements/rollback/<improvement_id>', methods=['POST'])
def rollback_improvement(improvement_id: str):
    """Rollback a specific improvement."""
    if not improvement_pipeline:
        return jsonify({
            "error": "Improvement pipeline not initialized",
            "success": False
        }), 500
    
    success, error = improvement_pipeline.applier.rollback_improvement(improvement_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": f"Rolled back improvement {improvement_id}"
        })
    else:
        return jsonify({
            "success": False,
            "error": error or "Unknown error"
        }), 400


if __name__ == '__main__':
    print("=" * 60)
    print("Stock Agent API Server")
    print("=" * 60)
    
    if not init_service():
        print("Failed to initialize service. Exiting.")
        sys.exit(1)
    
    print("\n🚀 Starting API server on http://localhost:5001")
    print("Endpoints:")
    print("  POST /api/chat - Send chat messages")
    print("  POST /api/session/start - Start new session")
    print("  POST /api/heartbeat - Keep session alive")
    print("  POST /api/session/end - End session")
    print("  GET  /api/context - Get conversation context")
    print("  GET  /api/memory - Get session memory state")
    print("  GET  /api/memory/stocks - Get tracked stocks")
    print("  POST /api/memory/clear - Clear session memory")
    print("  GET  /api/config - Get configuration")
    print("  GET  /api/health - Health check")
    print("\n📝 Session memory active - tracks stocks, analyses, downloads")
    print("📊 Self-improvement system active - conversations will be logged")
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
