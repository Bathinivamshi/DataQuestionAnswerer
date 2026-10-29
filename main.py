
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_service import generate_sql
from database import execute_safe_sql, initialize_database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database when the application starts."""
    initialize_database()
    logger.info("Database initialized successfully.")
    yield


app = FastAPI(
    title="Data Question Answerer",
    description=(
        "Ask questions in plain English and receive "
        "answers from a sample sales database."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500,
        description="A question about customers, products, or orders.",
    )


@app.get("/")
def home():
    """Return basic information about the application."""
    return {
        "message": "Welcome to Data Question Answerer!",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Check whether the API is responding."""
    return {"status": "healthy"}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    """Convert a natural-language question into SQL and execute it."""

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        sql = generate_sql(question)

        if sql.strip().upper() == "CANNOT_ANSWER":
            return {
                "question": question,
                "sql": None,
                "results": [],
                "message": (
                    "This question cannot be answered "
                    "using the available database."
                ),
            }

        # Validate and execute the generated SQL safely.
        result = execute_safe_sql(sql)

        return {
            "question": question,
            "sql": result["sql"],
            "results": result["rows"],
            "message": (
                "Query executed successfully."
                if result["rows"]
                else "Query executed successfully, but no rows matched."
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Failed to answer the question.")

        raise HTTPException(
            status_code=502,
            detail=(
                "The question could not be processed. "
                "Check the server terminal for details."
            ),
        ) from exc
