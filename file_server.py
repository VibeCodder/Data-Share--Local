#!/usr/bin/env python3
"""
Simple server for receiving files and text through the browser.
Run: python3 file_server.py [port]
Default port: 8000
Files and pasted text land in the ./uploads folder
"""

import os,socket,webbrowser
import sys
import cgi
import html
import mimetypes
import datetime
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def get_active_ip():
    # Creating a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connecting to a public IP forces the system to select the correct output card
        # The package is not physically sent
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

UPLOAD_DIR = "uploads"


def ensure_upload_dir():
    """(Re)creates the uploads folder if it's missing, e.g. deleted while the server is running."""
    if not os.path.isdir(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)


ensure_upload_dir()
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

  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }

  ::-webkit-scrollbar-track {
    background: var(--bg);
  }

  ::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
    border: 2px solid var(--bg);
  }

  ::-webkit-scrollbar-thumb:hover {
    background: var(--amber-dim);
  }

  ::-webkit-scrollbar-corner {
    background: var(--bg);
  }

  ::-webkit-resizer {
    background-color: var(--bg);
    background-image:
      linear-gradient(135deg, transparent 0 40%, var(--border) 40% 55%, transparent 55% 100%),
      linear-gradient(135deg, transparent 0 65%, var(--border) 65% 80%, transparent 80% 100%);
    border: none;
  }

  * {
    scrollbar-width: thin;
    scrollbar-color: var(--border) var(--bg);
  }

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

  .progress-wrap {
    margin-top: 14px;
    display: none;
  }

  .progress-wrap.active {
    display: block;
  }

  .progress-item {
    margin-bottom: 10px;
  }

  .progress-item:last-child {
    margin-bottom: 0;
  }

  .progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 5px;
    gap: 10px;
  }

  .progress-label .pname {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }

  .progress-label .ppct {
    color: var(--amber);
    flex-shrink: 0;
  }

  .progress-track {
    width: 100%;
    height: 6px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    width: 0%;
    background: var(--amber);
    box-shadow: 0 0 6px var(--amber-glow);
    transition: width 0.1s linear;
  }

  .progress-fill.done {
    background: #6fae7c;
  }

  .progress-fill.error {
    background: #c05656;
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
    list-style: none;
  }

  .file-row {
    display: flex;
    flex-direction: column;
    padding: 9px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    gap: 10px;
  }

  .file-row:last-child {
    border-bottom: none;
  }

  .file-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
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

  .preview-btn {
    margin-top: 0;
    width: auto;
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    font-family: inherit;
    font-size: 11px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 3px;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    white-space: nowrap;
  }

  .preview-btn:hover {
    color: var(--text);
    border-color: var(--amber-dim);
  }

  .preview-wrap {
    display: none;
  }

  .preview-wrap.open {
    display: block;
  }

  .preview-area {
    width: 100%;
    min-height: 90px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text);
    font-family: inherit;
    font-size: 12px;
    padding: 10px;
    resize: vertical;
    outline: none;
  }

  .copy-btn {
    margin-top: 8px;
    width: auto;
    font-size: 11px;
    padding: 6px 12px;
  }

  .copy-btn.copied {
    color: #6fae7c;
    border-color: #6fae7c;
  }

  .name-input {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text);
    font-family: inherit;
    font-size: 13px;
    padding: 10px 12px;
    outline: none;
    margin-bottom: 10px;
  }

  .name-input:focus {
    border-color: var(--amber-dim);
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
        <input type="file" name="file" id="fileInput" multiple>
        <span id="dropText">drag a file here or click to browse</span>
        <div class="filename" id="fileName"></div>
      </label>
      <button type="submit" id="fileSubmit">send file</button>
      <div class="progress-wrap" id="progressWrap"></div>
    </form>
  </div>

  <div class="panel">
    <div class="label">02 / text</div>
    <form method="POST" enctype="multipart/form-data" action="/">
      <input class="name-input" type="text" name="textname" placeholder="name (optional, e.g. notes)" maxlength="120">
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
  const fileForm = document.getElementById('fileForm');
  const fileSubmit = document.getElementById('fileSubmit');
  const progressWrap = document.getElementById('progressWrap');

  function describeSelection(files) {
    if (!files.length) return '';
    if (files.length === 1) return files[0].name;
    return `${files.length} files selected`;
  }

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      fileName.textContent = describeSelection(fileInput.files);
      dropText.textContent = 'selected:';
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
      fileName.textContent = describeSelection(e.dataTransfer.files);
      dropText.textContent = 'selected:';
    }
  });

  function uploadOne(file) {
    return new Promise((resolve, reject) => {
      const row = document.createElement('div');
      row.className = 'progress-item';
      row.innerHTML = `
        <div class="progress-label">
          <span class="pname"></span>
          <span class="ppct">0%</span>
        </div>
        <div class="progress-track"><div class="progress-fill"></div></div>
      `;
      row.querySelector('.pname').textContent = file.name;
      progressWrap.appendChild(row);

      const pct = row.querySelector('.ppct');
      const fill = row.querySelector('.progress-fill');

      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/', true);

      xhr.upload.addEventListener('progress', e => {
        if (e.lengthComputable) {
          const p = Math.round((e.loaded / e.total) * 100);
          fill.style.width = p + '%';
          pct.textContent = p + '%';
        }
      });

      xhr.addEventListener('load', () => {
        fill.style.width = '100%';
        fill.classList.add('done');
        pct.textContent = 'done';
        resolve();
      });

      xhr.addEventListener('error', () => {
        fill.classList.add('error');
        pct.textContent = 'error';
        reject(new Error('upload failed'));
      });

      const fd = new FormData();
      fd.append('file', file);
      xhr.send(fd);
    });
  }

  fileForm.addEventListener('submit', e => {
    e.preventDefault();
    const files = Array.from(fileInput.files || []);
    if (!files.length) return;

    fileSubmit.disabled = true;
    fileSubmit.textContent = 'sending...';
    progressWrap.innerHTML = '';
    progressWrap.classList.add('active');

    // upload sequentially so each bar fills in order
    files.reduce((chain, file) => {
      return chain.then(() => uploadOne(file).catch(() => {}));
    }, Promise.resolve()).then(() => {
      setTimeout(() => window.location.reload(), 400);
    });
  });

  document.querySelectorAll('[data-toggle-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.toggleTarget);
      if (!target) return;
      const open = target.classList.toggle('open');
      btn.textContent = open ? 'hide' : 'preview';
    });
  });

  document.querySelectorAll('[data-copy-target]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const wrap = document.getElementById(btn.dataset.copyTarget);
      if (!wrap) return;
      const area = wrap.querySelector('.preview-area');
      const text = area ? area.value : '';

      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
        } else {
          area.removeAttribute('readonly');
          area.select();
          document.execCommand('copy');
          area.setAttribute('readonly', 'true');
        }
        const original = btn.textContent;
        btn.textContent = 'copied!';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = original;
          btn.classList.remove('copied');
        }, 1500);
      } catch (err) {
        btn.textContent = 'copy failed';
        setTimeout(() => { btn.textContent = 'copy to clipboard'; }, 1500);
      }
    });
  });
