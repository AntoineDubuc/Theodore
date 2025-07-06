#!/usr/bin/env python3
"""
Theodore v2 CLI Entry Point.

Simple entry point that avoids circular import issues.
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add src to path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))
    
    from cli.main import cli
    cli()