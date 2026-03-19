from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ValueType(str, Enum):
    none = "none"
    numeric = "numeric"
    categorical = "categorical"


# --- Metric models ---


class DimensionCreate(BaseModel):
    name: str
    categories: list[str]


class MetricCreate(BaseModel):
    name: str
    value_type: ValueType
    unit: Optional[str] = None
    categories: Optional[list[str]] = None
    dimensions: Optional[list[DimensionCreate]] = None


class DimensionCategoryResponse(BaseModel):
    id: int
    name: str


class DimensionResponse(BaseModel):
    id: int
    name: str
    categories: list[DimensionCategoryResponse]


class MetricResponse(BaseModel):
    id: int
    name: str
    value_type: str
    unit: Optional[str] = None
    categories: list[str] = []
    dimensions: list[DimensionResponse] = []
    created_at: str


class MetricListItem(BaseModel):
    id: int
    name: str
    value_type: str
    unit: Optional[str] = None
    latest_value: Optional[str] = None
    latest_recorded_at: Optional[str] = None
    sparkline_data: list[Optional[float]] = []


# --- Log models ---


class LogCreate(BaseModel):
    recorded_at: str
    numeric_value: Optional[float] = None
    categorical_value: Optional[str] = None
    dimensions: Optional[dict[str, str]] = None


class LogResponse(BaseModel):
    id: int
    metric_id: int
    recorded_at: str
    numeric_value: Optional[float] = None
    categorical_value: Optional[str] = None
    dimensions: dict[str, str] = {}
    created_at: str


# --- Aggregation models ---


class AggregationQuery(BaseModel):
    range: str = "W"  # D, W, M, 6M, Y
    aggregate: str = "count"  # count, sum, mean
    group_by: Optional[str] = None
    filters: Optional[dict[str, str]] = None


class SeriesData(BaseModel):
    name: str
    data: list[Optional[float]]


class AggregationResponse(BaseModel):
    labels: list[str]
    series: list[SeriesData]


# --- Auth models ---


class LoginRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    display_name: Optional[str] = None
