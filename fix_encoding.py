#!/usr/bin/env python3
"""
Fix encoding issues in Python file
"""

def fix_encoding(filename):
    """Fix encoding issues in file"""
    try:
        # Try reading with different encodings
        content = None
        for encoding in ['utf-8', 'cp1252', 'latin1', 'utf-8-sig']:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ Successfully read with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # If all else fails, read as binary and clean
            with open(filename, 'rb') as f:
                binary_data = f.read()
            
            # Replace problematic bytes
            cleaned_data = binary_data.replace(b'\x93', b'"')  # Smart quote
            cleaned_data = cleaned_data.replace(b'\x8d', b' ')  # Replace with space
            cleaned_data = cleaned_data.replace(b'\x94', b'"')  # Smart quote
            cleaned_data = cleaned_data.replace(b'\x91', b"'")  # Smart quote
            cleaned_data = cleaned_data.replace(b'\x92', b"'")  # Smart quote
            
            # Convert to string
            content = cleaned_data.decode('utf-8', errors='ignore')
            print("✅ Cleaned binary data and converted to UTF-8")
        
        # Write back as UTF-8
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed encoding for {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing encoding: {e}")
        return False

if __name__ == "__main__":
    success = fix_encoding("run_user_controlled_automation.py")
    if success:
        print("🎉 File encoding fixed! Try running again.")
    else:
        print("❌ Failed to fix encoding.") 