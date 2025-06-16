from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, hotels, reservations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 HotelMate API starting up...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔥 Firebase Project: {settings.FIREBASE_PROJECT_ID}")
    print("✅ Server ready!")

    yield

    # Shutdown
    print("🛑 HotelMate API shutting down...")
    print("👋 Goodbye!")


# Create FastAPI instance
app = FastAPI(
    title="HotelMate API",
    description="Backend API for HotelMate - hotel booking application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(hotels.router, prefix="/api/hotels", tags=["Hotels"])
app.include_router(reservations.router, prefix="/api/reservations", tags=["Reservations"])


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "HotelMate API is running! 🏨",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
