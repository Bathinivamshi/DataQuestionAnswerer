
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError, ServerError

from database import SCHEMA_DESCRIPTION


# Load API settings from the .env file.
load_dotenv()

DEFAULT_MODEL = "gemini-3.8-flash"


def generate_sql(question: str) -> str:
    """Convert a natural-language question into a SQL SELECT query."""

    api_key = os.getenv("GEMINI_API_KEY")

    if (
        not api_key
        or api_key == "paste_your_actual_gemini_api_key_here"
    ):
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your real API key to .env."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a careful SQLite query generator.

DATABASE SCHEMA:
{SCHEMA_DESCRIPTION}

RULES:
1. Return only one valid SQLite SELECT query.
2. Use only the tables and columns in the schema.
3. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, PRAGMA, or other non-SELECT statements.
4. Do not use Markdown code fences.
5. Do not invent table names or column names.
6. If the question cannot be answered using this schema,
   return exactly: CANNOT_ANSWER
7. Limit the results to 100 rows when appropriate.
8. Do not explain the query; return only SQL.

USER QUESTION:
{question}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            sql = (response.text or "").strip()

            # Remove Markdown fences if the model returns them.
            if sql.startswith("```"):
                lines = sql.splitlines()

                if lines and lines[0].startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                sql = "\n".join(lines).strip()

            return sql

        except ServerError:
            if attempt == 2:
                raise

            wait_seconds = 3 * (attempt + 1)
            print(
                f"Gemini server is temporarily unavailable. "
                f"Retrying in {wait_seconds} seconds..."
            )
            time.sleep(wait_seconds)

        except APIError:
            # Authentication, quota, and other API errors
            # should be reported rather than retried blindly.
            raise

    raise RuntimeError("Gemini could not generate a SQL query.")
