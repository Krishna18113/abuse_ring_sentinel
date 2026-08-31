from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Abuse Ring Sentinel API",
        description="Production Merchant Risk Investigation & Evidence Engine API",
        version="1.0.0"
    )
    
    # Configure CORS for local frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router)
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "abuse-ring-sentinel"}
        
    return app

app = create_app()
