#!/usr/bin/env python3
"""
Test Local LLM with Financial/Stock Queries
===========================================

Tests the local LLM backend with 25-30 financial language inputs
related to stocks and companies.

This will download the model locally on first run.
"""

import sys
import time
from datetime import datetime

# Test queries covering different financial/stock scenarios
TEST_QUERIES = [
    # Stock Data Download Requests
    "Apple weekly data from 2020 to 2024",
    "Microsoft and Google daily 2023 and 2024",
    "Download Tesla monthly data from IPO to today",
    "NVDA weekly closing prices last year",
    "Amazon and Meta daily data 2022 to 2023",
    "Get Apple opening prices weekly from 2019",
    "Download magnificent 7 monthly data from last year",
    
    # Stock Analysis Requests
    "How is Apple performing today?",
    "What does Tesla stock look like?",
    "Compare Microsoft and Apple stock performance",
    "Show me NVIDIA current stock price",
    "What's happening with Google stock?",
    "How is Amazon doing in the market?",
    "Tell me about Meta stock performance",
    
    # Financial Analysis Requests
    "Stock analysis of NVIDIA",
    "Should I buy Tesla?",
    "Important metrics of Apple",
    "Financial analysis of Microsoft",
    "What are the key financial metrics for Google?",
    "Analyze Amazon's financial health",
    "Should I invest in Meta?",
    "Give me a financial breakdown of Apple",
    
    # Company Information Queries
    "What is Apple's market cap?",
    "Tell me about Tesla's revenue",
    "What sector is NVIDIA in?",
    "Compare Apple and Microsoft financials",
    "What are the key metrics for Amazon?",
    
    # General Financial Questions
    "What is a P/E ratio?",
    "Explain market capitalization",
    "What does EPS mean?",
    "How do I read a balance sheet?",
    "What is the difference between revenue and profit?",
]

