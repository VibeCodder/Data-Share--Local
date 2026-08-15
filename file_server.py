#!/usr/bin/env python3
"""
Simple server for receiving files and text through the browser.
Run: python3 file_server.py [port]
Default port: 8000
Files and pasted text land in the ./uploads folder
"""

import os
import sys
import cgi
import html
import mimetypes
import datetime
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FORM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>transfer://local</title>
<style>
  :root {
    --bg: #0b0d0c;
    --panel: #121615;
    --border: #262c2a;
    --text: #d8ddd9;
    --muted: #6f7a75;
    --amber: #f0a83c;
    --amber-dim: #6b4d1e;
    --amber-glow: rgba(240, 168, 60, 0.15);
  }

  * { box-sizing: border-box; }

  body {
    background: var(--bg);
    background-image:
      radial-gradient(ellipse at top, rgba(240,168,60,0.05), transparent 60%),
      repeating-linear-gradient(0deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 1px, transparent 1px, transparent 2px);
    color: var(--text);
    font-family: 'IBM Plex Mono', 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    min-height: 100vh;
    margin: 0;
    padding: 48px 20px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }

  .term {
    width: 100%;
    max-width: 560px;
  }

  .bar {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding-bottom: 14px;
    margin-bottom: 22px;
    border-bottom: 1px solid var(--border);
  }

  .bar h1 {
    font-size: 15px;
    font-weight: 500;
    letter-spacing: 0.06em;
    margin: 0;
    color: var(--amber);
  }

  .bar h1::after {
    content: '_';
    animation: blink 1.1s steps(1) infinite;
    color: var(--amber);
  }

  @keyframes blink {
    50% { opacity: 0; }
  }

  .status {
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.04em;
  }

  .status::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--amber);
    margin-right: 6px;
    box-shadow: 0 0 6px var(--amber);
  }

  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 22px;
    margin-bottom: 16px;
  }

  .label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 12px;
  }

  .drop {
    border: 1px dashed var(--border);
    border-radius: 3px;
    padding: 28px 16px;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
    transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
    cursor: pointer;
    display: block;
  }

  .drop.drag {
    border-color: var(--amber);
    background: var(--amber-glow);
    color: var(--text);
  }

  .drop input[type=file] {
    display: none;
  }

  .filename {
    margin-top: 10px;
    font-size: 12px;
    color: var(--amber);
    min-height: 16px;
  }

  textarea {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text);
    font-family: inherit;
    font-size: 13px;
    padding: 12px;
    resize: vertical;
    outline: none;
  }

  textarea:focus {
    border-color: var(--amber-dim);
  }

  button {
    margin-top: 14px;
    width: 100%;
    background: transparent;
    border: 1px solid var(--amber-dim);
    color: var(--amber);
    font-family: inherit;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 10px;
    border-radius: 3px;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  button:hover {
    background: var(--amber-glow);
    border-color: var(--amber);
  }

  .msg {
    font-size: 12px;
    color: var(--amber);
    border-left: 2px solid var(--amber-dim);
    padding: 8px 12px;
    margin-top: 4px;
    display: __MSG_DISPLAY__;
  }

  .foot {
    font-size: 11px;
    color: var(--muted);
    text-align: center;
    margin-top: 26px;
    letter-spacing: 0.03em;
  }

  .filelist {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .filelist li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    gap: 12px;
  }

  .filelist li:last-child {
    border-bottom: none;
  }

  .fname {
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }

  .fmeta {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-shrink: 0;
  }

  .filesize {
    color: var(--muted);
    font-size: 11px;
    white-space: nowrap;
    flex-shrink: 0;
    min-width: 42px;
    text-align: right;
  }

  .dl-btn {
    color: var(--amber);
    text-decoration: none;
    border: 1px solid var(--amber-dim);
    border-radius: 3px;
    padding: 4px 10px;
    font-size: 11px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    transition: background 0.15s ease, border-color 0.15s ease;
    white-space: nowrap;
  }

  .dl-btn:hover {
    background: var(--amber-glow);
    border-color: var(--amber);
  }

  .empty {
    color: var(--muted);
    font-size: 12px;
    padding: 4px 0;
  }
</style>
</head>
<body>
<div class="term">

  <div class="bar">
    <h1>transfer</h1>
    <div class="status">online</div>
  </div>

  <div class="panel">
    <div class="label">01 / file</div>
    <form method="POST" enctype="multipart/form-data" action="/" id="fileForm">
      <label class="drop" id="dropZone">
        <input type="file" name="file" id="fileInput">
        <span id="dropText">drag a file here or click to browse</span>
        <div class="filename" id="fileName"></div>
      </label>
      <button type="submit">send file</button>
    </form>
  </div>

  <div class="panel">
    <div class="label">02 / text</div>
    <form method="POST" enctype="multipart/form-data" action="/">
      <textarea name="text" rows="5" placeholder="paste text..."></textarea>
      <button type="submit">send text</button>
    </form>
  </div>

  <div class="panel">
    <div class="label">03 / download</div>
    <ul class="filelist">
__FILE_LIST__
    </ul>
  </div>

  <div class="msg">&gt; __MESSAGE__</div>

  <div class="foot">uploads/ &middot; local network transfer</div>

</div>

<script>
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileName = document.getElementById('fileName');
  const dropText = document.getElementById('dropText');

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      fileName.textContent = fileInput.files[0].name;
      dropText.textContent = 'selected file:';
    }
  });

  ['dragenter', 'dragover'].forEach(evt =>
    dropZone.addEventListener(evt, e => {
      e.preventDefault();
      dropZone.classList.add('drag');
    })
  );

  ['dragleave', 'drop'].forEach(evt =>
    dropZone.addEventListener(evt, e => {
      e.preventDefault();
      dropZone.classList.remove('drag');
    })
  );

  dropZone.addEventListener('drop', e => {
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      fileName.textContent = e.dataTransfer.files[0].name;
      dropText.textContent = 'selected file:';
    }
  });
