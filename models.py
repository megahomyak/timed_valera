from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

DeclarativeBase = declarative_base()


class User(DeclarativeBase):
    __tablename__ = "user"

    vk_id = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False)
    last_answered_question_id = Column(Integer, nullable=False)
    time_spent_on_solutions_in_seconds = Column(Integer, nullable=False)


class Question(DeclarativeBase):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    question_message_id = Column(Integer, nullable=False)
    answer_text = Column(String, nullable=False)


def get_session(database_file_name="sqlite:///db.db"):
    engine = create_engine(database_file_name)
    session = Session(engine)
    DeclarativeBase.metadata.create_all(engine)
    return session
