#!/usr/bin/env python3
"""
簡易サーバー起動テスト
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Server")

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Backend server is operational"
    }

if __name__ == "__main__":
    print("🚀 Starting test server on http://localhost:8000")
    print("📋 Available endpoints:")
    print("   GET / - Root endpoint")
    print("   GET /health - Health check")
    uvicorn.run(app, host="0.0.0.0", port=8000)