from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import get_current_user, require_write
from app.database import get_db
from app.models import LogCreate, LogResponse, AggregationResponse
from app.services import log_service, aggregation_service

router = APIRouter(prefix="/api/metrics/{metric_id}/logs", tags=["logs"])


@router.post("", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    metric_id: int,
    data: LogCreate,
    user: dict = Depends(require_write),
):
    async with get_db() as db:
        result = await log_service.create_log(db, metric_id, user["id"], data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found or invalid dimension/category",
        )
    return result


@router.get("", response_model=AggregationResponse)
async def get_logs(
    request: Request,
    metric_id: int,
    range: str = Query("W"),
    aggregate: str = Query("count"),
    group_by: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    # Parse filter_* params from query string (e.g. filter_Location=Home)
    filters: dict[str, str] = {}
    for key, value in request.query_params.items():
        if key.startswith("filter_"):
            dim_name = key[7:]  # Remove "filter_" prefix
            filters[dim_name] = value

    async with get_db() as db:
        result = await aggregation_service.aggregate_logs(
            db,
            metric_id=metric_id,
            user_id=user["id"],
            range_key=range,
            aggregate=aggregate,
            group_by=group_by,
            filters=filters if filters else None,
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found",
        )
    return result


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    metric_id: int,
    log_id: int,
    user: dict = Depends(require_write),
):
    async with get_db() as db:
        deleted = await log_service.delete_log(db, metric_id, log_id, user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found",
        )
