from typing import Annotated

from pydantic import BaseModel


class Book(BaseModel):
    id: str
    name: str
    has_intro: bool
    end_chapter: int


class Bible(BaseModel):
    id: str
    name: str
    name_local: str
    abbreviation_local: str
    books: list[Book]


class Chapter(BaseModel):
    header: str | None
    verses: list[str]
