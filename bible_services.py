import os

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from schema import Bible, Book, Chapter

load_dotenv()

BIBLE_API_KEY = os.getenv("BIBLE_API_KEY")


def parse_bible_html_content(api_response_data: dict):
    """
    Parses the HTML content of a Bible chapter from the API response
    and returns the main header and a list of verse texts.

    Args:
        api_response_data (dict): The 'data' part of the API response,
                                  containing the 'content' HTML string.

    Returns:
        tuple: A tuple containing:
               - str: The extracted main header text, or None if not found.
               - list: A list of strings, where each string is the text of a verse.
    """
    header_text = None
    verse_texts = []  # Changed to store just the text
    html_content = api_response_data["content"]
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Extract the header
    header_tag = soup.find('p', class_='mt1')
    if header_tag:
        header_text = header_tag.get_text(strip=True)

    # 2. Extract the verses
    paragraph_tags = soup.find_all('p', class_='p')

    for p_tag in paragraph_tags:
        current_verse_number = None  # Still needed temporarily for parsing logic
        current_verse_text_parts = []
        previous_was_text_like = False

        for element in p_tag.children:
            if element.name == 'span' and 'data-number' in element.attrs:
                # If we encounter a new verse number span, and we have collected
                # text for a previous verse, add it to our list
                if current_verse_number is not None:
                    # Append only text
                    verse_texts.append(
                        "".join(current_verse_text_parts).strip())
                    current_verse_text_parts = []
                    previous_was_text_like = False

                current_verse_number = int(element['data-number'])
                previous_was_text_like = False

            elif element.name == 'span' and 'class' in element.attrs and 'add' in element['class']:
                if current_verse_number is not None:
                    if previous_was_text_like:
                        current_verse_text_parts.append(" ")
                    current_verse_text_parts.append(element.get_text())
                    previous_was_text_like = True

            elif element.name is None:  # This is a NavigableString (raw text)
                text = element.strip()
                if current_verse_number is not None and text:
                    if previous_was_text_like:
                        current_verse_text_parts.append(" ")
                    current_verse_text_parts.append(text)
                    previous_was_text_like = True
            else:
                previous_was_text_like = False

        # After iterating through all elements in a paragraph, add the last verse found
        if current_verse_number is not None and current_verse_text_parts:
            # Append only text
            verse_texts.append("".join(current_verse_text_parts).strip())

    return header_text, verse_texts


class BibleService:

    @staticmethod
    async def _get_books_in_bible(id: str) -> list[Book]:
        url = f"https://api.scripture.api.bible/v1/bibles/{id}/books"

        params = {
            "include-chapters": "true",
        }
        headers = {
            "accept": "application/json",
            "api-key": BIBLE_API_KEY
        }

        # Send request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

        books = response.json()["data"]

        return_list = []
        for book in books:
            chapters = book["chapters"]
            has_intro = False

            if chapters[0]["number"] == "intro":
                has_intro = True

            return_list.append(Book(
                id=book["id"],
                name=book["name"],
                has_intro=has_intro,
                end_chapter=len(chapters) -
                1 if has_intro else len(chapters)
            ))

        return return_list
    # There would be a predefined list of bibles we want to support
    # For now, we will use KJV as the default only bible

    @staticmethod
    async def get_bibles(bible_ids: list[str] = ["de4e12af7f28f599-01", "06125adad2d5898a-01"]):
        url = "https://api.scripture.api.bible/v1/bibles"
        headers = {
            "accept": "application/json",
            "api-key": BIBLE_API_KEY
        }
        params = {
            "language": "eng",
            # ids should be comma separated
            "ids": ",".join(bible_ids),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

        bibles = response.json()["data"]

        return_list = []
        for bible in bibles:
            books = await BibleService._get_books_in_bible(bible["id"])
            return_list.append(
                Bible(
                    id=bible["id"],
                    name=bible["name"],
                    name_local=bible["nameLocal"],
                    abbreviation_local=bible["abbreviationLocal"],
                    books=books
                )
            )
        return return_list

    @staticmethod
    async def _get_a_verse(bible_id: str, verse_id: str) -> str:
        url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{verse_id}"

        params = {
            "content-type": "json",
            "include-notes": "false",
            "include-titles": "true",
            "include-chapter-numbers": "false",
            "include-verse-numbers": "false",
            "include-verse-spans": "false",
            "use-org-id": "false"
        }

        headers = {
            "accept": "application/json",
            "api-key": BIBLE_API_KEY
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

        verse_data = response.json()["data"]
        verse_string = ""
        for content in verse_data["content"]:
            for item in content["items"]:
                verse_string += item.get("text", "").lstrip()

        return verse_string

    @staticmethod
    async def get_chapter_verses(bible_id: str, chapter_id: str) -> list[str]:
        url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/passages/{chapter_id}"
        if "intro" in chapter_id:
            url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{chapter_id}"
        headers = {
            "accept": "application/json",
            "api-key": "2ead05467ed4d6f51dc72685bfd0440e"
        }
        params = {
            "content-type": "html",
            "include-notes": "false",
            "include-titles": "true",
            "include-chapter-numbers": "false",
            "include-verse-numbers": "true",
            "include-verse-spans": "false",
            "use-org-id": "false"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

        parsed_html = parse_bible_html_content(response.json()["data"])
        
        return Chapter(
            header=parsed_html[0],
            verses=parsed_html[1]
        )


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(BibleService.get_chapter_verses(
        "de4e12af7f28f599-01", "GEN.1")))
    # print(asyncio.run(BibleService._get_a_verse("de4e12af7f28f599-01", "GEN.1.31")))
