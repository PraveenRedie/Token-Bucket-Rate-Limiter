# app/main.py
from fastapi import FastAPI, Request, Response, Depends
import time

from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

from core.config import settings
from core.exceptions import RateLimitExceeded
from limiter.token_bucket import TokenBucket
from limiter.leaky_bucket import LeakyBucket
from storage.redis_store import RedisStorage
from storage.memory_store import MemoryStorage
from api.endpoints import demo


# Initialize the app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Choose storage backend based on configuration
# For simplicity, we'll use in-memory storage for local development
# and Redis for production
if settings.DEBUG:
    storage = MemoryStorage()
else:
    storage = RedisStorage()

# Initialize rate limiters
token_bucket = TokenBucket(
    storage=storage,
    max_tokens=settings.DEFAULT_TOKENS,
    refill_rate=settings.DEFAULT_REFILL_RATE,
    time_window=settings.DEFAULT_TIME_WINDOW,
)

leaky_bucket = LeakyBucket(
    storage=storage,
    capacity=settings.DEFAULT_TOKENS,
    leak_rate=settings.DEFAULT_REFILL_RATE,
    time_window=settings.DEFAULT_TIME_WINDOW,
)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for certain paths (e.g., docs, health check)
    if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
        return await call_next(request)
    
    # Get client identifier (IP address or API key)
    client_id = request.headers.get("X-API-Key")
    if not client_id:
        client_id = request.client.host
    
    # Get rate limiter strategy from header (default to token bucket)
    strategy = request.headers.get("X-Rate-Limit-Strategy", "token_bucket")
    
    # Choose rate limiter implementation
    if strategy == "leaky_bucket":
        limiter = leaky_bucket
    else:  # Default to token bucket
        limiter = token_bucket
    
    # Construct a unique key for the client and endpoint
    endpoint = request.url.path
    key = f"{client_id}:{endpoint}"
    
    # Try to consume a token
    allowed, metadata = await limiter.consume(key)
    
    if not allowed:
        # If not allowed, return 429 Too Many Requests
        response = Response(
            content={"detail": "Rate limit exceeded"}, 
            status_code=429, 
            media_type="application/json"
        )
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
        response.headers["Retry-After"] = str(metadata["reset"] - int(time.time()))
        
        return response
    
    # Execute the original request
    response = await call_next(request)
    
    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
    response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
    response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include API routers
app.include_router(demo.router, prefix="/api/v1")
