from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

DeclarativeBase = declarative_base()


class User(DeclarativeBase):
    __tablename__ = "user"

    vk_id = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False, default=0)
    time_spent_on_solutions_in_seconds = (
        Column(Integer, nullable=False, default=0)
    )


class Question(DeclarativeBase):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    question_text = Column(String, nullable=False)
    answer_text = Column(String, nullable=False)

    attachments = relationship("Attachment", back_populates="question")


class Attachment(DeclarativeBase):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    attachment_string = Column(String, nullable=False)

    question = relationship("Question", back_populates="attachments")


def get_session(database_file_name="sqlite:///db.db"):
    engine = create_engine(database_file_name)
    session = Session(engine)
    DeclarativeBase.metadata.create_all(engine)
    return session
