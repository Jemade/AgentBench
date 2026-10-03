import os


def database_url(value):
    """Accept hosted PostgreSQL URLs with the installed psycopg driver."""
    for prefix in ("postgres://", "postgresql://"):
        if value.startswith(prefix):
            return "postgresql+psycopg://" + value[len(prefix):]
    return value


DATABASE_URL = database_url(os.getenv("DATABASE_URL", "sqlite:///./agentbench.db"))
RUNNER = os.getenv("RUNNER", "docker")
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "agentbench-sandbox:1")
ALLOW_TRUSTED_LOCAL = os.getenv("ALLOW_TRUSTED_LOCAL", "false").lower() == "true"
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
PROVIDER_MODEL = os.getenv("PROVIDER_MODEL", "")
INPUT_PRICE = os.getenv("INPUT_PRICE_PER_MILLION", "")
OUTPUT_PRICE = os.getenv("OUTPUT_PRICE_PER_MILLION", "")
SECURE_COOKIE = os.getenv("SECURE_COOKIE", "false").lower() == "true"
LEASE_SECONDS = 180
