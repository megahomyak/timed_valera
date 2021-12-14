import asyncio
import datetime
import random
import sys
from typing import Optional, Dict, List

import loguru
import vkbottle.bot
from sqlalchemy import desc
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
        now = utils.now()
        question_date = datetime.datetime.combine(
            date=now,
            time=datetime.time(hour=config.question_hour_in_moscow_timezone),
            tzinfo=utils.MOSCOW_TIMEZONE
        )
        if now > question_date:
            question_date += datetime.timedelta(days=1)
        self.next_question_date = question_date
        self.current_question_info: Optional[CurrentQuestionInfo] = None
        self.commands = handlers_collector
        self.admin_id_to_question_answer: Dict[int, str] = {}

    async def send_to_questions_chat(
            self, message: str, forward_messages: List[int] = None):
        await self.send_to_user(
            peer_id=self.config.questions_chat_id,
            message=message,
            forward_messages=forward_messages
        )

    async def send_to_user(
            self, peer_id: int, message: str,
            forward_messages: List[int] = None):
        await self.vk_client.api.messages.send(
            peer_id=peer_id,
            random_id=random.randint(-1_000_000, 1_000_000),
            message=message,
            forward_messages=forward_messages
        )

    async def get_leaderboard(self) -> Optional[str]:
        users = (
            self.db_session
            .query(models.User)
            .order_by(desc(models.User.vk_id))
            .order_by(desc(models.User.time_spent_on_solutions_in_seconds))
            .all()
        )
        if users:
            users_vk_info = await self.vk_client.api.users.get(
                user_ids=[user.vk_id for user in users]
            )
            return "\n".join(
                f"{user_number}. "
                f"[id{user_from_vk.id}|{user_from_vk.first_name} "
                f"{user_from_vk.last_name}] - {user.score} "
                + utils.decline_word(
                    user.score, (
                        "правильный ответ", "правильных ответа",
                        "правильных ответов"
                    )
                )
                for user_from_vk, (user_number, user) in zip(
                    users_vk_info, enumerate(users, start=1)
                )
            )
        else:
            return None

    async def roll_a_question_every_day(self) -> None:
        while True:
            await asyncio.sleep(
                (self.next_question_date - utils.now()).total_seconds()
            )
            await self.roll_a_question(manual=False)

    async def roll_a_question(self, manual: bool):
        question: models.Question = (
            self.db_session.query(models.Question).get(self.question_id)
        )
        if question is None:
            self.current_question_info = None
            if self.question_id != self.config.starting_question_id:
                await self.send_to_questions_chat(
                    "Квест завершён! Лидерборд:\n"
                    + await self.get_leaderboard()
                )
                return
        else:
            self.current_question_info = CurrentQuestionInfo(
                question=question,
                question_date=self.next_question_date
            )
            self.question_id += 1
            await self.send_to_questions_chat(
                f"Новый вопрос (№{question.id}):",
                forward_messages=question.question_message_id
            )
        if not manual:
            self.next_question_date += datetime.timedelta(days=1)

    def message_is_from_admin(self, message: vkbottle.bot.Message):
        return (
            message.peer_id == message.from_id
            and message.peer_id in self.config.admin_ids
        )

    async def handle_new_message(self, message: vkbottle.bot.Message):
        try:
            question_answer = self.admin_id_to_question_answer.pop(
                message.from_id
            )
        except KeyError:
            if message.text.startswith("/"):
                text = message.text[1:]
                for regex, handler_type in self.commands:
                    if (
                        not handler_type.is_for_admins()
                        or self.message_is_from_admin(message)
                    ):
                        match = regex.fullmatch(text)
                        if match:
                            handler = handler_type(message, self)
                            await handler.handle_message(*match.groups())
                            break
                else:
                    await self.send_to_user(
                        message.peer_id, "Неизвестная команда!"
                    )
        else:
            question = models.Question(
                question_message_id=message.id, answers=[
                    models.Answer(text=answer.strip())
                    for answer in question_answer.split("|")
                ]
            )
            self.db_session.add(question)
            self.db_session.commit()
            await self.send_to_user(
                message.peer_id,
                f"Вопрос успешно добавлен! (ID: {question.id})"
            )

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
