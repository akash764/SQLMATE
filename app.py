from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

load_dotenv() # Load environment variables from .env file

app = FastAPI()

# Allow frontend from localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Create engine from user's connection details
def create_dynamic_engine(conn):
    try:
        db_url = (
            f"mysql+pymysql://{conn['user']}:{conn['password']}"
            f"@{conn['host']}:{conn['port']}/{conn['database']}"
        )
        return create_engine(db_url)
    except Exception as e:
        raise ValueError(f"Invalid connection: {e}")

@app.post("/query")
async def query_db(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    conn_info = body.get("connection", {})

    if not prompt or not conn_info:
        return {"error": "Prompt or DB connection details missing."}

    try:
        print(f"Received prompt: {prompt}")
        engine = create_dynamic_engine(conn_info)
        print("Database engine created.")

        # Ask Gemini to extract table names
        table_names_resp = model.generate_content(
            f"Extract table names from the user's prompt. If no explicit table names are mentioned, infer likely table names from nouns or context (e.g., 'users' from 'list all users'). Return them as a comma-separated list, with no additional explanation.\nPrompt: {prompt}"
        )
        print(f"Table names response: {table_names_resp.text}")
        tables = [t.strip() for t in table_names_resp.text.split(",")]

        # Validate table names
        tables = [t for t in tables if t and not t.lower().startswith("there are no table names")]

        if not tables:
            print("No valid table names extracted from the prompt.")
            # Instead of error, proceed with empty schema to allow SQL generation
            schema_parts = []
        else:
            # Get schema from MySQL
            schema_parts = []
            with engine.begin() as conn:
                for table in tables:
                    try:
                        rows = conn.execute(text(f"DESCRIBE {table}")).fetchall()
                        columns = [f"{row[0]} {row[1]}" for row in rows]
                        schema_parts.append(f"{table}({', '.join(columns)})")
                    except Exception as e:
                        print(f"Schema error for '{table}': {e}")
                        return {"error": f"Schema error for '{table}': {e}"}

        schema = "\n".join(schema_parts)
        print(f"Schema: {schema}")

        # Ask Gemini to generate SQL using schema
        system_prompt = f"""You are a MySQL expert.
Use the schema below to write a valid SQL query for the user's prompt.

{schema}

Return only the SQL query, nothing else.
"""

        sql_response = model.generate_content(
            f"{system_prompt}\nUser's prompt: {prompt}"
        )
        print(f"SQL response: {sql_response.text}")

        sql = sql_response.text.strip()

        # Clean SQL from markdown or code block formatting
        match = re.search(r'```(?:sql)?\s*(.*?)\s*```', sql, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
        else:
            # Fallback: remove leading/trailing ```
            sql = sql.strip('`').strip()

        # Execute the SQL query
        with engine.begin() as conn:
            result = conn.execute(text(sql))
            if sql.lower().startswith("select"):
                rows = [dict(row._mapping) for row in result]
                print(f"Query returned {len(rows)} rows.")
                return {"sql": sql, "data": rows}
            else:
                print(f"Query affected {result.rowcount} rows.")
                return {"sql": sql, "message": f"{result.rowcount} rows affected."}

    except Exception as e:
        print(f"Server error: {e}")
        return {"error": f"Server error: {e}"}