def test_local_llm():
    """Test local LLM with financial queries."""
    print("=" * 70)
    print("Local LLM Financial Query Test")
    print("=" * 70)
    print(f"Testing {len(TEST_QUERIES)} financial/stock queries")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configure for local LLM
    print("📦 Configuring for LOCAL LLM backend...")
    print("   This will download the model on first run (~2-4GB)")
    print("   Subsequent runs will be much faster!")
    print()
    
    try:
        # Set up config for local backend
        import json
        config = {
            "llm_provider": "free",
            "free_backend": "local",
            "free_model": "microsoft/Phi-3-mini-4k-instruct",  # Small, fast model
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        # Save config
        with open("llm_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration saved to llm_config.json")
        print(f"   Model: {config['free_model']}")
        print()
        
        # Initialize LLM client
        print("🔄 Initializing local LLM client...")
        print("   (First run: Downloading model - this may take 5-10 minutes)")
        print("   (Subsequent runs: Instant)")
        print()
        
        from llm_config import get_llm_client
        llm_client = get_llm_client()
        
        print("✅ Local LLM client initialized!")
        print()
        
        # Initialize stock agent service
        print("🔄 Initializing Stock Agent Service...")
        from stock_agent_service import StockAgentService
        service = StockAgentService(llm_client=llm_client)
        print("✅ Stock Agent Service initialized!")
        print()
        
        print("=" * 70)
        print("Starting Tests...")
        print("=" * 70)
        print()
        
        # Track results
        results = {
            "total": len(TEST_QUERIES),
            "success": 0,
            "failed": 0,
            "responses": []
        }
        
        # Run tests - memory efficient (process in batches, clear memory)
        import gc
        import torch
        
        batch_size = 5  # Process 5 queries at a time
        
        for batch_start in range(0, len(TEST_QUERIES), batch_size):
            batch_end = min(batch_start + batch_size, len(TEST_QUERIES))
            batch_queries = TEST_QUERIES[batch_start:batch_end]
            
            print(f"\n📦 Processing batch {batch_start//batch_size + 1} (queries {batch_start+1}-{batch_end})")
            print("=" * 70)
            
            for i, query in enumerate(batch_queries, batch_start + 1):
                print(f"\n[{i}/{len(TEST_QUERIES)}] Testing: {query}")
                print("-" * 70)
                
                start_time = time.time()
                
                try:
                    # Process request
                    result = service.process_request(query)
                    
                    elapsed = time.time() - start_time
                    
                    if result.get('success'):
                        results["success"] += 1
                        status = "✅ SUCCESS"
                    else:
                        results["failed"] += 1
                        status = "❌ FAILED"
                    
                    response_preview = result.get('response', '')[:100]
                    if len(result.get('response', '')) > 100:
                        response_preview += "..."
                    
                    print(f"Status: {status} | Type: {result.get('type', 'unknown')} | Time: {elapsed:.1f}s")
                    print(f"Response: {response_preview}")
                    
                    results["responses"].append({
                        "query": query,
                        "status": "success" if result.get('success') else "failed",
                        "type": result.get('type'),
                        "time": elapsed,
                        "response_length": len(result.get('response', ''))
                    })
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    results["failed"] += 1
                    print(f"Status: ❌ ERROR | Time: {elapsed:.1f}s")
                    print(f"Error: {str(e)[:100]}")
                    
                    results["responses"].append({
                        "query": query,
                        "status": "error",
                        "error": str(e)[:200],
                        "time": elapsed
                    })
                
                # Clear memory after each query
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            # Clear memory between batches
            print(f"\n🧹 Clearing memory after batch...")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            time.sleep(1)  # Brief pause between batches
        
        # Print summary
        print("=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"Total Queries: {results['total']}")
        print(f"✅ Successful: {results['success']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"Success Rate: {(results['success']/results['total']*100):.1f}%")
        print()
        
        # Calculate average time
        successful_times = [r['time'] for r in results['responses'] if r.get('status') == 'success']
        if successful_times:
            avg_time = sum(successful_times) / len(successful_times)
            print(f"Average Response Time: {avg_time:.2f}s")
            print(f"Fastest: {min(successful_times):.2f}s")
            print(f"Slowest: {max(successful_times):.2f}s")
        print()
        
        # Show request type breakdown
        type_counts = {}
        for r in results['responses']:
            req_type = r.get('type', 'unknown')
            type_counts[req_type] = type_counts.get(req_type, 0) + 1
        
        print("Request Type Breakdown:")
        for req_type, count in type_counts.items():
            print(f"  {req_type}: {count}")
        print()
        
        # Save detailed results
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        print()
        
        # Recommendations
        print("=" * 70)
        print("Recommendations")
        print("=" * 70)
        
        if results['success'] / results['total'] >= 0.8:
            print("✅ Excellent! Local LLM is working well.")
        elif results['success'] / results['total'] >= 0.6:
            print("⚠️  Good, but some queries failed. Check errors above.")
        else:
            print("❌ Many queries failed. Check model installation and dependencies.")
        
        if successful_times and avg_time > 10:
            print("⚠️  Response times are slow. Consider using a smaller model or GPU.")
        elif successful_times and avg_time < 5:
            print("✅ Response times are good!")
        
        print()
        print("=" * 70)
        print("Test Complete!")
        print("=" * 70)
        
        return results
        
    except ImportError as e:
        print(f"❌ ERROR: Missing dependencies: {e}")
        print()
        print("Install required packages:")
        print("  pip install transformers torch")
        return None
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print()
    print("🚀 Starting Local LLM Financial Query Test")
    print()
    
    # Check if transformers is installed
    try:
        import transformers
        import torch
        print("✅ Required packages found (transformers, torch)")
        print()
    except ImportError:
        print("⚠️  WARNING: transformers or torch not installed")
        print()
        print("Installing required packages...")
        print("Run: pip install transformers torch")
        print()
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting. Please install dependencies first.")
            sys.exit(1)
        print()
    
    # Run tests
    results = test_local_llm()
    
    if results:
        sys.exit(0 if results['success'] / results['total'] >= 0.7 else 1)
    else:
        sys.exit(1)



