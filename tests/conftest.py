import os
import sys
import tempfile
from pathlib import Path

# Tests use their own usage database and generous caps; tests/test_limits.py tightens them per test.
os.environ["USAGE_DB"] = os.path.join(tempfile.mkdtemp(prefix="tp-usage-"), "usage.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import config  # noqa: E402

config.LIMIT_VISITOR_CALLS = config.LIMIT_NETWORK_CALLS = config.LIMIT_GLOBAL_CALLS = 10**9
config.DAILY_SPEND_CAP_USD = 10**9
