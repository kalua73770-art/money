# File: app.py
"""
Main FastAPI application.
Imports and uses converters, format_loader, and gemini_client.
Handles routes, keepalive, and HTML responses.
"""

from fastapi import FastAPI, Form, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from subprocess import run, PIPE
from contextlib import asynccontextmanager
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import tempfile
import re
import json
from typing import Optional
from pydantic import BaseModel

# Import modular components
from converters import KrutiDev_to_Unicode, Unicode_to_KrutiDev
from gemini_client import call_gemini_correct_text

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("krutidev-converter")

app = FastAPI()

# Pydantic model for JSON requests (Word macro only, new route)
class HindiRequest(BaseModel):
    hindi_text: str = ""
    instruction: str = ""

# Keepalive config
SELF_URL = os.getenv("SELF_URL", "https://money-fgtr.onrender.com")
PING_INTERVAL_MIN = int(os.getenv("PING_INTERVAL_MIN", "14"))

# Keepalive scheduler
scheduler = BackgroundScheduler()

def ping_self():
    try:
        if not SELF_URL:
            return
        r = requests.head(SELF_URL, timeout=10)
        if r.status_code >= 400:
            requests.get(SELF_URL, timeout=10)
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        scheduler.add_job(ping_self, IntervalTrigger(minutes=PING_INTERVAL_MIN),
                          id="keepalive", replace_existing=True)
        scheduler.start()
        yield
        scheduler.shutdown(wait=False)
    except Exception as e:
        logger.error(f"Lifespan error: {str(e)}")

app.router.lifespan_context = lifespan

# Routes
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home():
    html = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>KrutiDev ⇄ Unicode Converter + Ajmat Correct</title>
