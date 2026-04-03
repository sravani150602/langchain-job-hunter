import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # --- LLM API Keys ---
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # --- LangSmith (tracing + monitoring for LangChain) ---
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    langchain_tracing_v2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "faang-job-hunter")

    # --- Adzuna (optional - for extra job coverage) ---
    adzuna_app_id: str = os.getenv("ADZUNA_APP_ID", "")
    adzuna_api_key: str = os.getenv("ADZUNA_API_KEY", "")

    # --- LLM Selection ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")

    # --- App ---
    app_name: str = "CareerCopilot AI"
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    job_refresh_interval_minutes: int = 30

    # jobright.ai max jobs per refresh (keep reasonable to not overload)
    jobright_max_jobs: int = int(os.getenv("JOBRIGHT_MAX_JOBS", "80"))

    # --- Legacy sources (still used as backup) ---
    greenhouse_companies: List[str] = [
        "uber", "airbnb", "stripe", "discord", "figma",
        "databricks", "snowflake", "coinbase", "robinhood",
        "lyft", "doordash", "instacart", "brex", "plaid",
        "scale", "anthropic", "openai"
    ]
    lever_companies: List[str] = ["netflix", "reddit", "dropbox", "zendesk"]
    faang_companies: List[str] = [
        "Google", "Meta", "Amazon", "Apple", "Microsoft",
        "Nvidia", "PayPal", "Uber", "Netflix", "Stripe",
        "Airbnb", "Databricks", "Snowflake", "Salesforce", "Adobe"
    ]

    # Target job titles for fresh grads
    target_roles: List[str] = [
        "Software Engineer", "Software Developer",
        "Data Engineer", "Backend Engineer",
        "Frontend Engineer", "Full Stack Engineer",
        "Machine Learning Engineer", "New Grad", "Entry Level"
    ]

    # --- AWS (ignored in local dev) ---
    use_dynamodb: bool = False
    dynamodb_table: str = "job-hunter-jobs"
    aws_region: str = "us-east-1"

    class Config:
        env_file = ".env"
        extra = "ignore"  # silently ignore unknown env vars


settings = Settings()
