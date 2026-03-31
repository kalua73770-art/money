"""
Main FastAPI application - Clean UI Version (No model name anywhere on website)
"""

from fastapi import FastAPI, Form, Body, HTTPException
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from typing import Optional
from pydantic import BaseModel
from html import escape

# Import modular components
from converters import KrutiDev_to_Unicode, Unicode_to_KrutiDev
from gemini_client import call_gemini_correct_text

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("krutidev-converter")

app = FastAPI()

# Pydantic model for Word macro
class HindiRequest(BaseModel):
    hindi_text: str = ""
    instruction: str = ""

# Keepalive
SELF_URL = os.getenv("SELF_URL", "https://money-2vpo.onrender.com")
PING_INTERVAL_MIN = int(os.getenv("PING_INTERVAL_MIN", "14"))

scheduler = BackgroundScheduler()

def ping_self():
    try:
        if not SELF_URL:
            return
        r = requests.head(SELF_URL, timeout=10)
        if r.status_code >= 400:
            requests.get(SELF_URL, timeout=10)
    except:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(ping_self, IntervalTrigger(minutes=PING_INTERVAL_MIN), id="keepalive", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)

app.router.lifespan_context = lifespan

@app.get("/health")
def health():
    return {"ok": True}


# ================= UI HOME =================
@app.get("/", response_class=HTMLResponse)
def home():
    html = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>KrutiDev ⇄ Unicode Converter + Ajmat Correct</title>
<style>
body {font-family:Arial,sans-serif;max-width:900px;margin:20px auto;padding:12px;}
textarea {width:100%;box-sizing:border-box;font-family:monospace;font-size:14px;}
.col {display:flex;gap:12px;}
.box {flex:1;padding:12px;border:1px solid #ddd;border-radius:8px;}
label {font-weight:600;display:block;margin-bottom:6px;}
button {padding:8px 14px;margin-top:8px;}
.note {font-size:13px;color:#444;margin-top:8px;}
.instr {font-size:12px;color:#666;}
</style>
</head>
<body>

<h2>KrutiDev ⇄ Unicode + Typo-Corrector & Document Generator</h2>

<div class="col">

<div class="box">
<form method="post" action="/convert-hindi">
<label>Hindi (KrutiDev010):</label>
<textarea name="hindi_text" rows="10"></textarea>

<label>Instruction:</label>
<textarea name="instruction" rows="3"></textarea>

<label><input type="checkbox" name="thinking_mode" value="on"> बेहतर सुधार मोड</label>

<button type="submit">Convert + Correct</button>
</form>
</div>

<div class="box">
<form method="post" action="/convert-english">
<label>English:</label>
<textarea name="english_text" rows="10"></textarea>

<label>Instruction:</label>
<textarea name="instruction" rows="3"></textarea>

<label><input type="checkbox" name="thinking_mode" value="on"> Advanced Mode</label>

<button type="submit">Correct</button>
</form>
</div>

</div>

<hr>

<h3>⚡ Simple Conversion (No AI)</h3>
<form method="post" action="/convert-simple">
<label>Text:</label>
<textarea name="text" rows="6"></textarea>

<label>Conversion Type:</label>
<select name="mode">
<option value="k2u">KrutiDev → Mangal</option>
<option value="u2k">Mangal → KrutiDev</option>
</select>

<button type="submit">Convert Only</button>
</form>

<p>Health: <a href="/health">/health</a></p>

</body>
</html>
"""
    return HTMLResponse(html)


# ================= SIMPLE UI ROUTE =================
@app.post("/convert-simple", response_class=HTMLResponse)
def convert_simple(text: str = Form(...), mode: str = Form(...)):
    try:
        if mode == "k2u":
            result = KrutiDev_to_Unicode(text)
        else:
            result = Unicode_to_KrutiDev(text)

        html = f"""
        <html>
        <body style="font-family:Arial;max-width:800px;margin:auto;padding:20px;">
        <h2>Simple Conversion Result</h2>

        <h3>Input</h3>
        <pre>{escape(text)}</pre>

        <h3>Output</h3>
        <pre id="out">{escape(result)}</pre>

        <button onclick="copy()">Copy</button>

        <script>
        function copy(){{
            navigator.clipboard.writeText(document.getElementById('out').innerText)
            alert("Copied")
        }}
        </script>

        <p><a href="/">Back</a></p>
        </body>
        </html>
        """
        return HTMLResponse(html)

    except Exception as e:
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)


# ================= SIMPLE API ROUTE =================
@app.post("/api/convert-simple")
def api_convert_simple(text: str, mode: str):
    try:
        if mode == "k2u":
            result = KrutiDev_to_Unicode(text)
        elif mode == "u2k":
            result = Unicode_to_KrutiDev(text)
        else:
            raise HTTPException(400, "Invalid mode")

        return {
            "input": text,
            "output": result,
            "mode": mode
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# ================= EXISTING ROUTES (UNCHANGED) =================

@app.post("/convert-hindi", response_class=HTMLResponse)
def convert_hindi(
    hindi_text: str = Form(...),
    instruction: str = Form(""),
    thinking_mode: Optional[str] = Form(None)
):
    try:
        thinking = thinking_mode == "on"

        unicode_text = KrutiDev_to_Unicode(hindi_text)
        corrected_unicode = call_gemini_correct_text(
            unicode_text, language="hi", instruction=instruction, thinking_mode=thinking
        )
        corrected_krutidev = Unicode_to_KrutiDev(corrected_unicode)

        return HTMLResponse(f"<pre>{corrected_unicode}</pre>")

    except Exception as e:
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)


@app.post("/convert-english", response_class=HTMLResponse)
def convert_english(
    english_text: str = Form(...),
    instruction: str = Form(""),
    thinking_mode: Optional[str] = Form(None)
):
    try:
        thinking = thinking_mode == "on"
        corrected = call_gemini_correct_text(
            english_text, language="en", instruction=instruction, thinking_mode=thinking
        )
        return HTMLResponse(f"<pre>{corrected}</pre>")

    except Exception as e:
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)


@app.post("/api/hindi")
def api_hindi(hindi_text: str, instruction: str = ""):
    unicode_text = KrutiDev_to_Unicode(hindi_text)
    corrected_unicode = call_gemini_correct_text(unicode_text, language="hi", instruction=instruction)
    corrected_krutidev = Unicode_to_KrutiDev(corrected_unicode)
    return {
        "input_krutidev": hindi_text,
        "corrected_mangal": corrected_unicode,
        "corrected_krutidev": corrected_krutidev,
    }


@app.post("/api/english")
def api_english(english_text: str, instruction: str = ""):
    corrected = call_gemini_correct_text(english_text, language="en", instruction=instruction)
    return {"corrected": corrected}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
