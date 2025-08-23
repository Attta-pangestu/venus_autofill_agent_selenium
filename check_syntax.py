#!/usr/bin/env python3
"""
Simple syntax checker untuk mencari error di file python
"""

import ast
import sys

def check_syntax(filename):
    """Check syntax of Python file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content, filename=filename)
        print(f"✅ Syntax check PASSED for {filename}")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error in {filename}:")
        print(f"   Line {e.lineno}: {e.text.strip() if e.text else 'N/A'}")
        print(f"   Error: {e.msg}")
        print(f"   Position: {' ' * (e.offset - 1) if e.offset else ''}^")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error checking {filename}: {e}")
        return False

if __name__ == "__main__":
    filename = "run_user_controlled_automation.py"
    success = check_syntax(filename)
    sys.exit(0 if success else 1) 