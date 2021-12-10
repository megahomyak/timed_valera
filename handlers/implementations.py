from sqlalchemy import desc

import models
import utils
from handlers.base_handler import AdminsCommandHandler, UsersCommandHandler
from handlers.handlers_collector import HandlersCollector

handlers_collector = HandlersCollector()


@handlers_collector.add(r"ответ\s+(.+)")
class Answer(UsersCommandHandler):

    async def handle_message(self, answer_text: str):
        if self.bot.current_question_info is None:
            await self.answer("Квест сейчас не идёт!")
        elif self.message.peer_id != self.message.from_id:
            await self.answer("Отвечать можно только в личке!")
        elif (
            self.bot.current_question_info.question.answer_text
            == answer_text
        ):
            user: models.User = self.bot.db_session.query(
                models.User
            ).get(self.message.from_id)
            if user is None:
                user = models.User(
                    vk_id=self.message.from_id,
                    score=0,
                    time_spent_on_solutions_in_seconds=0,
                    last_answered_question_id=0
                )
                self.bot.db_session.add(user)
            if user.last_answered_question_id == self.bot.question_id:
                await self.answer("Вы уже отвечали на этот вопрос!")
            else:
                user.last_answered_question_id = self.bot.question_id
                user.score += 1
                user.time_spent_on_solutions_in_seconds += (
                    utils.now() - self.bot.current_question_info.question_date
                ).total_seconds()
                self.bot.db_session.commit()
                await self.answer("Ответ правильный!")
        else:
            await self.answer("Ответ неправильный!")


@handlers_collector.add(r"удалить")
class DeleteAQuestion(AdminsCommandHandler):

    async def handle_message(self) -> None:
        question = (
            self.bot.db_session
            .query(models.Question)
            .order_by(desc(models.Question.id))
            .limit(1)
            .first()
        )
        if question is None:
            await self.answer("Вопросов больше не осталось!")
        elif (
            self.bot.current_question_info is not None
            and question is self.bot.current_question_info.question
        ):
            await self.answer("Невозможно удалить текущий вопрос!")
        else:
            self.bot.db_session.delete(question)
            self.bot.db_session.commit()
            await self.answer("Последний вопрос успешно удалён!")


@handlers_collector.add(r"вопросы")
class ListQuestions(AdminsCommandHandler):

    async def handle_message(self) -> None:
        questions = self.bot.db_session.query(models.Question).all()
        if questions:
            question_messages = await self.bot.vk_client.api.messages.get_by_id(
                message_ids=[
                    question.question_message_id
                    for question in questions
                ]
            )
            await self.answer("\n".join(
                f"{question.id}. "
                f"{question_message.text} | {question.answer_text}"
                for question, question_message in zip(
                    questions, question_messages.items
                )
            ))
        else:
            await self.answer("Вопросов ещё нет!")


@handlers_collector.add(r"вопрос")
class GetCurrentQuestion(UsersCommandHandler):

    async def handle_message(self) -> None:
        if self.bot.current_question_info is None:
            await self.answer("Квест ещё не идёт!")
        else:
            question = self.bot.current_question_info.question
            await self.answer(
                f"Текущий вопрос (№{question.id})",
                forward_messages=[question.question_message_id]
            )


@handlers_collector.add(r"вопрос\s+(\d+)")
class GetQuestionByID(AdminsCommandHandler):

    async def handle_message(self, question_id: str) -> None:
        question_id = int(question_id)
        question = self.bot.db_session.query(models.Question).get(question_id)
        if question is None:
            await self.answer(f"Вопроса с ID {question_id} нет!")
        else:
            await self.answer(
                f"Вопрос с ID {question_id} (ответ: {question.answer_text}):",
                forward_messages=question.question_message_id
            )


@handlers_collector.add(r"добавить\s+(.+)")
class AddCommand(AdminsCommandHandler):

    async def handle_message(self, question_text: str) -> None:
        self.bot.admin_id_to_question_answer[self.message.from_id] = (
            question_text
        )
        await self.answer(
            "Теперь отправьте сообщение вопроса. Оно будет переслано игрокам в "
            "качестве вопроса"
        )


@handlers_collector.add(r"команды")
@handlers_collector.add(r"помощь")
class GetHelp(AdminsCommandHandler):

    async def handle_message(self) -> None:
        await self.answer(
            "/удалить - удалить последний вопрос из списка вопросов\n"
            "/вопросы - получить список вопросов в формате"
            "{айди}. {текст сообщения с вопросом} | {ответ}\n"
            "/вопрос [айди] - получить сообщение с вопросом под некоторым "
            "номером и ответ на него\n"
            "/добавить [текст ответа], затем [текст вопроса] - добавить вопрос "
            "в конец списка, можно прикрепить файлики к сообщению\n"
            "/помощь или /команды - это сообщение\n"
            "\n"
            "ещё есть /ответ [текст ответа], /вопрос (без аргументов!) и "
            "/лидерборд, это уже для всех"
        )


@handlers_collector.add(r"лидерборд")
class GetLeaderboard(UsersCommandHandler):

    async def handle_message(self) -> None:
        users = (
            self.bot.db_session
            .query(models.User)
            .order_by(desc(models.User.vk_id))
            .order_by(desc(models.User.time_spent_on_solutions_in_seconds))
            .all()
        )
        if users:
            users_vk_info = await self.bot.vk_client.api.users.get(
                user_ids=[user.vk_id for user in users]
            )
            await self.answer("\n".join(
                f"{user_number}. "
                f"[id{user_from_vk.id}|{user_from_vk.first_name} "
                f"{user_from_vk.last_name}] - {user.score} правильных ответов"
                for user_from_vk, (user_number, user) in zip(
                    users_vk_info, enumerate(users, start=1)
                )
            ))
        else:
            await self.answer("Пока никто не участвовал в квесте!")
