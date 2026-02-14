from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import auth, recipes, tags, ingredients, search, upload, import_export, share
from app.core.config import settings

# Register HEIF/HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

app = FastAPI(title="Recipe API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(ingredients.router)
app.include_router(search.router)
app.include_router(upload.router)
app.include_router(import_export.router)
app.include_router(share.router)

# Serve uploaded files - use same path as upload.py
upload_dir = os.path.abspath(settings.UPLOAD_DIR)
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
