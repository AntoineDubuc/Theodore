#!/usr/bin/env python3
"""
Inspect crawl4ai.config module to find LLMConfig or equivalent
"""

try:
    import crawl4ai.config as config
    print("Available in crawl4ai.config:")
    for attr in dir(config):
        if not attr.startswith('_'):
            print(f"  {attr}: {type(getattr(config, attr))}")
    
    # Check for LLM-related classes
    llm_attrs = [attr for attr in dir(config) if 'llm' in attr.lower() or 'LLM' in attr]
    print(f"\nLLM-related attributes: {llm_attrs}")
    
except Exception as e:
    print(f"Error inspecting config: {e}")

try:
    # Check extraction_strategy module for LLMConfig
    import crawl4ai.extraction_strategy as extraction
    print("\nAvailable in crawl4ai.extraction_strategy:")
    for attr in dir(extraction):
        if not attr.startswith('_'):
            obj = getattr(extraction, attr)
            print(f"  {attr}: {type(obj)}")
    
    # Look for config-related classes
    config_attrs = [attr for attr in dir(extraction) if 'config' in attr.lower() or 'Config' in attr]
    print(f"\nConfig-related attributes: {config_attrs}")
    
except Exception as e:
    print(f"Error inspecting extraction_strategy: {e}")

try:
    # Check the main crawl4ai module
    import crawl4ai
    print("\nAvailable in main crawl4ai module:")
    for attr in dir(crawl4ai):
        if not attr.startswith('_'):
            obj = getattr(crawl4ai, attr)
            print(f"  {attr}: {type(obj)}")
    
    # Look for LLM or config related
    relevant_attrs = [attr for attr in dir(crawl4ai) if any(term in attr.lower() for term in ['llm', 'config'])]
    print(f"\nRelevant attributes: {relevant_attrs}")
    
except Exception as e:
    print(f"Error inspecting main module: {e}")

# Try to find LLMConfig by searching all modules
try:
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    print(f"\nLLMExtractionStrategy found: {LLMExtractionStrategy}")
    
    # Get the signature to see what it expects for llm_config
    import inspect
    sig = inspect.signature(LLMExtractionStrategy.__init__)
    print("LLMExtractionStrategy.__init__ parameters:")
    for param_name, param in sig.parameters.items():
        print(f"  {param_name}: {param.annotation} = {param.default}")
        
except Exception as e:
    print(f"Error inspecting LLMExtractionStrategy: {e}")