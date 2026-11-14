import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

if __name__ == "__main__":
    import uvicorn
    print("=" * 65)
    print("🚀 Starting Multi-Agent Stock Research Analyst - Backend API")
    print("📡 Serving on: http://127.0.0.1:8000")
    print("📖 Interactive API Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
