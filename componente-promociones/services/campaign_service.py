from datetime import datetime, timezone
from uuid import UUID

from app.enums.campaign_enums import CampaignStatus
from app.exceptions.campaign_exceptions import (
    BusinessRuleViolationException,
    CampaignNotFoundException,
    InvalidCampaignStateException,
)
from app.models.campaign import Campaign
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignService:
    def __init__(self, repository: CampaignRepository):
        self.repository = repository

    def create_campaign(self, payload: CampaignCreate) -> Campaign:
        self._validate_priority(payload.priority)
        self._validate_dates(payload.start_date, payload.end_date)

        campaign = Campaign(
            name=payload.name,
            description=payload.description,
            type=payload.type,
            status=CampaignStatus.DRAFT,
            channel=payload.channel,
            priority=payload.priority,
            start_date=payload.start_date,
            end_date=payload.end_date,
            action_message=payload.action_message,
        )
        return self.repository.create(campaign)

    def list_campaigns(self, status=None, channel=None, campaign_type=None) -> list[Campaign]:
        return self.repository.list_filtered(status=status, channel=channel, campaign_type=campaign_type)

    def get_campaign_by_id(self, campaign_id: UUID) -> Campaign:
        campaign = self.repository.get_by_id(campaign_id)
        if not campaign:
            raise CampaignNotFoundException(str(campaign_id))
        return campaign

    def update_campaign(self, campaign_id: UUID, payload: CampaignUpdate) -> Campaign:
        campaign = self.get_campaign_by_id(campaign_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return campaign

        new_start_date = updates.get("start_date", campaign.start_date)
        new_end_date = updates.get("end_date", campaign.end_date)
        self._validate_dates(new_start_date, new_end_date)

        if "priority" in updates:
            self._validate_priority(updates["priority"])

        return self.repository.update(campaign, updates)

    def activate_campaign(self, campaign_id: UUID) -> Campaign:
        campaign = self.get_campaign_by_id(campaign_id)

        if campaign.status == CampaignStatus.CANCELLED:
            raise InvalidCampaignStateException("A cancelled campaign cannot be activated again.")

        if campaign.status not in {CampaignStatus.DRAFT, CampaignStatus.PAUSED}:
            raise InvalidCampaignStateException("Only campaigns in DRAFT or PAUSED status can be activated.")

        self._validate_dates(campaign.start_date, campaign.end_date)

        if campaign.status == CampaignStatus.EXPIRED or self._is_expired(campaign.end_date):
            raise InvalidCampaignStateException("An expired campaign cannot be activated.")

        return self.repository.update(campaign, {"status": CampaignStatus.ACTIVE})

    def pause_campaign(self, campaign_id: UUID) -> Campaign:
        campaign = self.get_campaign_by_id(campaign_id)

        if campaign.status != CampaignStatus.ACTIVE:
            raise InvalidCampaignStateException("Only ACTIVE campaigns can be paused.")

        return self.repository.update(campaign, {"status": CampaignStatus.PAUSED})

    def cancel_campaign(self, campaign_id: UUID) -> Campaign:
        campaign = self.get_campaign_by_id(campaign_id)

        if campaign.status == CampaignStatus.CANCELLED:
            raise InvalidCampaignStateException("Campaign is already cancelled.")

        return self.repository.update(campaign, {"status": CampaignStatus.CANCELLED})

    @staticmethod
    def _validate_priority(priority: int) -> None:
        if priority < 1:
            raise BusinessRuleViolationException("Priority must be greater than or equal to 1.")

    @staticmethod
    def _validate_dates(start_date: datetime, end_date: datetime) -> None:
        if start_date >= end_date:
            raise BusinessRuleViolationException("start_date must be earlier than end_date.")

    @staticmethod
    def _is_expired(end_date: datetime) -> bool:
        now = datetime.now(timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        return end_date <= now
