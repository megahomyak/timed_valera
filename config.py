import json
from dataclasses import dataclass
from typing import Set


@dataclass
class Config:
    vk_bot_token: str
    question_hour_in_moscow_timezone: int
    admin_ids: Set[int]
    starting_question_id: int
    questions_chat_id: int

    @classmethod
    def make(cls, filename="config.json"):
        fields = json.load(open(filename, encoding="utf-8"))
        fields["admin_ids"] = set(fields["admin_ids"])
        return cls(**fields)
