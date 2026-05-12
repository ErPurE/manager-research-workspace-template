"""
Windows executable entry point for Manager Dashboard.

The launcher keeps the existing browser-based Dashboard model: it starts the
local Flask server, opens the browser, and leaves workspace data outside the
program installation directory.
"""

import os
import socket
import sys
import threading
import time
import webbrowser

from server import APP_VERSION, WORKSPACE_ROOT, app, prepare_runtime


def find_available_port(start=5000, limit=20):
    for port in range(start, start + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No available local port found for Manager Dashboard.")


def open_browser_later(url):
    time.sleep(1.2)
    webbrowser.open(url)


def main():
    prepare_runtime()
    preferred_port = int(os.environ.get("MANAGER_DASHBOARD_PORT", "5000"))
    port = find_available_port(preferred_port)
    os.environ["MANAGER_DASHBOARD_PORT"] = str(port)
    url = f"http://127.0.0.1:{port}"

    print(f"Manager Dashboard {APP_VERSION}")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"URL: {url}")
    print("Close this window to stop the Dashboard.")

    threading.Thread(target=open_browser_later, args=(url,), daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}")
        input("Press Enter to exit...")
        sys.exit(1)
