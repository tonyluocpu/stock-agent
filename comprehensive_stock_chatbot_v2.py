#!/usr/bin/env python3
"""
Stock Agent Chatbot - CLI Interface
=====================================

This is the CLI interface for the stock agent.
The backend logic is in stock_agent_service.py for easy frontend integration.
"""

import sys
import argparse
from pathlib import Path

# Import service layer
try:
    from stock_agent_service import StockAgentService
    from llm_config import get_llm_client, setup_config_interactive, load_config
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    print("Please ensure all required files are present.")
    sys.exit(1)


class StockAgentCLI:
    """
    CLI interface for the stock agent.
    Uses the service layer for all backend logic.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.name = "Stock Agent Chatbot"
        
        # Check if configuration exists
        config = load_config()
        if not config.get("llm_provider"):
            print("⚠️  No LLM configuration found!")
            print("Running interactive setup...")
            if not setup_config_interactive():
                print("ERROR: Configuration setup failed.")
                sys.exit(1)
        
        # Initialize service
        try:
            self.service = StockAgentService()
            print(f"✅ {self.name} initialized!")
            print(f"   LLM Provider: {config.get('llm_provider', 'unknown')}")
            if config.get('llm_provider') == 'free':
                print(f"   Backend: {config.get('free_backend', 'unknown')}")
            else:
                print(f"   Model: {config.get('openrouter_model', 'unknown')}")
        except Exception as e:
            print(f"ERROR: Failed to initialize service: {e}")
            sys.exit(1)
    
    def chat(self):
        """Main chatbot loop."""
        print(f"\n{self.name} - Chat Mode")
        print("=" * 60)
        print("Hi! I'm your Stock Agent Chatbot!")
        print("I can help with stock data, analysis, and general questions!")
        print("\nExamples:")
        print("  • Stock Data: 'Apple weekly data 2020-2024'")
        print("  • Stock Analysis: 'How is Tesla performing?'")
        print("  • Financial Analysis: 'Stock analysis of NVIDIA'")
        print("  • General Questions: 'What is 2+2?'")
        print("\nType 'quit', 'exit', or 'goodbye' to end.")
        print("Type 'config' to change LLM settings.")
        print("=" * 60)
        print()
        
        while True:
            try:
                user_input = input("Stock Agent> ").strip()
                
                if not user_input:
                    continue
                
                # Handle exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye', 'stop', 'end']:
                    print("\n👋 Goodbye! Thanks for using the Stock Agent!")
                    break
                
                # Handle config command
                if user_input.lower() == 'config':
                    print("\n🔧 Configuration Setup")
                    setup_config_interactive()
                    # Reinitialize service with new config
                    try:
                        self.service = StockAgentService()
                        print("✅ Service reinitialized with new configuration!")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not reinitialize: {e}")
                    continue
                
                # Process request through service layer
                context = self.service.get_context()
                result = self.service.process_request(user_input, context)
                
                # Display response
                if result.get('success'):
                    print(f"\n{result.get('response', '')}")
                    
                    # Add to context
                    self.service.add_to_context(
                        user_input,
                        result.get('response', ''),
                        result.get('type', 'general')
                    )
                else:
                    print(f"\n❌ {result.get('response', 'Request failed')}")
                
                print()  # Blank line for readability
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using the Stock Agent!")
                break
            except EOFError:
                print("\n\n👋 Input closed. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'quit' to exit.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Stock Agent Chatbot')
    parser.add_argument('--chat', '-c', action='store_true', help='Start chatbot mode')
    parser.add_argument('--config', action='store_true', help='Run configuration setup')
    parser.add_argument('--request', '-r', help='Process a single request')
    
    args = parser.parse_args()
    
    if args.config:
        setup_config_interactive()
        return
    
    cli = StockAgentCLI()
    
    if args.request:
        # Process single request
        result = cli.service.process_request(args.request)
        print(result.get('response', 'No response'))
    else:
        # Start chat mode
        cli.chat()


if __name__ == "__main__":
    main()






