"""
Usage Tracking and Health Monitoring API Routes

================================================================================
USER USAGE ENDPOINTS
================================================================================

1. GET /api/usage/overview
   - Auth: Required (Bearer token)
   - Query Params: days?, interval?, period?, start_date?, end_date?
   - Returns: UsageOverview for authenticated user
   - Aggregate: Sum tokens and requests per day within the time range
   - Filter: Only data for the authenticated user

2. GET /api/usage/models
   - Auth: Required (Bearer token)
   - Query Params: days?, interval?, period?, start_date?, end_date?
   - Returns: ModelUsage[] (array of per-model usage)
   - Group by: model field
   - Filter: Only models used by authenticated user
   - Sort: By total_requests descending

3. GET /api/usage/logs
   - Auth: Required (Bearer token)
   - Query Params: skip (default: 0), limit (default: 100), days?, interval?, period?
   - Returns: UsageRecord[] (paginated logs)
   - Filter: Only logs for authenticated user
   - Sort: By timestamp descending (newest first)
   - Include: All fields from UsageRecord

================================================================================
ADMIN HEALTH ENDPOINTS
================================================================================

4. GET /api/admin/health/overview
   - Auth: Required (admin scope)
   - Query Params: days?, interval?, period?, start_date?, end_date?
   - Returns: SystemOverview with system-wide statistics
   - Aggregate: Sum ALL users' tokens and requests per day
   - Include: total_users (all users), active_users (users with requests in period)
   - Filter: None (system-wide data)

5. GET /api/admin/health/models
   - Auth: Required (admin scope)
   - Query Params: days?, interval?, period?, start_date?, end_date?
   - Returns: ModelUsage[] (system-wide model usage)
   - Group by: model field across all users
   - Aggregate: Sum requests for each model per day/week/month
   - Sort: By total_requests descending

6. GET /api/admin/health/gpu
   - Auth: Required (admin scope)
   - Returns: GPUStatus[] (real-time GPU metrics)
   - Source: Query GPU hardware using NVML (NVIDIA) or equivalent
   - Poll: Current GPU state at request time
   - Include: Memory usage, utilization, temperature for each GPU
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_session_factory
from user import get_current_active_user, get_admin_user, User
from .manager import UsageManager, get_gpu_status
from .models import DailyUsage


# Initialize router
router = APIRouter()

# Initialize manager
usage_manager = UsageManager()


def get_db():
    """Get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Response Models
# ============================================================================

class UsageOverviewResponse(BaseModel):
    """Response model for usage overview."""
    total_tokens: int
    total_requests: int
    period_start: str
    period_end: str
    daily_data: List[dict]

    class Config:
        from_attributes = True


class ModelUsageResponse(BaseModel):
    """Response model for model usage."""
    model_name: str
    total_requests: int
    total_tokens: int
    period_start: str
    period_end: str
    daily_data: List[dict]

    class Config:
        from_attributes = True


class UsageRecordResponse(BaseModel):
    """Response model for usage record."""
    id: int
    user_id: str
    timestamp: str
    model: str
    api_type: str
    prompt_tokens: int
    completion_tokens: Optional[int] = None
    total_tokens: int
    request_id: Optional[str] = None
    input_count: Optional[int] = None
    extra_data: Optional[dict] = None
    hostname: Optional[str] = None
    process_id: Optional[int] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SystemOverviewResponse(BaseModel):
    """Response model for system overview."""
    total_tokens: int
    total_requests: int
    total_users: int
    active_users: int
    period_start: str
    period_end: str
    daily_data: List[dict]

    class Config:
        from_attributes = True


class GPUStatusResponse(BaseModel):
    """Response model for GPU status."""
    gpu_id: str
    label: str
    memory_used_gb: float
    memory_total_gb: float
    utilization_percent: float
    temperature_celsius: Optional[float] = None

    class Config:
        from_attributes = True


# ============================================================================
# User Usage Endpoints
# ============================================================================

