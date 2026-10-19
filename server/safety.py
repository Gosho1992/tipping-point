"""Basic crisis check: a phrase list. It will miss some wording; the model's crisis flag is a second check."""
import re

_PHRASES = [
    r"kill(ing|ed)? myself", r"end(ing|ed)? (my|it) (own )?life", r"end(ing)? it all", r"take my (own )?life", r"suicid",
    r"want(s|ed|ing)? to die", r"wish i (was|were) dead", r"better off dead", r"don'?t want to (live|be alive|exist)",
    r"no reason to live", r"self[- ]?harm", r"hurt(ing)? myself", r"cut(ting)? myself",
    r"overdose", r"can'?t go on", r"not safe at home", r"someone is hurting me",
]
_RX = re.compile("|".join(_PHRASES), re.IGNORECASE)


def contains_crisis(texts) -> bool:
    for t in texts:
        if t and _RX.search(str(t).replace("’", "'")):
            return True
    return False
