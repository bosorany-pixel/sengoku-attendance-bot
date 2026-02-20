"""Pydantic models for API responses."""
from typing import Optional, List
from pydantic import BaseModel, field_serializer


class MemberResponse(BaseModel):
    """Response model for a member with stats."""
    uid: int  # Stored as int in DB, serialized as str in JSON
    display_name: str
    event_count: int
    total_amount: float
    pov_count: int = 0
    checked_pov_count: int = 0
    last_pov: Optional[str] = None
    last_checked_pov: Optional[str] = None

    @field_serializer('uid')
    def serialize_uid(self, uid: int) -> str:
        """Serialize UID as string to preserve precision in JavaScript."""
        return str(uid)


class EventResponse(BaseModel):
    """Response model for an event."""
    message_id: int
    guild_id: int
    channel_id: int
    channel_name: str
    message_text: str
    read_time: Optional[str]
    disband: int
    points: Optional[int]
    hidden: int

    @field_serializer("message_id", "guild_id", "channel_id")
    def serialize_snowflake(self, value: int) -> str:
        """Serialize Discord snowflake IDs as strings to avoid JS number precision loss."""
        return str(value)


class PaymentResponse(BaseModel):
    """Response model for a payment."""
    payment_sum: float
    message_id: int
    channel_id: int
    guild_id: int
    payment_ammount: float
    user_amount: int
    pay_time: Optional[str]

    @field_serializer("message_id", "guild_id", "channel_id")
    def serialize_snowflake(self, value: int) -> str:
        """Serialize Discord snowflake IDs as strings to avoid JS number precision loss."""
        return str(value)


class ArchiveResponse(BaseModel):
    """Response model for an archive."""
    file: str
    name: str


class UserDetailResponse(BaseModel):
    """Response model for user details."""
    uid: int  # Stored as int in DB, serialized as str in JSON
    display_name: str
    pov_count: int = 0
    checked_pov_count: int = 0
    last_pov: Optional[str] = None
    last_checked_pov: Optional[str] = None
    
    @field_serializer('uid')
    def serialize_uid(self, uid: int) -> str:
        """Serialize UID as string to preserve precision in JavaScript."""
        return str(uid)


class MembersListResponse(BaseModel):
    """Response for members list endpoint."""
    members: List[MemberResponse]
    total_count: int


class UserEventsResponse(BaseModel):
    """Response for user events endpoint."""
    user: UserDetailResponse
    events: List[EventResponse]
    total_count: int


class UserPaymentsResponse(BaseModel):
    """Response for user payments endpoint."""
    user: UserDetailResponse
    payments: List[PaymentResponse]
    total_count: int


class ArchivesListResponse(BaseModel):
    """Response for archives list endpoint."""
    archives: List[ArchiveResponse]


class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str
    technical_timeout: bool


class LevelResponse(BaseModel):
    """Response model for a BP level (attendance threshold)."""
    level: int
    attendance: int


class AchievementResponse(BaseModel):
    """Response model for an achievement."""
    id: int
    bp_level: int
    description: str
    picture: str


class LevelsAndAchievementsResponse(BaseModel):
    """Response for levels and achievements list endpoint (no user data)."""
    levels: List[LevelResponse]
    achievements: List[AchievementResponse]


class UserAchievementsResponse(BaseModel):
    """Response for user achievements endpoint."""
    user: UserDetailResponse
    achievements: List[AchievementResponse]
    total_count: int
