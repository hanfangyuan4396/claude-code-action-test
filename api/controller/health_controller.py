from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancer health checks.

    Returns:
        dict: Health status information including status, service, and version.
    """
    return {"status": "healthy", "service": "FastAPI Demo API", "version": "1.0.0"}
