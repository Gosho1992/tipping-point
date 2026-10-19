"""Strict JSON shapes the AI must reply in (OpenAI Structured Outputs)."""

TURN = {
    "type": "object",
    "additionalProperties": False,
    "required": ["statements", "themes", "cells", "next_question", "crisis"],
    "properties": {
        "statements": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "title", "text", "quote"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "quote": {"type": "string"},
                },
            },
        },
        "themes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "name", "cites"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "cites": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "cells": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["option", "theme", "score", "cites", "depends_on_others"],
                "properties": {
                    "option": {"type": "string"},
                    "theme": {"type": "string"},
                    "score": {"type": ["integer", "null"]},
                    "cites": {"type": "array", "items": {"type": "string"}},
                    "depends_on_others": {"type": "boolean"},
                },
            },
        },
        "next_question": {"type": "string"},
        "crisis": {"type": "boolean"},
    },
}

VALUES = {
    "type": "object",
    "additionalProperties": False,
    "required": ["values", "crisis"],
    "properties": {
        "values": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "cites"],
                "properties": {
                    "name": {"type": "string"},
                    "cites": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "crisis": {"type": "boolean"},
    },
}

SCORES = {
    "type": "object",
    "additionalProperties": False,
    "required": ["cells", "crisis"],
    "properties": {
        "cells": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["option", "value", "score", "reason", "cites", "depends_on_others"],
                "properties": {
                    "option": {"type": "string"},
                    "value": {"type": "string"},
                    "score": {"type": ["integer", "null"]},
                    "reason": {"type": "string"},
                    "cites": {"type": "array", "items": {"type": "string"}},
                    "depends_on_others": {"type": "boolean"},
                },
            },
        },
        "crisis": {"type": "boolean"},
    },
}

FUTURES = {
    "type": "object",
    "additionalProperties": False,
    "required": ["cards", "crisis"],
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["option", "sentences"],
                "properties": {
                    "option": {"type": "string"},
                    "sentences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["text", "cites"],
                            "properties": {
                                "text": {"type": "string"},
                                "cites": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                },
            },
        },
        "crisis": {"type": "boolean"},
    },
}
