"""
Gemini API client for text correction and document generation.
Supports dynamic model selection: gemini-2.5-flash-lite (default) or gemini-2.5-flash (thinking_mode).
Added markdown stripping to remove bold etc. from outputs.
Added support for multiple API keys to handle quota exhaustion by rotating keys.
Improved prompts for better punctuation.
"""

import os
import requests
import logging
import re
from typing import List

from format_loader import load_specific_format

logger = logging.getLogger("krutidev-converter")

# Gemini config - multiple keys support
GEMINI_API_KEYS: List[str] = [
    k.strip()
    for k in os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", "")).split(",")
    if k.strip()
]

if not GEMINI_API_KEYS:
    raise RuntimeError("No GEMINI_API_KEY or GEMINI_API_KEYS set in environment")


def strip_markdown(text: str) -> str:
    """
    Strips common markdown like bold, italic, headers, lists, code blocks to plain text.
    """
    # Bold **
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    # Italic *
    text = re.sub(r'\*(.+?)\*', r'\1', text, flags=re.DOTALL)
    # Headers #
    text = re.sub(r'^#{1,6}\s*(.+)$', r'\1', text, flags=re.MULTILINE)
    # Lists - or * or +
    text = re.sub(r'^\s*[-+*]\s+', '', text, flags=re.MULTILINE)
    # Code blocks
    text = re.sub(r'```[\s\S]*?```', '', text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()


def _make_gemini_call(prompt_text: str, gemini_url: str, pass_name: str = "pass") -> str:
    """
    Internal function to make a single Gemini API call with the provided URL.
    Tries multiple keys on quota errors.
    """
    headers_base = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    for i, api_key in enumerate(GEMINI_API_KEYS):
        headers = headers_base.copy()
        headers["x-goog-api-key"] = api_key
        logger.info(f"Calling Gemini {pass_name} with key index {i+1}/{len(GEMINI_API_KEYS)} using URL: {gemini_url}")

        try:
            resp = requests.post(gemini_url, headers=headers, json=payload, timeout=60)
            logger.info(f"Gemini {pass_name} status with key {i+1}: {resp.status_code}")

            if resp.status_code == 200:
                j = resp.json()
                try:
                    result = j["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"Gemini {pass_name} successful with key {i+1}")
                    return result.strip()
                except (KeyError, IndexError) as e:
                    logger.error(f"Parsing Gemini {pass_name} response error with key {i+1}: {e}")
                    continue
            elif resp.status_code == 429:  # Quota exceeded
                logger.warning(f"Quota exceeded for key {i+1}, trying next")
                continue
            else:
                logger.error(f"Gemini {pass_name} error with key {i+1}: {resp.status_code} {resp.text[:200]}")
                continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for Gemini {pass_name} with key {i+1}: {e}")
            continue

    raise RuntimeError(f"All Gemini API keys failed for {pass_name}.")


def call_gemini_correct_text(
    user_text: str,
    language: str = "hi",
    instruction: str = "",
    thinking_mode: bool = False
) -> str:
    """
    Calls Gemini API with dynamic model based on thinking_mode.
    thinking_mode=True  → gemini-2.5-flash
    thinking_mode=False → gemini-2.5-flash-lite (default, faster)
    Uses two-pass approach: correction + review.
    """
    try:
        model_name = "gemini-2.5-flash" if thinking_mode else "gemini-2.5-flash-lite"
        base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
        default_url = f"{base_url}{model_name}:generateContent"
        gemini_url = os.getenv("GEMINI_URL", default_url)  # Env override if needed

        format_content = ""
        use_format = bool(instruction.strip())

        if language.startswith("hi"):
            base_instruction = (
                "आप एक एडिटिंग और डॉक्यूमेंट जेनरेशन सहायक हैं। केवल टाइपिंग/स्पेलिंग/पंक्चुएशन गलतियाँ सुधारें।\n"
                "वाक्य संरचना, केस सेक्शन कानूनी भाषा या अर्थ न बदलें।\n"
                "मार्कडाउन का उपयोग न करें, जैसे **बोल्ड** या *इटैलिक*। सादा टेक्स्ट दें।\n"
                "नामों के बाद अल्पविराम (,) जोड़ें, जैसे 'ओम प्रकाश यादव,'।\n"
                "उम्र, ग्राम, पोस्ट, थाना, जिला, राज्य आदि के पहले हाइफन (-) लगाएँ, जैसे 'उम्र-26 वर्ष,' 'ग्राम-बेता,'।\n"
                "अंत में पूर्ण विराम (।) जोड़ें यदि उपयुक्त हो।\n"
            )
            if use_format:
                format_content = load_specific_format(language, instruction)
                if format_content:
                    base_instruction += (
                        f"निर्देश '{instruction}' के आधार पर दिए गए टेक्स्ट डिटेल्स से डॉक्यूमेंट भरें। फॉर्मेट का उपयोग करें लेकिन केवल रेलेवेंट भाग।\n"
                        "शर्तों या पॉइंट्स को नंबरिंग से लिखें (1., 2., आदि), बुलेट मार्क्स जैसे * या - का उपयोग न करें।\n"
                        f"संदर्भ फॉर्मेट: {format_content}\n\n"
                    )
                else:
                    base_instruction += f"निर्देश '{instruction}' के अनुसार डॉक्यूमेंट जेनरेट करें। पंक्चुएशन जोड़ें जैसा ऊपर निर्देशित।\n\n"
            else:
                base_instruction += "केवल दिए गए टेक्स्ट को सुधारें, कोई अतिरिक्त फॉर्मेट या डॉक्यूमेंट न जोड़ें।\n\n"

            review_instruction = (
                "नीचे दिए गए सुधारे हुए टेक्स्ट की समीक्षा करें और कोई बची हुई टाइपिंग/स्पेलिंग/पंक्चुएशन गलतियाँ सुधारें।\n"
                "केवल आवश्यक सुधार करें, अर्थ या संरचना न बदलें। "
            )
            if use_format:
                review_instruction += "यदि जेनरेटेड डॉक्यूमेंट है, तो फॉर्मेट चेक करें, सिर्फ एक डॉक्यूमेंट दें, सारे न लिस्ट करें। बुलेट्स * को नंबरिंग से बदलें। पंक्चुएशन सुनिश्चित करें।\n"
            review_instruction += "मार्कडाउन न दें, सादा Unicode देवनागरी टेक्स्ट में आउटपुट दें।\n\n"

        else:
            base_instruction = (
                "You are a copyeditor and document generation assistant. Only fix spelling, typing, punctuation, and capitalization errors.\n"
                "Do NOT change meaning, structure, or legal terminology.\n"
                "Do not use markdown like **bold** or *italic*. Plain text only.\n"
                "Add commas after names, e.g., 'Om Prakash Yadav,'.\n"
                "Add hyphens before fields like age, village, post, thana, district, state, e.g., 'age-26 years,' 'village-Beta,'.\n"
                "Add period (.) at the end if appropriate.\n"
            )
            if use_format:
                format_content = load_specific_format(language, instruction)
                if format_content:
                    base_instruction += (
                        f"Based on instruction '{instruction}', fill the document using text details. Use the format but only relevant parts.\n"
                        "For conditions or points, use numbering (1., 2., etc.), do not use bullet marks like * or -.\n"
                        f"Reference format: {format_content}\n\n"
                    )
                else:
                    base_instruction += f"Generate document based on instruction '{instruction}'. Add punctuation as instructed above.\n\n"
            else:
                base_instruction += "Only correct the given text, do not add any extra formats or documents.\n\n"

            review_instruction = (
                "Review the following corrected/generated text and fix any remaining spelling, typing, punctuation, or capitalization errors.\n"
                "Only make necessary fixes; do NOT change meaning or structure. "
            )
            if use_format:
                review_instruction += "If it's a generated document, ensure format compliance, output only one document, not a list. Replace bullets * with numbering. Ensure punctuation.\n"
            review_instruction += "Output plain text, no markdown.\n\n"

        full_instruction = base_instruction
        if instruction.strip():
            full_instruction += (
                f"उपयोगकर्ता निर्देश: {instruction}\n\n"
                if language.startswith("hi")
                else f"User instruction: {instruction}\n\n"
            )

        prompt_text = full_instruction + user_text
        logger.info("Calling Gemini first pass")
        corrected = _make_gemini_call(prompt_text, gemini_url=gemini_url, pass_name="first pass")

        review_prompt = review_instruction + corrected
        logger.info("Calling Gemini second pass")
        final_corrected = _make_gemini_call(review_prompt, gemini_url=gemini_url, pass_name="second pass")

        final_corrected = strip_markdown(final_corrected)

        return final_corrected

    except Exception as e:
        logger.error(f"call_gemini_correct_text error: {str(e)}", exc_info=True)
        return user_text  # Fallback to original text
