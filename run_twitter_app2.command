#!/bin/bash
# Starts the description server (headless_scrapper) if it isn't running, then the bookmark app.
# Python environments live outside Google Drive, in ~/.local/share/venvs/.

PY_STUFF="/Users/guykindler/My Drive/python stuff"
APP_DIR="$PY_STUFF/twitter bookmark app"
SERVER_DIR="$PY_STUFF/headless_scrapper"
APP_PY="$HOME/.local/share/venvs/twitter-bookmark-app/bin/python"
SERVER_PY="$HOME/.local/share/venvs/headless_scrapper/bin/python"
LOG_DIR="$HOME/Library/Logs/twitter-bookmark-app"
SERVER_URL="http://127.0.0.1:5000/"
mkdir -p "$LOG_DIR"

# Port 5000 is also used by macOS AirPlay Receiver, so check for our own page, not just any answer.
server_up() { curl -s --max-time 2 "$SERVER_URL" | grep -q "Website Describer"; }

if server_up; then
    echo "Description server already running."
else
    echo "Starting description server (log: $LOG_DIR/server.log)..."
    (cd "$SERVER_DIR" && nohup "$SERVER_PY" server.py >> "$LOG_DIR/server.log" 2>&1 &)
    for _ in $(seq 1 20); do server_up && break; sleep 0.5; done
    server_up && echo "Description server is up." || echo "WARNING: server did not start; Tab descriptions won't work. See $LOG_DIR/server.log"
fi

cd "$APP_DIR"
exec "$APP_PY" "twitter app2.py"
