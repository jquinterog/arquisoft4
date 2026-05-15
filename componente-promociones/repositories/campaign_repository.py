from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.campaign_enums import CampaignStatus, CampaignType, Channel
from app.models.campaign import Campaign


class CampaignRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, campaign: Campaign) -> Campaign:
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def get_by_id(self, campaign_id: UUID) -> Campaign | None:
        return self.db.get(Campaign, campaign_id)

    def list_filtered(
        self,
        status: CampaignStatus | None = None,
        channel: Channel | None = None,
        campaign_type: CampaignType | None = None,
    ) -> list[Campaign]:
        stmt = select(Campaign)

        if status:
            stmt = stmt.where(Campaign.status == status)
        if channel:
            stmt = stmt.where(Campaign.channel == channel)
        if campaign_type:
            stmt = stmt.where(Campaign.type == campaign_type)

        stmt = stmt.order_by(Campaign.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def update(self, campaign: Campaign, updates: dict) -> Campaign:
        for field, value in updates.items():
            setattr(campaign, field, value)

        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
