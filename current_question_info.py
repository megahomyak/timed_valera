import datetime
from dataclasses import dataclass

import models


@dataclass
class CurrentQuestionInfo:
    question: models.Question
    question_date: datetime.datetime