@router.get("/api/usage/overview", response_model=UsageOverviewResponse, tags=["Usage"])
async def get_usage_overview(
    days: Optional[int] = Query(None, description="Number of days to query"),
    interval: Optional[str] = Query(
        None, description="Interval: day, week, or month"),
    period: Optional[int] = Query(None, description="Number of intervals"),
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get usage overview for the authenticated user.

    Returns aggregated token and request counts for the specified time period.
    """
    # Calculate time range
    start, end = usage_manager.calculate_time_range(
        days=days,
        interval=interval,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Get usage overview
    overview = usage_manager.get_user_usage_overview(
        db, current_user.id, start, end)
    return UsageOverviewResponse(**overview.dict())


@router.get("/api/usage/models", response_model=List[ModelUsageResponse], tags=["Usage"])
async def get_usage_models(
    days: Optional[int] = Query(None, description="Number of days to query"),
    interval: Optional[str] = Query(
        None, description="Interval: day, week, or month"),
    period: Optional[int] = Query(None, description="Number of intervals"),
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get per-model usage breakdown for the authenticated user.

    Returns usage statistics grouped by model, sorted by total requests.
    """
    # Calculate time range
    start, end = usage_manager.calculate_time_range(
        days=days,
        interval=interval,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Get model usage
    model_usage = usage_manager.get_user_model_usage(
        db, current_user.id, start, end)
    return [ModelUsageResponse(**mu.dict()) for mu in model_usage]


@router.get("/api/usage/logs", response_model=List[UsageRecordResponse], tags=["Usage"])
async def get_usage_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of records to return"),
    days: Optional[int] = Query(None, description="Number of days to query"),
    interval: Optional[str] = Query(
        None, description="Interval: day, week, or month"),
    period: Optional[int] = Query(None, description="Number of intervals"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated usage logs for the authenticated user.

    Returns detailed usage records sorted by timestamp (newest first).
    """
    # Calculate time range if specified
    start = None
    end = None
    if days or (interval and period):
        start, end = usage_manager.calculate_time_range(
            days=days,
            interval=interval,
            period=period
        )

    # Get usage logs
    logs = usage_manager.get_user_usage_logs(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        start_date=start,
        end_date=end
    )

    return [UsageRecordResponse(**log.dict()) for log in logs]


# ============================================================================
# Admin Health Endpoints
# ============================================================================

@router.get("/api/admin/health/overview", response_model=SystemOverviewResponse, tags=["Admin Health"])
async def get_system_overview(
    days: Optional[int] = Query(None, description="Number of days to query"),
    interval: Optional[str] = Query(
        None, description="Interval: day, week, or month"),
    period: Optional[int] = Query(None, description="Number of intervals"),
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601)"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide usage overview (admin only).

    Returns aggregated statistics for all users across the system.
    """
    # Calculate time range
    start, end = usage_manager.calculate_time_range(
        days=days,
        interval=interval,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Get system overview
    overview = usage_manager.get_system_overview(db, start, end)
    return SystemOverviewResponse(**overview.dict())


@router.get("/api/admin/health/models", response_model=List[ModelUsageResponse], tags=["Admin Health"])
async def get_system_models(
    days: Optional[int] = Query(None, description="Number of days to query"),
    interval: Optional[str] = Query(
        None, description="Interval: day, week, or month"),
    period: Optional[int] = Query(None, description="Number of intervals"),
    start_date: Optional[datetime] = Query(
        None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(
        None, description="End date (ISO 8601)"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide per-model usage (admin only).

    Returns usage statistics for all models across all users.
    """
    # Calculate time range
    start, end = usage_manager.calculate_time_range(
        days=days,
        interval=interval,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Get model usage
    model_usage = usage_manager.get_system_model_usage(db, start, end)
    return [ModelUsageResponse(**mu.dict()) for mu in model_usage]


@router.get("/api/admin/health/gpu", response_model=List[GPUStatusResponse], tags=["Admin Health"])
async def get_gpu_status_endpoint(
    current_user: User = Depends(get_admin_user)
):
    """
    Get current GPU status (admin only).

    Returns GPU metrics including memory usage, utilization, and temperature.
    Returns mock data for development/testing.
    """
    try:
        gpu_statuses = get_gpu_status()
        return [GPUStatusResponse(**gpu.dict()) for gpu in gpu_statuses]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve GPU status: {str(e)}"
        )
