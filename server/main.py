"""Tipping Point server: serves the page and the AI endpoints. Never logs or stores the person's text."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import json

from . import ai, citations, config, limits, prompts, safety, schemas, security

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("tippingpoint")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

CRISIS = {"crisis": True}


def _err(status: int, code: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code})


app.middleware("http")(security.guard)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    too_long = any("too_long" in e.get("type", "") for e in exc.errors())
    log.info("rejected %s: %s", request.url.path, "too_large" if too_long else "bad_request")
    return _err(413, "too_large") if too_long else _err(422, "bad_request")


# ---- request shapes (also enforce size limits) ----
class StatementIn(BaseModel):
    id: str = Field(max_length=8)
    title: str = Field(max_length=80)
    text: str = Field(max_length=300)


class OptionIn(BaseModel):
    id: str = Field(max_length=2)
    name: str = Field(max_length=80)


class TurnRequest(BaseModel):
    decision: str = Field(min_length=1, max_length=500)
    options: list[OptionIn] = Field(min_length=3, max_length=3)
    asked: list[str] = Field(default_factory=list, max_length=40)
    question: str = Field(max_length=400)
    answer: str = Field(min_length=1, max_length=1500)
    statements: list[StatementIn] = Field(default_factory=list, max_length=40)
    next_number: int = Field(ge=1, le=10000)


FALLBACK_QUESTION = "What would you miss most if you chose differently?"


class ValuesRequest(BaseModel):
    decision: str = Field(min_length=1, max_length=500)
    options: list[str] = Field(min_length=2, max_length=2)
    statements: list[StatementIn] = Field(min_length=1, max_length=40)


class ValueIn(BaseModel):
    id: str = Field(max_length=8)
    name: str = Field(max_length=60)


class ScoresRequest(BaseModel):
    options: list[OptionIn] = Field(min_length=3, max_length=3)
    values: list[ValueIn] = Field(min_length=1, max_length=10)
    statements: list[StatementIn] = Field(min_length=1, max_length=40)


class FuturesRequest(BaseModel):
    options: list[OptionIn] = Field(min_length=3, max_length=3)
    statements: list[StatementIn] = Field(min_length=1, max_length=40)


def _run_ai(request: Request, task: str, instructions: str, payload: dict, schema: dict):
    """Reserve budget, call the AI, record the real cost immediately, then hand back the parsed reply.
    Returns (data, None) or (None, error response). The model's crisis flag stops the flow."""
    model = config.MODELS[task]
    prompt_chars = len(instructions) + len(json.dumps(payload, ensure_ascii=False))
    try:
        res = limits.reserve(limits.visitor_key(request.headers.get("x-visitor-id")),
                             limits.network_key(request.client.host if request.client else None),
                             model, prompt_chars, config.MAX_OUT[task])
    except limits.LimitError as e:
        log.info("%s: %s", task, e.code)
        return None, _err(429, e.code)
    try:
        data, usage = ai.call(task, instructions, payload, schema)
    except ai.AIError as e:
        spent = limits.settle(res, e.usage, keep=e.maybe_billed)
        log.warning("%s: ai failed (%s) cost_usd=%.6f", task, e.reason, spent)
        return None, _err(502, "ai_failed")
    spent = limits.settle(res, usage, keep=True)
    log.info("%s: cost_usd=%.6f", task, spent)
    if data.get("crisis"):
        log.info("%s: model crisis flag", task)
        return None, JSONResponse(content=CRISIS)
    return data, None


@app.get("/api/config")
def settings():
    return {"dealbreakerFail": config.DEALBREAKER_FAIL, "targetAnswers": config.TARGET_ANSWERS}


@app.post("/api/turn")
def turn(req: TurnRequest, request: Request):
    if any(len(q) > 400 for q in req.asked):
        return _err(413, "too_large")
    texts = [req.decision, *[o.name for o in req.options], req.answer] + [t for s in req.statements for t in (s.title, s.text)]
    if safety.contains_crisis(texts):
        log.info("turn: crisis phrase")
        return CRISIS
    payload = {
        "DECISION": req.decision,
        "OPTIONS": [o.model_dump() for o in req.options],
        "STATEMENTS": [s.model_dump() for s in req.statements],
        "ASKED_QUESTIONS": req.asked + [req.question],
        "CURRENT_QUESTION": req.question,
        "LATEST_ANSWER": req.answer,
    }
    data, err = _run_ai(request, "turn", prompts.TURN, payload, schemas.TURN)
    if err:
        return err
    new, mapping, mismatched = citations.renumber_new(data.get("statements"), req.answer, req.next_number)
    valid = {s.id for s in req.statements} | {s["id"] for s in new}
    themes, t_removed = citations.validate_themes(data.get("themes"), valid, mapping)
    raw_cells = [
        {**c, "value": c.get("theme"), "cites": citations.map_cites(c.get("cites"), mapping)}
        for c in (data.get("cells") or [])
    ]
    cells, c_changed = citations.validate_cells(raw_cells, [o.id for o in req.options], [t["id"] for t in themes], valid)
    for c in cells:
        c.pop("reason", None)
    log.info("turn: new=%d quote_mismatch=%d themes=%d themes_removed=%d cells_converted_or_missing=%d",
             len(new), mismatched, len(themes), t_removed, c_changed)
    question = (data.get("next_question") or "").strip()[:400] or FALLBACK_QUESTION
    return {"statements": new, "themes": themes, "cells": cells, "next_question": question, "crisis": False}


