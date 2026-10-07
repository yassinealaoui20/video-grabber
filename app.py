import os, re, tempfile, shutil
from flask import Flask, request, jsonify, send_file, send_from_directory
import yt_dlp

app = Flask(__name__, static_folder="static")
ALLOWED = re.compile(r"^https?://([\w-]+\.)*(youtube\.com|youtu\.be|facebook\.com|fb\.watch|instagram\.com|tiktok\.com)/", re.I)

def check(url):
    return bool(url and ALLOWED.match(url))

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.post("/api/info")
def info():
    url = (request.json or {}).get("url", "").strip()
    if not check(url):
        return jsonify(error="Paste a link from YouTube, Facebook, Instagram or TikTok."), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True}) as y:
            d = y.extract_info(url, download=False)
        return jsonify(title=d.get("title"), thumbnail=d.get("thumbnail"),
                       duration=d.get("duration"), uploader=d.get("uploader"))
    except Exception:
        return jsonify(error="Could not read this link. It may be private or unavailable."), 422

@app.get("/api/download")
def download():
    url = request.args.get("url", "").strip()
    if not check(url):
        return jsonify(error="Unsupported link."), 400
    tmp = tempfile.mkdtemp()
    try:
        opts = {"quiet": True, "noplaylist": True, "merge_output_format": "mp4",
                "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                "outtmpl": os.path.join(tmp, "%(title).80s.%(ext)s")}
        with yt_dlp.YoutubeDL(opts) as y:
            y.download([url])
        f = os.path.join(tmp, os.listdir(tmp)[0])
        resp = send_file(f, as_attachment=True, mimetype="video/mp4")
        resp.call_on_close(lambda: shutil.rmtree(tmp, ignore_errors=True))
        return resp
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        return jsonify(error="Download failed."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
