"""Settings read from .env. Every limit and model choice lives here."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
load_dotenv(ROOT / ".env")


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, default))


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MODELS = {
    "turn": os.getenv("MODEL_TURN", "gpt-6-luna"),
    "values": os.getenv("MODEL_VALUES", "gpt-6-luna"),
    "scores": os.getenv("MODEL_SCORES", "gpt-6-luna"),
    "futures": os.getenv("MODEL_FUTURES", "gpt-6-luna"),
}
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "low")
AI_TIMEOUT_S = _f("AI_TIMEOUT_S", 30)

MAX_OUT = {
    "turn": _i("MAX_OUT_TURN", 2000),
    "values": _i("MAX_OUT_VALUES", 800),
    "scores": _i("MAX_OUT_SCORES", 2000),
    "futures": _i("MAX_OUT_FUTURES", 1000),
}

_DEFAULT_PRICES = {"gpt-6-luna": (0.10, 0.50), "gpt-6.1-sol": (2.00, 10.00)}


def price_per_m(model: str) -> tuple[float, float]:
    """(input, output) USD per 1M tokens for a model, from .env or defaults."""
    key = model.upper().replace("-", "_").replace(".", "_")
    d_in, d_out = _DEFAULT_PRICES.get(model, (10.0, 50.0))  # unknown model: assume expensive
    return _f(f"PRICE_IN_PER_M_{key}", d_in), _f(f"PRICE_OUT_PER_M_{key}", d_out)


LIMIT_VISITOR_CALLS = _i("LIMIT_VISITOR_CALLS", 45)
LIMIT_NETWORK_CALLS = _i("LIMIT_NETWORK_CALLS", 90)
LIMIT_GLOBAL_CALLS = _i("LIMIT_GLOBAL_CALLS", 1500)
DAILY_SPEND_CAP_USD = _f("DAILY_SPEND_CAP_USD", 1.00)
IP_HASH_SALT = os.getenv("IP_HASH_SALT", "")

MAX_BODY_BYTES = 64 * 1024

DEALBREAKER_FAIL = _i("DEALBREAKER_FAIL", 3)
TARGET_ANSWERS = _i("TARGET_ANSWERS", 5)
