from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, require_write
from app.database import get_db
from app.models import MetricCreate, MetricResponse, MetricListItem
from app.services import metric_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=list[MetricListItem])
async def list_metrics(user: dict = Depends(get_current_user)):
    async with get_db() as db:
        return await metric_service.list_metrics(db, user["id"])


@router.post("", response_model=MetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(data: MetricCreate, user: dict = Depends(require_write)):
    async with get_db() as db:
        return await metric_service.create_metric(db, user["id"], data)


@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(metric_id: int, user: dict = Depends(get_current_user)):
    async with get_db() as db:
        result = await metric_service.get_metric(db, user["id"], metric_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    return result


@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(metric_id: int, user: dict = Depends(require_write)):
    async with get_db() as db:
        deleted = await metric_service.delete_metric(db, user["id"], metric_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