</script>
</body>
</html>
"""


def human_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def render_file_list():
    entries = []
    for name in os.listdir(UPLOAD_DIR):
        full = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(full):
            entries.append((os.path.getmtime(full), name, os.path.getsize(full)))

    if not entries:
        return '      <li class="empty">no files available yet</li>'

    entries.sort(reverse=True)  # newest first

    rows = []
    for _, name, size in entries:
        safe_name = html.escape(name)
        url_name = urllib.parse.quote(name)
        rows.append(
            f'      <li>'
            f'<span class="fname" title="{safe_name}">{safe_name}</span>'
            f'<span class="fmeta">'
            f'<span class="filesize">{human_size(size)}</span>'
            f'<a class="dl-btn" href="/download/{url_name}" download>download</a>'
            f'</span>'
            f'</li>'
        )
    return "\n".join(rows)


class Handler(BaseHTTPRequestHandler):
    def _send_html(self, message=""):
        page = FORM_HTML.replace("__MESSAGE__", message or "ready")
        page = page.replace("__MSG_DISPLAY__", "block" if message else "none")
        page = page.replace("__FILE_LIST__", render_file_list())
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def _send_download(self, filename):
        # protection against directory traversal (e.g. ../../etc/passwd)
        safe_name = os.path.basename(urllib.parse.unquote(filename))
        full_path = os.path.join(UPLOAD_DIR, safe_name)

        if not os.path.isfile(full_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("File not found.".encode("utf-8"))
            return

        mime_type, _ = mimetypes.guess_type(full_path)
        mime_type = mime_type or "application/octet-stream"
        size = os.path.getsize(full_path)

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(size))
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{safe_name}"',
        )
        self.end_headers()
        with open(full_path, "rb") as f:
            self.wfile.write(f.read())

    def do_GET(self):
        if self.path.startswith("/download/"):
            filename = self.path[len("/download/"):]
            self._send_download(filename)
        else:
            self._send_html()

    def do_POST(self):
        ctype = self.headers.get("Content-Type", "")
        if not ctype.startswith("multipart/form-data"):
            self._send_html("Error: invalid data.")
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
            message = f"File saved: {save_path}"

        elif "text" in form and form["text"].value.strip():
            text_value = form["text"].value
            save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_text.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text_value)
            message = f"Text saved as: {save_path}"

        else:
            message = "Nothing was sent."

        print(message)
        self._send_html(message)

    def log_message(self, format, *args):
        pass  # silence default logging so the console stays readable


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Server running on port {port}. Files land in the '{UPLOAD_DIR}/' folder.")
    print(f"On the local network, access it via: http://YOUR_LOCAL_IP:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.server_close()
