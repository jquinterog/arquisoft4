from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from componente_promociones.enums.campaign_enums import CampaignStatus, CampaignType, Channel


class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    type: CampaignType
    channel: Channel
    priority: int = Field(..., ge=1)
    start_date: datetime
    end_date: datetime
    action_message: str = Field(..., min_length=1)


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    type: CampaignType | None = None
    channel: Channel | None = None
    priority: int | None = Field(default=None, ge=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    action_message: str | None = Field(default=None, min_length=1)


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    type: CampaignType
    status: CampaignStatus
    channel: Channel
    priority: int
    start_date: datetime
    end_date: datetime
    action_message: str
    created_at: datetime
    updated_at: datetime
