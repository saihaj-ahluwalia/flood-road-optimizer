"""
AquaRoute AI - Local Zero-Config HTTP Server
Serves the web dashboard locally on http://localhost:8000
"""

import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 8000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local data fetching
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

def run_server():
    # Change working directory to project root or web folder
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)

    handler = CustomHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/web/index.html"
        print("=" * 60)
        print("🌊 AquaRoute AI - Local Web Command Center")
        print("=" * 60)
        print(f"🚀 Serving at: {url}")
        print("Press Ctrl+C to stop the server.\n")

        # Open in default browser automatically
        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
