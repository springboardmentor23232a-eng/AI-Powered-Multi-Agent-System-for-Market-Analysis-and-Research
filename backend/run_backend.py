import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Starting Multi-Agent Stock Research Analyst - Backend API")
    print("📡 Serving on: http://127.0.0.1:8000")
    print("📖 Interactive API Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
