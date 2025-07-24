from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import api_router
from services import configurator as config
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from ws.websocket_manager import ws_manager
import asyncio

app = FastAPI(title="EasyAstro API", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du router principal
app.include_router(api_router, prefix="/api/v1")


# Serve frontend static files
frontend_path = Path(__file__).parent / "frontend" 
app.mount("/assets", StaticFiles(directory=frontend_path / "assets"), name="assets")
app.mount("/catalog", StaticFiles(directory=frontend_path / "catalog"), name="catalog")
# Route racine `/` => sert index.html
@app.get("/")
def serve_index():
    return FileResponse(frontend_path / "index.html")

# Pour toutes les autres routes inconnues, on sert aussi index.html (React Router)
@app.get("/frontend/{path:path}")
def serve_react_app(path: str):
    file_path = frontend_path / path
    if file_path.exists() and file_path.is_file():
        print(f"Serving file: {file_path}")
        return FileResponse(file_path)  # ex: favicon.ico
    return FileResponse(frontend_path / "index.html")  # fallback pour React Router

@app.on_event("startup")
async def startup_event():
    ws_manager.set_loop(asyncio.get_running_loop())

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("main:app", host=config.CONFIG['global']["server_ip"], port=config.CONFIG['global']["server_port"], reload=True)