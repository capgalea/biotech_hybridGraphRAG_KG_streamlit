import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

try:
    from app import main
    print(f"DEBUG IMPORTED FROM: {main.__file__}")
    from app.main import app
    print("Successfully imported app")
    
    print("\nRegistered Routes:")
    for route in app.routes:
        print(f"Path: {route.path} | Name: {route.name} | Methods: {route.methods}")

except Exception as e:
    print(f"Error importing app: {e}")