@app.post("/api/values")
def values(req: ValuesRequest, request: Request):
    if any(len(o) > 80 for o in req.options):
        return _err(413, "too_large")
    texts = [req.decision, *req.options] + [t for s in req.statements for t in (s.title, s.text)]
    if safety.contains_crisis(texts):
        log.info("values: crisis phrase")
        return CRISIS
    payload = {
        "DECISION": req.decision,
        "OPTIONS": req.options + ["Wait / neither"],
        "STATEMENTS": [{"id": s.id, "title": s.title, "text": s.text} for s in req.statements],
    }
    data, err = _run_ai(request, "values", prompts.VALUES, payload, schemas.VALUES)
    if err:
        return err
    vals, removed = citations.validate_values(data.get("values"), {s.id for s in req.statements})
    log.info("values: kept=%d removed=%d", len(vals), removed)
    return {"values": vals, "crisis": False}


@app.post("/api/scores")
def scores(req: ScoresRequest, request: Request):
    texts = [o.name for o in req.options] + [v.name for v in req.values] + [t for s in req.statements for t in (s.title, s.text)]
    if safety.contains_crisis(texts):
        log.info("scores: crisis phrase")
        return CRISIS
    payload = {
        "OPTIONS": [o.model_dump() for o in req.options],
        "VALUES": [v.model_dump() for v in req.values],
        "STATEMENTS": [s.model_dump() for s in req.statements],
    }
    data, err = _run_ai(request, "scores", prompts.SCORES, payload, schemas.SCORES)
    if err:
        return err
    cells, changed = citations.validate_cells(
        data.get("cells"), [o.id for o in req.options], [v.id for v in req.values], {s.id for s in req.statements}
    )
    log.info("scores: cells=%d converted_or_missing=%d", len(cells), changed)
    return {"cells": cells, "crisis": False}


@app.post("/api/futures")
def futures(req: FuturesRequest, request: Request):
    texts = [o.name for o in req.options] + [t for s in req.statements for t in (s.title, s.text)]
    if safety.contains_crisis(texts):
        log.info("futures: crisis phrase")
        return CRISIS
    payload = {"OPTIONS": [o.model_dump() for o in req.options], "STATEMENTS": [s.model_dump() for s in req.statements]}
    data, err = _run_ai(request, "futures", prompts.FUTURES, payload, schemas.FUTURES)
    if err:
        return err
    cards, removed = citations.validate_futures(data.get("cards"), [o.id for o in req.options], {s.id for s in req.statements})
    log.info("futures: sentences=%d removed=%d", sum(len(c["sentences"]) for c in cards), removed)
    return {"cards": cards, "crisis": False}


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1500)
    language: str = Field(min_length=1, max_length=80)


TRANSLATION_PROMPT = """Translate the user's transcript into natural English.
Preserve the meaning, tone, uncertainty, and first-person perspective. Do not summarize,
add advice, answer the content, or remove sensitive details. Return only the English
translation in translated_text. Set crisis true if the source expresses suicidal thoughts,
wanting to harm themselves, being in danger, or serious distress; otherwise false."""


TRANSLATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["translated_text", "crisis"],
    "properties": {
        "translated_text": {"type": "string"},
        "crisis": {"type": "boolean"},
    },
}


@app.post("/api/translate")
def translate(req: TranslationRequest, request: Request):
    """Translate reviewed speech text while using the existing model and spend reservation."""
    if safety.contains_crisis([req.text]):
        log.info("translate: crisis phrase")
        return CRISIS
    payload = {"SOURCE_LANGUAGE": req.language, "TRANSCRIPT": req.text}
    data, err = _run_ai(request, "turn", TRANSLATION_PROMPT, payload, TRANSLATION_SCHEMA)
    if err:
        return err
    translated_text = (data.get("translated_text") or "").strip()[:1500]
    if not translated_text:
        return _err(502, "ai_failed")
    if data.get("crisis") or safety.contains_crisis([translated_text]):
        return CRISIS
    return {"translated_text": translated_text, "crisis": False}


app.mount("/", StaticFiles(directory=config.WEB_DIR, html=True), name="web")
