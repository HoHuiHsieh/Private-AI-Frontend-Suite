"""
Usage Manager

Handles usage tracking, aggregation, and analytics.
"""
import subprocess
import json
from datetime import datetime, timedelta, timezone, date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct
from collections import defaultdict

from database import UsageDB, UserDB
from config import get_config
from .models import (
    UsageRecord,
    DailyUsage,
    UsageOverview,
    ModelUsage,
    DailyUsage,
    SystemOverview,
    GPUStatus
)


class UsageManager:
    """Manager for usage tracking and analytics."""

    def __init__(self):
        """Initialize usage manager."""
        pass

    def calculate_time_range(
        self,
        days: Optional[int] = None,
        interval: Optional[str] = None,
        period: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """
        Calculate time range for queries based on parameters.

        Priority: start_date/end_date > days > interval+period

        Args:
            days: Direct number of days to query
            interval: One of "day", "week", "month"
            period: Number of intervals
            start_date: Explicit start date
            end_date: Explicit end date

        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        now = datetime.now(timezone.utc)

        # Priority 1: Explicit start/end dates
        if start_date and end_date:
            return (start_date, end_date)

        # Priority 2: Days parameter
        if days is not None:
            start = now - timedelta(days=days)
            return (start, now)

        # Priority 3: Interval + Period
        if interval and period:
            if interval == "day":
                start = now - timedelta(days=period)
            elif interval == "week":
                start = now - timedelta(weeks=period)
            elif interval == "month":
                # Approximate month as 30 days
                start = now - timedelta(days=period * 30)
            else:
                start = now - timedelta(days=30)  # Default
            return (start, now)

        # Default: Last 30 days
        start = now - timedelta(days=30)
        return (start, now)

    def get_user_usage_overview(
        self,
        db: Session,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> UsageOverview:
        """
        Get usage overview for a specific user.

        Args:
            db: Database session
            user_id: User ID
            start_date: Start of time range
            end_date: End of time range

        Returns:
            UsageOverview object
        """
        # Query total tokens and requests
        total_query = db.query(
            func.sum(UsageDB.total_tokens).label('total_tokens'),
            func.count(UsageDB.id).label('total_requests')
        ).filter(
            and_(
                UsageDB.user_id == str(user_id),
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).first()

        total_tokens = total_query.total_tokens or 0
        total_requests = total_query.total_requests or 0

        # Query daily data
        daily_query = db.query(
            func.date(UsageDB.timestamp).label('date'),
            func.sum(UsageDB.total_tokens).label('tokens'),
            func.count(UsageDB.id).label('requests')
        ).filter(
            and_(
                UsageDB.user_id == str(user_id),
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).group_by(
            func.date(UsageDB.timestamp)
        ).order_by(
            func.date(UsageDB.timestamp)
        ).all()

        daily_data = [
            DailyUsage(date=row.date, tokens=row.tokens or 0,
                       requests=row.requests or 0)
            for row in daily_query
        ]

        return UsageOverview(
            total_tokens=total_tokens,
            total_requests=total_requests,
            period_start=start_date,
            period_end=end_date,
            daily_data=daily_data
        )

    def get_user_model_usage(
        self,
        db: Session,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[ModelUsage]:
        """
        Get per-model usage for a specific user.

        Args:
            db: Database session
            user_id: User ID
            start_date: Start of time range
            end_date: End of time range

        Returns:
            List of ModelUsage objects sorted by total_requests descending
        """
        # Query models with total requests
        model_query = db.query(
            UsageDB.model,
            func.count(UsageDB.id).label('total_requests'),
            func.sum(UsageDB.total_tokens).label('total_tokens')
        ).filter(
            and_(
                UsageDB.user_id == str(user_id),
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).group_by(
            UsageDB.model
        ).order_by(
            func.count(UsageDB.id).desc()
        ).all()

        # For each model, get daily request counts
        model_usage_list = []
        for row in model_query:
            model_name = row.model
            total_requests = row.total_requests
            total_tokens = row.total_tokens

            # Query daily data for this model
            daily_query = db.query(
                func.date(UsageDB.timestamp).label('date'),
                func.sum(UsageDB.total_tokens).label('tokens'),
                func.count(UsageDB.id).label('requests')
            ).filter(
                and_(
                    UsageDB.user_id == str(user_id),
                    UsageDB.model == model_name,
                    UsageDB.timestamp >= start_date,
                    UsageDB.timestamp <= end_date
                )
            ).group_by(
                func.date(UsageDB.timestamp)
            ).order_by(
                func.date(UsageDB.timestamp)
            ).all()

            daily_data: List[DailyUsage] = [
                DailyUsage(
                    date=row.date,
                    tokens=row.tokens or 0,
                    requests=row.requests or 0
                )
                for row in daily_query]

            model_usage_list.append(ModelUsage(
                model_name=model_name,
                total_requests=total_requests,
                total_tokens=total_tokens,
                period_start=start_date,
                period_end=end_date,
                daily_data=daily_data
            ))
        return model_usage_list

    def get_user_usage_logs(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UsageRecord]:
        """
        Get paginated usage logs for a specific user.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            start_date: Optional start of time range
            end_date: Optional end of time range

        Returns:
            List of UsageRecord objects sorted by timestamp descending
        """
        query = db.query(UsageDB).filter(UsageDB.user_id == str(user_id))

        if start_date:
            query = query.filter(UsageDB.timestamp >= start_date)
        if end_date:
            query = query.filter(UsageDB.timestamp <= end_date)

        db_records = query.order_by(
            UsageDB.timestamp.desc()
        ).offset(skip).limit(limit).all()

        return [self._db_usage_to_model(record) for record in db_records]

    def get_system_overview(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> SystemOverview:
        """
        Get system-wide usage overview (admin only).

        Args:
            db: Database session
            start_date: Start of time range
            end_date: End of time range

        Returns:
            SystemOverview object
        """
        # Query total tokens and requests
        total_query = db.query(
            func.sum(UsageDB.total_tokens).label('total_tokens'),
            func.count(UsageDB.id).label('total_requests')
        ).filter(
            and_(
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).first()

        total_tokens = total_query.total_tokens or 0
        total_requests = total_query.total_requests or 0

        # Query total users (all users in system)
        total_users = db.query(func.count(distinct(UserDB.id))).scalar() or 0

        # Query active users (users with requests in period)
        active_users = db.query(
            func.count(distinct(UsageDB.user_id))
        ).filter(
            and_(
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).scalar() or 0

        # Query daily data
        daily_query = db.query(
            func.date(UsageDB.timestamp).label('date'),
            func.sum(UsageDB.total_tokens).label('tokens'),
            func.count(UsageDB.id).label('requests')
        ).filter(
            and_(
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).group_by(
            func.date(UsageDB.timestamp)
        ).order_by(
            func.date(UsageDB.timestamp)
        ).all()

        daily_data = [
            DailyUsage(date=row.date, tokens=row.tokens or 0,
                       requests=row.requests or 0)
            for row in daily_query
        ]

        return SystemOverview(
            total_tokens=total_tokens,
            total_requests=total_requests,
            total_users=total_users,
            active_users=active_users,
            period_start=start_date,
            period_end=end_date,
            daily_data=daily_data
        )

    def get_system_model_usage(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[ModelUsage]:
        """
        Get system-wide per-model usage (admin only).

        Args:
            db: Database session
            start_date: Start of time range
            end_date: End of time range

        Returns:
            List of ModelUsage objects sorted by total_requests descending
        """
        # Query models with total requests
        model_query = db.query(
            UsageDB.model,
            func.count(UsageDB.id).label('total_requests'),
            func.sum(UsageDB.total_tokens).label('total_tokens')
        ).filter(
            and_(
                UsageDB.timestamp >= start_date,
                UsageDB.timestamp <= end_date
            )
        ).group_by(
            UsageDB.model
        ).order_by(
            func.count(UsageDB.id).desc()
        ).all()

        # For each model, get daily request counts
        model_usage_list = []
        for row in model_query:
            model_name = row.model
            total_requests = row.total_requests
            total_tokens = row.total_tokens

            # Query daily data for this model
            daily_query = db.query(
                func.date(UsageDB.timestamp).label('date'),
                func.sum(UsageDB.total_tokens).label('tokens'),
                func.count(UsageDB.id).label('requests')
            ).filter(
                and_(
                    UsageDB.model == model_name,
                    UsageDB.timestamp >= start_date,
                    UsageDB.timestamp <= end_date
                )
            ).group_by(
                func.date(UsageDB.timestamp)
            ).order_by(
                func.date(UsageDB.timestamp)
            ).all()

            daily_data: List[DailyUsage] = [
                DailyUsage(
                    date=row.date,
                    tokens=row.tokens or 0,
                    requests=row.requests or 0
                )
                for row in daily_query]

            model_usage_list.append(ModelUsage(
                model_name=model_name,
                total_requests=total_requests,
                total_tokens=total_tokens,
                period_start=start_date,
                period_end=end_date,
                daily_data=daily_data
            ))

        return model_usage_list

    def _db_usage_to_model(self, db_usage: UsageDB) -> UsageRecord:
        """Convert database usage record to model usage record."""
        # Parse extra_data if it's a JSON string
        extra_data = db_usage.extra_data
        if extra_data is not None and isinstance(extra_data, str):
            try:
                extra_data = json.loads(extra_data)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, keep as None or original value
                extra_data = None

        return UsageRecord(
            id=db_usage.id,
            user_id=db_usage.user_id,
            timestamp=db_usage.timestamp,
            model=db_usage.model,
            api_type=db_usage.api_type,
            prompt_tokens=db_usage.prompt_tokens,
            completion_tokens=db_usage.completion_tokens,
            total_tokens=db_usage.total_tokens,
            request_id=db_usage.request_id,
            input_count=db_usage.input_count,
            extra_data=extra_data,
            hostname=db_usage.hostname,
            process_id=db_usage.process_id,
            created_at=db_usage.created_at
        )


def get_gpu_status() -> List[GPUStatus]:
    """
    Get current GPU status.

    This function returns pseudo/mock data for testing and development.
    In production, replace with actual GPU monitoring using pynvml.

    Returns:
        List of GPUStatus objects with mock data
    """
    # # Return mock GPU data for testing
    # # In production, replace with actual GPU monitoring code
    # mock_gpus = [
    #     GPUStatus(
    #         gpu_id="0",
    #         label="NVIDIA Tesla V100",
    #         memory_used_gb=12.5,
    #         memory_total_gb=32.0,
    #         utilization_percent=75.3,
    #         temperature_celsius=68.0
    #     ),
    #     GPUStatus(
    #         gpu_id="1",
    #         label="NVIDIA Tesla V100",
    #         memory_used_gb=8.2,
    #         memory_total_gb=32.0,
    #         utilization_percent=45.7,
    #         temperature_celsius=62.0
    #     ),
    #     GPUStatus(
    #         gpu_id="2",
    #         label="NVIDIA A100",
    #         memory_used_gb=28.9,
    #         memory_total_gb=40.0,
    #         utilization_percent=92.1,
    #         temperature_celsius=73.5
    #     )
    # ]

    # return mock_gpus

    # Uncomment below for actual GPU monitoring with pynvml:
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        gpus = []

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

            try:
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = None

            gpus.append(GPUStatus(
                gpu_id=str(i),
                label=pynvml.nvmlDeviceGetName(handle),
                memory_used_gb=mem_info.used / (1024**3),
                memory_total_gb=mem_info.total / (1024**3),
                utilization_percent=float(utilization.gpu),
                temperature_celsius=float(temp) if temp is not None else None
            ))

        pynvml.nvmlShutdown()
        return gpus
    except Exception as e:
        print(f"GPU monitoring error: {e}")
        return []
