"""One-click launcher for Tipping Point.

Asks for an OpenAI API key the first time (saved only in .env on this computer),
then starts the app and opens it in your browser. Run it through start.bat
(Windows) or start.sh (macOS/Linux), which set up Python packages first.
"""
import secrets
import shutil
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"


def ensure_env() -> None:
    if not ENV.exists():
        shutil.copy(ROOT / ".env.example", ENV)
    lines = ENV.read_text(encoding="utf-8").splitlines()
    changed = False
    has_key = False
    for i, line in enumerate(lines):
        if line.startswith("IP_HASH_SALT=") and "change-me" in line:
            lines[i] = "IP_HASH_SALT=" + secrets.token_hex(16)
            changed = True
        if line.startswith("OPENAI_API_KEY="):
            has_key = True
            if not line.split("=", 1)[1].strip():
                lines[i] = "OPENAI_API_KEY=" + ask_key()
                changed = True
    if not has_key:
        lines.append("OPENAI_API_KEY=" + ask_key())
        changed = True
    if changed:
        ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("Saved in .env on this computer only.\n")


def ask_key() -> str:
    print("\nTipping Point needs an OpenAI API key (get one at https://platform.openai.com/api-keys).")
    while True:
        key = input("Paste your key and press Enter: ").strip().strip('"').strip("'")
        if len(key) > 20 and " " not in key:
            return key
        print("That doesn't look like an API key. Please try again.")


def free_port(start: int = 8000) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit("No free port found between 8000 and 8049.")


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Tipping Point needs Python 3.10 or newer.")
    ensure_env()
    port = free_port()
    url = f"http://127.0.0.1:{port}"

    def open_browser() -> None:
        time.sleep(2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    print(f"Tipping Point is running at {url}")
    print("Keep this window open while you use it. Close it (or press Ctrl+C) to stop.\n")

    import uvicorn

    uvicorn.run("server.main:app", host="127.0.0.1", port=port, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
