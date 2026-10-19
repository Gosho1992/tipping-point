"""One-off check: can this key call the configured model with a structured output? Prints usage only."""
from server import ai, config, schemas

data, usage = ai.call(
    "turn",
    "Extract the statement and ask one short question. Set crisis to false.",
    {"LATEST_ANSWER": "I want to be near my family.", "EXISTING_STATEMENTS": []},
    schemas.TURN,
)
print("model:", config.MODELS["turn"])
print("ok, statements:", len(data["statements"]), "| tokens in/out:", usage.input_tokens, usage.output_tokens)
