from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import api_router
from services import config





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

@app.get("/")
async def root():
    return {"message": "Telescope Control API is running"}

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("main:app", host=config.CONFIG["server_ip"], port=config.CONFIG["server_port"], reload=True)