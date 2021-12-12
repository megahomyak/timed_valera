from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

DeclarativeBase = declarative_base()


class User(DeclarativeBase):
    __tablename__ = "users"

    vk_id = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False)
    last_answered_question_id = Column(Integer, nullable=False)
    time_spent_on_solutions_in_seconds = Column(Integer, nullable=False)


class Question(DeclarativeBase):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    question_message_id = Column(Integer, nullable=False)

    answers = relationship(
        "Answer", back_populates="question", cascade="all, delete"
    )


class Answer(DeclarativeBase):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    text = Column(String, nullable=False)

    question = relationship("Question", back_populates="answers")


def get_session(database_file_name="sqlite:///db.db"):
    engine = create_engine(database_file_name)
    session = Session(engine)
    DeclarativeBase.metadata.create_all(engine)
    return session
