"""
最小構成のFastAPIアプリケーション
起動テスト用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="バイト求人マッチングシステム",
    description="Minimal Test Version",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Backend is running!",
        "status": "healthy",
        "version": "0.0.1"
    }

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "healthy"}

@app.get("/api/v1/test")
async def test():
    """テストエンドポイント"""
    return {"message": "API is working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)