"""
Usage data models
"""

from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime, date


@dataclass
class UsageRecord:
    """Usage record data model."""
    id: int
    user_id: str
    timestamp: datetime
    model: str
    api_type: str
    prompt_tokens: int
    completion_tokens: Optional[int] = None
    total_tokens: int = 0
    request_id: Optional[str] = None
    input_count: Optional[int] = None
    extra_data: Optional[dict] = None
    hostname: Optional[str] = None
    process_id: Optional[int] = None
    created_at: Optional[datetime] = None

    def dict(self) -> dict:
        """Convert usage record to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model": self.model,
            "api_type": self.api_type,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "request_id": self.request_id,
            "input_count": self.input_count,
            "extra_data": self.extra_data,
            "hostname": self.hostname,
            "process_id": self.process_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class DailyUsage:
    """Daily usage aggregation."""
    date: date
    tokens: int
    requests: int

    def dict(self) -> dict:
        """Convert daily usage to dictionary representation."""
        return {
            "date": self.date.isoformat() if isinstance(self.date, date) else self.date,
            "tokens": self.tokens,
            "requests": self.requests,
        }


@dataclass
class UsageOverview:
    """Usage overview for a user."""
    total_tokens: int
    total_requests: int
    period_start: datetime
    period_end: datetime
    daily_data: List[DailyUsage] = field(default_factory=list)

    def dict(self) -> dict:
        """Convert usage overview to dictionary representation."""
        return {
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "daily_data": [d.dict() for d in self.daily_data],
        }


@dataclass
class ModelUsage:
    """Model-specific usage data."""
    model_name: str
    total_requests: int
    total_tokens: int
    period_start: datetime
    period_end: datetime
    daily_data: List[DailyUsage] = field(default_factory=list)

    def dict(self) -> dict:
        """Convert model usage to dictionary representation."""
        return {
            "model_name": self.model_name,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "daily_data": [d.dict() for d in self.daily_data],
        }


@dataclass
class SystemOverview:
    """System-wide overview for admin."""
    total_tokens: int
    total_requests: int
    total_users: int
    active_users: int
    period_start: datetime
    period_end: datetime
    daily_data: List[DailyUsage] = field(default_factory=list)

    def dict(self) -> dict:
        """Convert system overview to dictionary representation."""
        return {
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "total_users": self.total_users,
            "active_users": self.active_users,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "daily_data": [d.dict() for d in self.daily_data],
        }


@dataclass
class GPUStatus:
    """GPU status data model."""
    gpu_id: str
    label: str
    memory_used_gb: float
    memory_total_gb: float
    utilization_percent: float
    temperature_celsius: Optional[float] = None

    def dict(self) -> dict:
        """Convert GPU status to dictionary representation."""
        return {
            "gpu_id": self.gpu_id,
            "label": self.label,
            "memory_used_gb": self.memory_used_gb,
            "memory_total_gb": self.memory_total_gb,
            "utilization_percent": self.utilization_percent,
            "temperature_celsius": self.temperature_celsius,
        }
