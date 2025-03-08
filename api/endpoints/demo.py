# app/api/endpoints/demo.py
import time
from fastapi import APIRouter, Depends, Header, Query
from typing import Optional, Dict, Any

router = APIRouter()

@router.get("/limited")
async def limited_endpoint():
    """
    A demo endpoint that is rate limited.
    This endpoint is protected by the rate limiter middleware.
    """
    # Simulate some processing time
    time.sleep(0.1)
    
    return {
        "message": "This is a rate-limited endpoint",
        "timestamp": time.time()
    }

@router.get("/unlimited")
async def unlimited_endpoint():
    """
    A demo endpoint that is not rate limited.
    This is for comparison purposes only.
    """
    # Simulate some processing time
    time.sleep(0.1)
    
    return {
        "message": "This is an unlimited endpoint",
        "timestamp": time.time()
    }

@router.get("/custom-limit")
async def custom_limit_endpoint(
    limit: int = Query(10, description="Custom token limit"),
    refill_rate: float = Query(0.5, description="Custom refill rate (tokens per second)")
):
    """
    A demo endpoint with custom rate limit parameters.
    This demonstrates how to apply different rate limits to different endpoints.
    """
    # Note: In a real implementation, you would apply custom limits in the middleware
    # This is just for demonstration purposes
    
    return {
        "message": "This endpoint has custom rate limits",
        "custom_limit": limit,
        "custom_refill_rate": refill_rate,
        "timestamp": time.time()
    }