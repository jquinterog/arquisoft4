from enum import Enum


class CampaignType(str, Enum):
    NEXT_BEST_OFFER = "NEXT_BEST_OFFER"
    NEXT_BEST_ACTION = "NEXT_BEST_ACTION"
    DISCOUNT = "DISCOUNT"
    CROSS_SELL = "CROSS_SELL"
    SUPPORT_OFFER = "SUPPORT_OFFER"
    DATA_PLAN_OFFER = "DATA_PLAN_OFFER"


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Channel(str, Enum):
    WEB = "WEB"
    APP = "APP"
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    CALL_CENTER = "CALL_CENTER"
    ALL = "ALL"
