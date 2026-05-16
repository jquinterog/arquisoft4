from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from componente_promociones.kafka import publisher
from componente_promociones.database import get_db
from componente_promociones.enums.campaign_enums import CampaignStatus, CampaignType, Channel
from componente_promociones.repositories.campaign_repository import CampaignRepository
from componente_promociones.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate
from componente_promociones.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def get_campaign_service(db: Session = Depends(get_db)) -> CampaignService:
    repository = CampaignRepository(db)
    return CampaignService(repository)


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(payload: CampaignCreate, service: CampaignService = Depends(get_campaign_service)):
    campaign = service.create_campaign(payload)
    await publisher.publish_campaign_created_safely(campaign)
    return campaign


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(
    status: CampaignStatus | None = Query(default=None),
    channel: Channel | None = Query(default=None),
    type: CampaignType | None = Query(default=None),
    service: CampaignService = Depends(get_campaign_service),
):
    return service.list_campaigns(status=status, channel=channel, campaign_type=type)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: UUID, service: CampaignService = Depends(get_campaign_service)):
    return service.get_campaign_by_id(campaign_id)


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    service: CampaignService = Depends(get_campaign_service),
):
    return service.update_campaign(campaign_id, payload)


@router.patch("/{campaign_id}/activate", response_model=CampaignResponse)
def activate_campaign(campaign_id: UUID, service: CampaignService = Depends(get_campaign_service)):
    return service.activate_campaign(campaign_id)


@router.patch("/{campaign_id}/pause", response_model=CampaignResponse)
def pause_campaign(campaign_id: UUID, service: CampaignService = Depends(get_campaign_service)):
    return service.pause_campaign(campaign_id)


@router.patch("/{campaign_id}/cancel", response_model=CampaignResponse)
def cancel_campaign(campaign_id: UUID, service: CampaignService = Depends(get_campaign_service)):
    return service.cancel_campaign(campaign_id)
