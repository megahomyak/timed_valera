import sqlalchemy
from sqlalchemy.sql import func as sql_functions

import models
import utils
from handlers.base_handler import AdminsCommandHandler, UsersCommandHandler
from handlers.handlers_collector import HandlersCollector

handlers_collector = HandlersCollector()


@handlers_collector.add(r"ответ\s+(.+)")
class Answer(UsersCommandHandler):

    async def handle_message(self, answer_text: str):
        if self.bot.current_question_info is None:
            await self.answer("Квест ещё не начался!")
        else:
            if self.message.peer_id != self.message.chat_id:
                await self.answer("Отвечать можно только в личке!")
            elif (
                self.bot.current_question_info.question.answer_text
                == answer_text
            ):
                user: models.User = self.bot.db_session.query(
                    models.User
                ).get(self.message.from_id)
                if user is None:
                    user = models.User(vk_id=self.message.from_id)
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
        rows_amount = self.bot.db_session.execute(
            sqlalchemy.delete(models.Question).where(
                models.Question.id == self.bot.db_session.query(
                    sql_functions.max(models.Question.id)
                )
            )
        )
        if rows_amount == 0:
            await self.answer("Вопросов нет!")
        else:
            self.bot.db_session.commit()
            await self.answer("Последний вопрос успешно удалён!")


@handlers_collector.add(r"вопросы")
class ListQuestions(AdminsCommandHandler):

    async def handle_message(self) -> None:
        await self.answer("\n".join(
            f"{question.id}. {question.question_text} | {question.answer_text}"
            for question in self.bot.db_session.query(models.Question).all()
        ) or "Вопросов ещё нет!")


@handlers_collector.add(r"добавить\s+(.+?)\s*\|\s*(.+)")
class AddCommand(AdminsCommandHandler):

    async def handle_message(
            self, question_text: str, answer_text: str) -> None:
        question = models.Question(
            question_text=question_text, answer_text=answer_text
        )
        self.bot.db_session.add(question)
        self.bot.db_session.flush()
        attachments = []
        for attachment_from_message in self.message.attachments:
            attachment_type = attachment_from_message.type.name.lower()
            attachment_type_object = getattr(
                attachment_from_message, attachment_type
            )
            attachment_string = (
                f"{attachment_type}{attachment_type_object.owner_id}"
                f"_{attachment_type_object.id}"
            )
            attachments.append(models.Attachment(
                question_id=question.id, attachment_string=attachment_string
            ))
        self.bot.db_session.add_all(attachments)
        self.bot.db_session.commit()
        print(",".join(
            attachment.attachment_string
            for attachment in question.attachments
        ))
        await self.answer(
            f"Новый вопрос (№{question.id}): "
            f"{question.question_text}",
            attachment=",".join(
                attachment.attachment_string
                for attachment in question.attachments
            )
        )
        await self.answer("Вопрос успешно добавлен!")


@handlers_collector.add(r"команды")
@handlers_collector.add(r"помощь")
class Help(AdminsCommandHandler):

    async def handle_message(self) -> None:
        await self.answer(
            "/удалить - удалить последний вопрос\n"
            "/вопросы - получить список вопросов в формате"
            "{айди}. {вопрос} | {ответ}\n"
            "/добавить [текст вопроса] | [текст ответа] - добавить вопрос в "
            "конец, можно прикрепить файлики к сообщению\n"
            "/помощь или /команды - это сообщение\n"
            "\n"
            "ещё есть /ответ [текст ответа], /вопрос и /лидерборд, это уже для "
            "всех"
        )
