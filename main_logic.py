import asyncio
import datetime
import random
import sys
from typing import Optional

import loguru
import vkbottle.bot
from sqlalchemy.orm import Session

import models
import utils
from config import Config
from current_question_info import CurrentQuestionInfo
from handlers.implementations import handlers_collector


class Bot:

    # noinspection PyShadowingNames
    def __init__(
            self, db_session: Session, config: Config,
            vk_client: vkbottle.Bot):
        self.db_session = db_session
        self.config = config
        vk_client.on.message()(self.handle_new_message)
        self.vk_client = vk_client
        self.question_id = self.config.starting_question_id
        question_date = utils.now()
        if question_date.hour > config.question_hour_in_moscow_timezone:
            question_date += datetime.timedelta(days=1)
        question_date.replace(
            hour=config.question_hour_in_moscow_timezone,
            minute=0,
            second=0,
            microsecond=0
        )
        self.next_question_date = question_date
        self.current_question_info: Optional[CurrentQuestionInfo] = None
        self.commands = handlers_collector

    async def send_to_questions_chat(
            self, message: str, attachment: str = None):
        await self.send_to_user(
            peer_id=self.config.questions_chat_id,
            message=message,
            attachment=attachment
        )

    async def send_to_user(
            self, peer_id: int, message: str, attachment: str = None):
        await self.vk_client.api.messages.send(
            peer_id=peer_id,
            random_id=random.randint(-1_000_000, 1_000_000),
            message=message,
            attachment=attachment
        )

    async def roll_a_question_every_day(self) -> None:
        while True:
            await asyncio.sleep(
                (self.next_question_date - utils.now()).total_seconds()
            )
            question: models.Question = (
                self.db_session.query(models.Question).get(self.question_id)
            )
            if question is None:
                if self.question_id != self.config.starting_question_id:
                    await self.send_to_questions_chat("Квест завершён!")
                return
            else:
                self.current_question_info = CurrentQuestionInfo(
                    question=question,
                    question_date=self.next_question_date
                )
                self.next_question_date += datetime.timedelta(days=1)
                self.question_id += 1
                await self.send_to_questions_chat(
                    f"Новый вопрос (№{question.id}): "
                    f"{question.question_text}",
                    attachment=",".join(
                        attachment.attachment_string
                        for attachment in question.attachments
                    )
                )

    async def handle_new_message(self, message: vkbottle.bot.Message):
        if message.text.startswith("/"):
            text = message.text[1:]
            for regex, handler_type in self.commands:
                if (
                    not handler_type.is_for_admins()
                    or message.from_id in self.config.admin_ids
                ):
                    match = regex.fullmatch(text)
                    if match:
                        handler = handler_type(message, self)
                        await handler.handle_message(*match.groups())
                        break
            else:
                await self.send_to_user(message.peer_id, "Неизвестная команда!")

    async def run(self):
        asyncio.create_task(self.roll_a_question_every_day())
        await self.vk_client.run_polling()


if __name__ == '__main__':
    config = Config.make()
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level="WARNING")
    bot = Bot(
        db_session=models.get_session(),
        config=config,
        vk_client=vkbottle.Bot(token=config.vk_bot_token)
    )
    print("Starting!")
    asyncio.get_event_loop().run_until_complete(bot.run())
