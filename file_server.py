#!/usr/bin/env python3
"""
Prosty serwer do odbierania plików i tekstu przez przeglądarkę.
Uruchom: python3 file_server.py [port]
Domyślny port: 8000
Pliki i wklejony tekst lądują w folderze ./uploads
"""

import os
import sys
import cgi
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FORM_HTML = """<!DOCTYPE html>
<html lang="pl">
<head><meta charset="utf-8"><title>Wyślij plik / tekst</title></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 40px auto;">
<h2>Wyślij plik lub tekst na serwer</h2>

<h3>Plik</h3>
<form method="POST" enctype="multipart/form-data" action="/">
  <input type="file" name="file">
  <input type="submit" value="Wyślij plik">
</form>

<h3>Tekst</h3>
<form method="POST" enctype="multipart/form-data" action="/">
  <textarea name="text" rows="6" style="width:100%"></textarea><br>
  <input type="submit" value="Wyślij tekst">
</form>

<p style="color:green">{message}</p>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send_html(self, message=""):
        html = FORM_HTML.format(message=message)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_GET(self):
        self._send_html()

    def do_POST(self):
        ctype = self.headers.get("Content-Type", "")
        if not ctype.startswith("multipart/form-data"):
            self._send_html("Błąd: nieprawidłowe dane.")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": ctype},
        )

        message = ""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if "file" in form and form["file"].filename:
            item = form["file"]
            filename = os.path.basename(item.filename)
            save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{filename}")
            with open(save_path, "wb") as f:
                f.write(item.file.read())
            message = f"Zapisano plik: {save_path}"

        elif "text" in form and form["text"].value.strip():
            text_value = form["text"].value
            save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_text.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text_value)
            message = f"Zapisano tekst jako: {save_path}"

        else:
            message = "Nie wysłano nic."

        print(message)
        self._send_html(message)

    def log_message(self, format, *args):
        pass  # wyciszamy domyślne logi, żeby konsola była czytelna


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Serwer działa na porcie {port}. Pliki lądują w folderze '{UPLOAD_DIR}/'.")
    print(f"W sieci lokalnej dostęp przez: http://TWOJE_IP_LOKALNE:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymuję serwer.")
        server.server_close()
