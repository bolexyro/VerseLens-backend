
from fastapi import FastAPI

from bible_services import BibleService
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# plan
# On page load, the server would send all the books, and the chapters in each
# for a book, you could send end chapter number, and has_intro

# When user selects a book and a chapter, server sends the content of that chapter.


@app.get("/bibles")
async def get_bibles():
    return await BibleService.get_bibles()


# get chapter verses
@app.get("/bibles/{bible_id}/chapters/{chapter_id}")
async def get_chapter_verses(bible_id: str, chapter_id: str):
    return await BibleService.get_chapter_verses(bible_id, chapter_id)

# requeststo third party api
# first get the different bibles you want to support we would start with NLT and kjv
# ​/v1​/bibles​/{bibleId}
# get the books in each of the bibles,
# ​/v1​/bibles​/{bibleId}​/books
# then fetch the chapters in each book
# /v1/bibles/{bibleId}/books/{bookId}/chapters