<style>
body {{ font-family: Arial, sans-serif; max-width:900px; margin:20px auto; padding:12px; }}
textarea {{ width:100%; box-sizing:border-box; font-family:monospace; font-size:14px; }}
.col {{ display:flex; gap:12px; }}
.box {{ flex:1; padding:12px; border:1px solid #ddd; border-radius:8px; }}
label {{ font-weight:600; display:block; margin-bottom:6px; }}
button {{ padding:8px 14px; margin-top:8px; }}
.note {{ font-size:13px; color:#444; margin-top:8px; }}
.instr {{ font-size:12px; color:#666; }}
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
<div class="note">KrutiDev में लिखा हुआ text यहाँ डालें। निर्देश में AI को बताएं कि क्या अतिरिक्त करना है।</div>
<button type="submit">Convert + Correct/Generate</button>
</form>
</div>
<div class="box">
<form method="post" action="/convert-english">
<label>English:</label>
<textarea name="english_text" rows="10" placeholder="English text..."></textarea>
<label class="instr">AI Instructions (optional):</label>
<textarea name="instruction" rows="3" placeholder="Example: Correct and also generate full affidavit for this person..."></textarea>
<div class="note">English text directly Gemini को भेजा जाएगा। निर्देश में affidavit आदि जेनरेट करने को कहें।</div>
<button type="submit">Correct/Generate</button>
</form>
</div>
</div>
<p style="margin-top:14px;">Health: <a href="/health">/health</a> | Ping: <a href="/ping">/ping</a></p>
<hr/>
<small>Pure Python KrutiDev engine • No TECkit/txtconv required • Set GEMINI_API_KEY in env • Format files in Format folder</small>
</body>
</html>
"""
    return HTMLResponse(html)

@app.post("/convert-hindi", response_class=HTMLResponse)
def convert_hindi(hindi_text: str = Form(...), instruction: str = Form("")):
    try:
        logger.info("Starting convert_hindi")
        logger.info("Calling KrutiDev_to_Unicode")
        unicode_text = KrutiDev_to_Unicode(hindi_text)
        logger.info(f"Python converter done, unicode len: {len(unicode_text)}")

        logger.info("Calling Gemini correct/generate")
        corrected_unicode = call_gemini_correct_text(unicode_text, language="hi", instruction=instruction)
        logger.info(f"Gemini corrected/generated, len: {len(corrected_unicode)}")

        logger.info("Calling Unicode_to_KrutiDev")
        corrected_krutidev = Unicode_to_KrutiDev(corrected_unicode)
        logger.info(f"Back to Kruti, len: {len(corrected_krutidev)}")

        html = f"""  
        <html>  
        <head>  
          <meta charset="utf-8">  
          <title>Hindi Result</title>  
          <style>  
            body {{ font-family: Arial, sans-serif; max-width:900px; margin:24px auto; padding:12px; }}  
            pre {{ font-family: monospace; font-size: 14px; border: 1px solid #ddd; padding: 10px; border-radius: 4px; }}  
            .note {{ font-size: 13px; color: #444; margin-top: 8px; }}  
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
          <button onclick="copyToClipboard('corrected_mangal')">Copy Corrected Mangal to Clipboard</button>  
          <h3>Corrected/Generated KrutiDev</h3>  
          <pre id="corrected_krutidev">{corrected_krutidev}</pre>  
          <button onclick="copyToClipboard('corrected_krutidev')">Copy Corrected KrutiDev to Clipboard</button>  
          <div class="note">Note: To view KrutiDev text correctly, ensure the KrutiDev 010 font is applied in your text editor. Mangal (Unicode) is standard Devanagari. Generated documents follow the format from Format folder.</div>  
          <p><a href="/">Back</a></p>  
          <script>  
            function copyToClipboard(id) {{  
              var text = document.getElementById(id).innerText;  
              navigator.clipboard.writeText(text).then(function() {{  
                alert('Copied to clipboard!');  
              }}, function(err) {{  
                alert('Could not copy text: ' + err);  
              }});  
            }}  
          </script>  
        </body>  
        </html>  
        """  
        return HTMLResponse(html)  
    except Exception as e:  
        logger.error(f"convert_hindi error: {str(e)}", exc_info=True)  
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)

@app.post("/convert-english", response_class=HTMLResponse)
def convert_english(english_text: str = Form(...), instruction: str = Form("")):
    try:
        corrected = call_gemini_correct_text(english_text, language="en", instruction=instruction)
        html = f"""
<html>
<head>
<meta charset="utf-8">
<title>English Result</title>
<style>
body {{ font-family: Arial, sans-serif; max-width:900px; margin:24px auto; padding:12px; }}
pre {{ font-family: monospace; font-size: 14px; border: 1px solid #ddd; padding: 10px; border-radius: 4px; }}
</style>
</head>
<body>
<h2>English Correction/Generation Result</h2>
<h3>Input</h3>
<pre id="input_english">{english_text}</pre>
<h3>Instruction</h3>
<pre>{instruction}</pre>
<h3>Corrected/Generated</h3>
<pre id="corrected_english">{corrected}</pre>
<button onclick="copyToClipboard('corrected_english')">Copy to Clipboard</button>
<p><a href="/">Back</a></p>
<script>
function copyToClipboard(id) {{
var text = document.getElementById(id).innerText;
navigator.clipboard.writeText(text).then(function() {{
alert('Copied to clipboard!');
}}, function(err) {{
alert('Could not copy text: ' + err);
}});
}}
</script>
</body>
</html>
"""
        return HTMLResponse(html)
    except Exception as e:
        logger.error(f"convert_english error: {str(e)}", exc_info=True)
        return HTMLResponse(f"<pre>Error: {str(e)}</pre>", status_code=500)

# API endpoints - Reverted /api/hindi to previous simple version (for website/API compatibility)
@app.post("/api/hindi")
def api_hindi(hindi_text: str, instruction: str = ""):
    try:
        unicode_text = KrutiDev_to_Unicode(hindi_text)
        corrected_unicode = call_gemini_correct_text(unicode_text, language="hi", instruction=instruction)
        corrected_krutidev = Unicode_to_KrutiDev(corrected_unicode)  # New Python converter
        return {
            "input_krutidev": hindi_text,
            "instruction": instruction,
            "corrected_mangal": corrected_unicode,
            "corrected_krutidev": corrected_krutidev,
        }
    except Exception as e:
        logger.error(f"API hindi error: {str(e)}", exc_info=True)
        return {"error": str(e)}

# New route for Word macro - JSON only, to avoid affecting old API
@app.post("/api/word-macro-hindi")
def word_macro_hindi(json_body: HindiRequest = Body(...)):
    """
    Dedicated route for Word macro JSON requests.
    Expects full JSON body with hindi_text and optional instruction.
    """
    try:
        text = (json_body.hindi_text or "").strip()
        instr = (json_body.instruction or "").strip()

        if not text:
            raise HTTPException(status_code=400, detail="Missing hindi_text in JSON body")

        unicode_text = KrutiDev_to_Unicode(text)
        corrected_unicode = call_gemini_correct_text(
            unicode_text,
            language="hi",
            instruction=instr
        )
        corrected_krutidev = Unicode_to_KrutiDev(corrected_unicode)

        return {
            "input_krutidev": text,
            "instruction": instr,
            "corrected_mangal": corrected_unicode,
            "corrected_krutidev": corrected_krutidev,
        }
    except Exception as e:
        logger.error(f"Word macro API error: {str(e)}", exc_info=True)
        return {"error": str(e)}
        
@app.post("/api/only-unicode-to-krutidev")
async def only_unicode_to_krutidev(data: dict):
    unicode_text = data.get("unicode_text", "")
    if not unicode_text:
        return {"error": "Missing 'unicode_text' in request body"}
    
    try:
        result = Unicode_to_KrutiDev(unicode_text)
        return {
            "success": True,
            "krutidev": result
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/english")
def api_english(english_text: str, instruction: str = ""):
    try:
        corrected = call_gemini_correct_text(english_text, language="en", instruction=instruction)
        return {"input": english_text, "instruction": instruction, "corrected": corrected}
    except Exception as e:
        logger.error(f"API english error: {str(e)}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
