import uvicorn
import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    print("Starting Uvicorn server...")
    print(f"Routes: {[r.path for r in app.routes]}")
    uvicorn.run(app, host="127.0.0.1", port=8001)
