
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

Import modular components

from converters import KrutiDev_to_Unicode, Unicode_to_KrutiDev
from gemini_client import call_gemini_correct_text

Logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("krutidev-converter")

app = FastAPI()

Pydantic model for Word macro

class HindiRequest(BaseModel):
hindi_text: str = ""
instruction: str = ""

Keepalive

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
<textarea name="hindi_text" rows="10" placeholder="KrutiDev text..."></textarea>  
<label class="instr">AI Instructions (optional):</label>  
<textarea name="instruction" rows="3" placeholder="उदाहरण: सुधार के साथ जमीन विक्रीनामा (नॉन-सीएनटी) भी बना दें..."></textarea>  
<label><input type="checkbox" name="thinking_mode" value="on"> बेहतर सुधार मोड</label>  
<div class="note">KrutiDev में लिखा हुआ text यहाँ डालें। निर्देश में AI को बताएं कि क्या अतिरिक्त करना है।<br>  
<b>बेहतर सुधार मोड चेक करें (खासकर लंबे डॉक्यूमेंट के लिए)</b></div>  
<button type="submit">Convert + Correct/Generate</button>  
</form>  
</div>  <div class="box">  
<form method="post" action="/convert-english">  
<label>English:</label>  
<textarea name="english_text" rows="10" placeholder="English text..."></textarea>  
<label class="instr">AI Instructions (optional):</label>  
<textarea name="instruction" rows="3" placeholder="Example: Correct and also generate full affidavit..."></textarea>  
<label><input type="checkbox" name="thinking_mode" value="on"> Advanced Correction Mode</label>  
<div class="note">English text directly भेजा जाएगा।<br>  
<b>Advanced mode चेक करें बेहतर रिजल्ट के लिए</b></div>  
<button type="submit">Correct/Generate</button>  
</form>  
</div>  
</div>  <p style="margin-top:14px;">Health: <a href="/health">/health</a> | Ping: <a href="/ping">/ping</a></p>  
<hr/>  
<small>Pure Python KrutiDev engine • Format files in Format folder</small>  
</body>  
</html>  
"""  
    return HTMLResponse(html)  @app.post("/convert-hindi", response_class=HTMLResponse)
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

    escaped_krutidev = escape(corrected_krutidev)  

    html = f"""

<html>  
<head>  
<meta charset="utf-8">  
<title>Hindi Result</title>  
<style>  
body {{font-family:Arial,sans-serif;max-width:900px;margin:24px auto;padding:12px;}}  
pre {{font-family:monospace;font-size:14px;border:1px solid #ddd;padding:10px;border-radius:4px;}}  
.note {{font-size:13px;color:#444;margin-top:8px;}}  
</style>  
</head>  
<body>  
<h2>Hindi Correction/Generation Result</h2>  
<h3>Input KrutiDev</h3>  
<pre id="input_krutidev">{hindi_text}</pre>  
<h3>Instruction</h3>  
<pre>{instruction}</pre>  
<h3>Corrected/Generated Mangal (Unicode)</h3>  
<pre id="corrected_mangal">{corrected_unicode}</pre>  
<button onclick="copyToClipboard('corrected_mangal')">Copy Mangal</button>  
<h3>Corrected/Generated KrutiDev</h3>  
<pre id="corrected_krutidev">{escaped_krutidev}</pre>  
<button onclick="copyToClipboard('corrected_krutidev')">Copy KrutiDev</button>  
<div class="note">KrutiDev font लगाकर देखें। Mangal सामान्य Unicode देवनागरी है।</div>  
<p><a href="/">Back</a></p>  
<script>  
function copyToClipboard(id) {{  
  var text = document.getElementById(id).innerText;  
  navigator.clipboard.writeText(text).then(()=>alert('Copied!'));  
}}  
</script>  
</body>  
</html>  
"""  
        return HTMLResponse(html)  
    except Exception as e:  
        logger.error(f"convert_hindi error: {e}", exc_info=True)  
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)  @app.post("/convert-english", response_class=HTMLResponse)
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

html = f"""

<html>  
<head><meta charset="utf-8"><title>English Result</title>  
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:24px auto;padding:12px;}} pre{{font-family:monospace;font-size:14px;border:1px solid #ddd;padding:10px;border-radius:4px;}}</style>  
</head>  
<body>  
<h2>English Correction/Generation Result</h2>  
<h3>Input</h3><pre id="input">{english_text}</pre>  
<h3>Instruction</h3><pre>{instruction}</pre>  
<h3>Corrected/Generated</h3><pre id="corrected">{corrected}</pre>  
<button onclick="copyToClipboard('corrected')">Copy</button>  
<p><a href="/">Back</a></p>  
<script>function copyToClipboard(id){{navigator.clipboard.writeText(document.getElementById(id).innerText).then(()=>alert('Copied!'));}}</script>  
</body>  
</html>  
"""  
        return HTMLResponse(html)  
    except Exception as e:  
        logger.error(f"convert_english error: {e}", exc_info=True)  
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)  API routes (Word macro ke liye unchanged)

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

@app.post("/api/word-macro-hindi")
def word_macro_hindi(json_body: HindiRequest = Body(...)):
text = (json_body.hindi_text or "").strip()
instr = (json_body.instruction or "").strip()
if not text:
raise HTTPException(400, "Missing hindi_text")
unicode_text = KrutiDev_to_Unicode(text)
corrected_unicode = call_gemini_correct_text(unicode_text, language="hi", instruction=instr)
corrected_krutidev = Unicode_to_KrutiDev(corrected_unicode)
return {
"input_krutidev": text,
"corrected_mangal": corrected_unicode,
"corrected_krutidev": corrected_krutidev,
}

@app.post("/api/english")
def api_english(english_text: str, instruction: str = ""):
corrected = call_gemini_correct_text(english_text, language="en", instruction=instruction)
return {"corrected": corrected}

if name == "main":
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
