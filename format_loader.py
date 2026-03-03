# File: format_loader.py
"""
Handles loading of specific format files based on user instructions.
Supports Hindi and English mappings.
"""

import os
import logging

logger = logging.getLogger("krutidev-converter")

# Format folder
FORMAT_FOLDER = "Format"

# Mappings for Hindi and English instructions to filenames (more robust partial matches)
HINDI_MAPPINGS = {
    "shadi": "Vivahanama.txt",
    "विवाह": "Vivahanama.txt",
    "विवाहनामा": "Vivahanama.txt",
    "शादी": "Vivahanama.txt",
    "gadi": "Gadiformat.txt",
    "गाड़ी": "Gadiformat.txt",
    "गाड़ी agreement": "Gadiformat.txt",
    "कार": "Gadiformat.txt",
    "vehicle": "Gadiformat.txt",
    "jamin": "Jaminbikricnt.txt",  # Default to CNT if not specified
    "जमीन": "Jaminbikricnt.txt",
    "जमीन बिक्री": "Jaminbikricnt.txt",
    "cnt": "Jaminbikricnt.txt",
    "सीएनटी": "Jaminbikricnt.txt",
    "non cnt": "Jaminbikrinoncnt.txt",
    "नॉन सीएनटी": "Jaminbikrinoncnt.txt",
    "non cnt": "Jaminbikrinoncnt.txt",
    "affidavit": "Awedanaffidavit.txt",
    "शपथ पत्र": "Awedanaffidavit.txt",
    "शपथ-पत्र": "Awedanaffidavit.txt",
    "satyapan": "Satyapan.txt",
    "सत्यापन": "Satyapan.txt",
    "dan": "Daankrnekaagreement.txt",
    "दान": "Daankrnekaagreement.txt",
    "दान agreement": "Daankrnekaagreement.txt",
}

ENGLISH_MAPPINGS = {
    "affidavit": "Englishaffidavit.txt",
    "indemnity bond": "Englishindemnitybond.txt",
    "satyapan verification": "Englishsatyapanverification.txt",
    "verification": "Englishsatyapanverification.txt",
    # Add more as needed
}

def load_specific_format(language: str, instruction: str) -> str:
    """
    Loads the content of a specific format file based on the instruction and language.
    """
    try:
        if not instruction.strip():
            return ""
        
        mappings = HINDI_MAPPINGS if language.startswith("hi") else ENGLISH_MAPPINGS
        lower_instruction = instruction.lower()
        
        filename = None
        for key, file in mappings.items():
            if key in lower_instruction:
                filename = file
                break
        
        if not filename:
            logger.warning(f"No matching format file for instruction: {instruction}")
            return ""
        
        filepath = os.path.join(FORMAT_FOLDER, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Format file not found: {filepath}")
            return ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        logger.info(f"Loaded format file: {filename}, length: {len(content)}")
        return content
    except Exception as e:
        logger.error(f"load_specific_format error: {str(e)}")
        return ""
