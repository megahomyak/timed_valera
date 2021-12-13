import json
from dataclasses import dataclass


@dataclass
class Config:
    vk_bot_token: str
    question_hour_in_moscow_timezone: int
    admins_peer_id: int
    starting_question_id: int
    questions_chat_id: int

    @classmethod
    def make(cls, filename="config.json"):
        fields = json.load(open(filename, encoding="utf-8"))
        fields["admin_ids"] = set(fields["admin_ids"])
        return cls(**fields)