</script>
</body>
</html>
"""


def sanitize_text_name(raw_name):
    """Turns user-provided text into a safe .txt filename fragment."""
    raw_name = os.path.basename((raw_name or "").strip())
    if not raw_name:
        return "text.txt"

    # drop any extension the user typed, we always force .txt
    stem, _ = os.path.splitext(raw_name)
    stem = stem.strip() or "text"

    # keep it filesystem-friendly: letters, digits, space, dash, underscore, dot
    safe_stem = "".join(c if (c.isalnum() or c in " -_.") else "_" for c in stem)
    safe_stem = safe_stem.strip(" ._") or "text"
    safe_stem = safe_stem.replace(" ", "_")

    return f"{safe_stem}.txt"


def human_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


PREVIEW_MAX_CHARS = 200_000  # cap how much text gets embedded in the page


def render_file_list():
    ensure_upload_dir()
    entries = []
    for name in os.listdir(UPLOAD_DIR):
        full = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(full):
            entries.append((os.path.getmtime(full), name, os.path.getsize(full)))

    if not entries:
        return '      <li class="empty">no files available yet</li>'

    entries.sort(reverse=True)  # newest first

    rows = []
    for i, (_, name, size) in enumerate(entries):
        safe_name = html.escape(name)
        url_name = urllib.parse.quote(name)
        full = os.path.join(UPLOAD_DIR, name)
        is_txt = name.lower().endswith(".txt")

        preview_html = ""
        if is_txt:
            preview_id = f"preview-{i}"
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(PREVIEW_MAX_CHARS + 1)
                truncated = len(content) > PREVIEW_MAX_CHARS
                if truncated:
                    content = content[:PREVIEW_MAX_CHARS] + "\n... (truncated)"
            except OSError:
                content = ""

            safe_content = html.escape(content)
            preview_html = (
                f'<div class="preview-wrap open" id="{preview_id}">'
                f'<textarea class="preview-area" readonly>{safe_content}</textarea>'
                f'<button type="button" class="preview-btn copy-btn" data-copy-target="{preview_id}">copy to clipboard</button>'
                f'</div>'
            )

        preview_btn = (
            f'<button type="button" class="preview-btn" data-toggle-target="preview-{i}">hide</button>'
            if is_txt else ""
        )

        rows.append(
            f'      <li class="file-row">'
            f'<div class="file-top">'
            f'<span class="fname" title="{safe_name}">{safe_name}</span>'
            f'<span class="fmeta">'
            f'<span class="filesize">{human_size(size)}</span>'
            f'{preview_btn}'
            f'<a class="dl-btn" href="/download/{url_name}" download>download</a>'
            f'</span>'
            f'</div>'
            f'{preview_html}'
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
        ensure_upload_dir()
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

        ensure_upload_dir()

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
            raw_name = form["textname"].value if "textname" in form else ""
            filename = sanitize_text_name(raw_name)
            save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{filename}")
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
    print(f"On the local network, access it via: http://{get_active_ip()}:{port}")
    webbrowser.open_new_tab(f"http://{get_active_ip()}:{port}")
    try:
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.server_close()
