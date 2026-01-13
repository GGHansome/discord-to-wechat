from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class DiscordMessage:
    id: str
    content: str
    username: str
    timestamp: datetime
    channel_url: str
    attachments: List[str] = field(default_factory=list)
    channel_name: Optional[str] = None

