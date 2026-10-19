"""OpenAI calls. One structured call per task; returns parsed JSON and token usage."""
import json
import logging
from dataclasses import dataclass

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    PermissionDeniedError,
)

from . import config

log = logging.getLogger("tippingpoint")
_client: OpenAI | None = None


@dataclass
class Usage:
    model: str
    input_tokens: int
    output_tokens: int


class AIError(Exception):
    """An AI call failed. maybe_billed=True when the request may have reached OpenAI."""

    def __init__(self, reason: str, maybe_billed: bool, usage: Usage | None = None):
        super().__init__(reason)
        self.reason = reason
        self.maybe_billed = maybe_billed
        self.usage = usage


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY or None, timeout=config.AI_TIMEOUT_S, max_retries=0)
    return _client


def call(task: str, instructions: str, payload: dict, schema: dict) -> tuple[dict, Usage]:
    model = config.MODELS[task]
    try:
        resp = _get_client().responses.create(
            model=model,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
            text={"format": {"type": "json_schema", "name": f"{task}_result", "schema": schema, "strict": True}},
            reasoning={"effort": config.REASONING_EFFORT},
            max_output_tokens=config.MAX_OUT[task],
            store=False,
        )
    except APITimeoutError as e:  # subclass of APIConnectionError: check first
        raise AIError("timeout", maybe_billed=True) from e
    except (AuthenticationError, PermissionDeniedError) as e:
        raise AIError(f"auth_{e.status_code}", maybe_billed=False) from e
    except APIStatusError as e:
        raise AIError(f"status_{e.status_code}", maybe_billed=e.status_code >= 500) from e
    except APIConnectionError as e:
        raise AIError("connection", maybe_billed=False) from e

    u = getattr(resp, "usage", None)
    usage = Usage(model, getattr(u, "input_tokens", 0) or 0, getattr(u, "output_tokens", 0) or 0)
    log.info("ai task=%s model=%s in=%d out=%d status=%s", task, model, usage.input_tokens, usage.output_tokens, getattr(resp, "status", "?"))

    if getattr(resp, "status", "completed") != "completed":
        raise AIError(f"incomplete", maybe_billed=True, usage=usage)
    try:
        data = json.loads(resp.output_text)
    except (TypeError, ValueError) as e:
        raise AIError("bad_json", maybe_billed=True, usage=usage) from e
    return data, usage
