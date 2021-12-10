import random
import typing
from abc import ABC, abstractmethod

import vkbottle.bot

if typing.TYPE_CHECKING:
    from main_logic import Bot


class BaseHandler(ABC):

    def __init__(self, message: vkbottle.bot.Message, bot: "Bot"):
        self.message = message
        self.bot = bot

    async def answer(self, message: str, attachment: str = None):
        await self.message.answer(
            random_id=random.randint(-1_000_000, 1_000_000),
            message=message,
            attachment=attachment
        )

    @staticmethod
    @abstractmethod
    def is_for_admins() -> bool:
        pass

    @abstractmethod
    async def handle_message(self, *args) -> None:
        pass


class AdminsCommandHandler(BaseHandler, ABC):

    @staticmethod
    def is_for_admins() -> bool:
        return True


class UsersCommandHandler(BaseHandler, ABC):

    @staticmethod
    def is_for_admins() -> bool:
        return False
