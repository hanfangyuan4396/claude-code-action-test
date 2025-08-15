from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import psutil
import os

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float
    memory_usage: dict
    cpu_usage: float


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring service availability
    """
    # Get process info
    process = psutil.Process(os.getpid())
    
    # Get system metrics
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime=process.create_time(),
        memory_usage={
            "rss": memory_info.rss,
            "vms": memory_info.vms
        },
        cpu_usage=cpu_percent
    )