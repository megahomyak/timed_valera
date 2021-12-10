import re
from typing import Type, Iterator, Tuple

from handlers.base_handler import BaseHandler


class HandlersCollector:

    def __init__(self):
        self.regexes_and_handlers = []

    def __iter__(self) -> Iterator[Tuple[re.Pattern, Type[BaseHandler]]]:
        return iter(self.regexes_and_handlers)

    def add(self, regex: str):
        def wrapper(class_: Type[BaseHandler]):
            self.regexes_and_handlers.append(
                (re.compile(regex, re.DOTALL | re.IGNORECASE), class_)
            )
            return class_
        return wrapper
