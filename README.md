
# Data Question Answerer

An AI-powered application that converts natural-language questions into SQL queries and retrieves answers from a sample sales database.

## Features

- Ask database questions in plain English.
- Use Google Gemini to generate SQL queries.
- Validate generated SQL before execution.
- Execute read-only queries against SQLite.
- Return structured JSON responses through FastAPI.
- Explore and test endpoints using Swagger UI.
- Restrict query results to a maximum of 100 rows.

## Tech Stack

- Python
- Google Gemini API
- FastAPI
- SQLite
- SQLGlot
- Pydantic

## Project Structure

```text
data-question-answerer/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── database.py
├── ai_service.py
├── main.py
└── README.md
```

## Prerequisites

- Python 3.10 or newer
- A Google Gemini API key
- Visual Studio Code (recommended)

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd data-question-answerer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

If you use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

Use a model ID supported by your Gemini API account. Never commit your API key to GitHub.

### 5. Start the application

```bash
uvicorn main:app --reload
```

### 6. Open Swagger UI

Visit:

http://127.0.0.1:8000/docs

## Example Questions

- Which products cost more than 1000?
- How many customers are in Hyderabad?
- Show all delivered orders.
- What is the average product price?
- Which customers placed orders?
- How many orders are pending?

## API Endpoint

`POST /ask`

Example request:

```json
{
  "question": "Which products cost more than 1000?"
}
```

Example response:

```json
{
  "question": "Which products cost more than 1000?",
  "sql": "SELECT product_name, price FROM products WHERE price > 1000 LIMIT 100",
  "results": [
    {
      "product_name": "Laptop",
      "price": 55000.0
    },
    {
      "product_name": "Headphones",
      "price": 2000.0
    },
    {
      "product_name": "Keyboard",
      "price": 1500.0
    }
  ],
  "message": "Query executed successfully."
}
```

The exact generated SQL formatting may differ.

## Security Notes

- Keep API keys in environment variables.
- Validate generated SQL before executing it.
- Restrict database access to approved tables.
- Use a row limit to reduce oversized responses.
- Review and test all generated queries before production use.

This project is an educational prototype. Production deployments require additional authentication, rate limiting, monitoring, and security testing.

## Future Improvements

- Add a React frontend.
- Display results in interactive charts.
- Support CSV uploads.
- Add query history.
- Deploy the API to a cloud platform.

## Author

Bathini Vamshi

Built as a portfolio project to demonstrate Python, SQL, API development, and generative AI integration.
