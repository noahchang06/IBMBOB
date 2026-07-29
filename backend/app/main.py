from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
from app.data.knowledge_base import knowledge_base
from app.db.sqlite_repository import SQLiteRepository

repo = SQLiteRepository()

@asynccontextmanager
async def lifespan(app: FastAPI):
    knowledge_base.load()
    await repo.init_db()
    yield

app = FastAPI(title="Creative Reasoning Platform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
