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
import sys
import io

# Remplace stdout par un flux utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Gestionnaire de cycle de vie
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    # Initialize WebSocket manager with the current event loop
    ws_manager.set_loop(asyncio.get_running_loop())
    yield
    # clean up code
    ws_manager.close_all_connections()
    pass

app = FastAPI(
    title="EasyAstro API", 
    version="1.0.0",
    lifespan=lifespan  # Lifecycle manager
)

# CORS Configuration 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        f"http://*:{config.CONFIG['global']['server_port']}"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Serve frontend static files
frontend_path = Path(__file__).parent / "frontend" 
app.mount("/assets", StaticFiles(directory=frontend_path / "assets"), name="assets")
app.mount("/catalog", StaticFiles(directory=frontend_path / "catalog"), name="catalog")

# root `/` => serve index.html
@app.get("/")
def serve_index():
    return FileResponse(frontend_path / "index.html")

# For all unknown paths, serve the React app
@app.get("/frontend/{path:path}")
def serve_react_app(path: str):
    file_path = frontend_path / path
    if file_path.exists() and file_path.is_file():
        print(f"Serving file: {file_path}")
        return FileResponse(file_path)  # ex: favicon.ico
    return FileResponse(frontend_path / "index.html")  # fallback pour React Router


if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("main:app", host=config.CONFIG['global']["server_ip"], port=config.CONFIG['global']["server_port"], reload=config.CONFIG['global']['reload_on_change'])