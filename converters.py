
# File: converters.py
"""
KrutiDev to Unicode (Mangal) and Unicode to KrutiDev converters.
Handles the core mapping logic with special handling for 'f', 'r', 'Z', etc.
Added lock for 'bZ' in Z right-shift to prevent shifting for 'ई'.
"""

import logging
import re

logger = logging.getLogger("krutidev-converter")

def KrutiDev_to_Unicode(krutidev_substring):
    """
    Converts KrutiDev encoded text to Unicode Devanagari (Mangal).
    Handles special shifts for 'f' (matra) and 'Z' (reph).
    """
    try:
        modified_substring = krutidev_substring

        array_one = ["ñ","Q+Z","sas","aa",")Z","ZZ","‘","’","“","”",  
            "å",  "ƒ",  "„",   "…",   "†",   "‡",   "ˆ",   "‰",   "Š",   "‹",   
            "¶+",   "d+", "[+k","[+", "x+",  "T+",  "t+", "M+", "<+", "Q+", ";+", "j+", "u+",  
            "Ùk", "Ù", "Dr", "–", "—","é","™","=kk","f=k",    
            "à",   "á",    "â",   "ã",   "ºz",  "º",   "í", "{k", "{", "=",  "«",     
            "Nî",   "Vî",    "Bî",   "Mî",   "<î", "|", "K", "}",  
            "J",   "Vª",   "Mª",  "<ªª",  "Nª",   "Ø",  "Ý", "nzZ",  "æ", "ç", "Á", "xz", "#", ":",  
            "v‚","vks",  "vkS",  "vk",    "v",  "b±", "Ã",  "bZ",  "b",  "m",  "Å",  ",s",  ",",   "_",  
            "ô",  "d", "Dk", "D", "[k", "[", "x","Xk", "X", "Ä", "?k", "?",   "³",   
            "pkS",  "p", "Pk", "P",  "N",  "t", "Tk", "T",  ">", "÷", "¥",  
            "ê",  "ë",   "V",  "B",   "ì",   "ï", "M+", "<+", "M",  "<", ".k", ".",      
            "r",  "Rk", "R",   "Fk", "F",  ")", "n", "/k", "èk",  "/", "Ë", "è", "u", "Uk", "U",     
            "i",  "Ik", "I",   "Q",    "¶",  "c", "Ck",  "C",  "Hk",  "H", "e", "Ek",  "E",  
            ";",  "¸",   "j",    "y", "Yk",  "Y",  "G",  "o", "Ok", "O",  
            "'k", "'",   "\"k",  "\"",  "l", "Lk",  "L",   "g",   
            "È", "z",   
            "Ì", "Í", "Î",  "Ï",  "Ñ",  "Ò",  "Ó",  "Ô",   "Ö",  "Ø",  "Ù","Ük", "Ü",  
            "‚",    "ks",   "kS",   "k",  "h",    "q",   "w",   "`",    "s",    "S",  
            "a",    "¡",    "%",     "W",  "•", "·", "∙", "·", "~j",  "~", "\\","+"," ः",  
            "^", "*",  "Þ", "ß", "(", "¼", "½", "¿", "À", "¾", "A", "-", "&", "&", "Œ", "]","~ ","@"]  
          
        array_two = ["॰","QZ+","sa","a","र्द्ध","z","\"","\"","'","'",  
            "०",  "१",  "२",  "३",     "४",   "५",  "६",   "७",   "८",  "९",     
            "फ़्",  "क़",  "ख़", "ख़्",  "ग़", "ज़्", "ज़",  "ड़",  "ढ़",   "फ़",  "य़",  "ऱ",  "ऩ",      
            "त्त", "त्त्", "क्त",  "दृ",  "कृ","न्न","न्न्","=k","f=",  
            "ह्न",  "ह्य",  "हृ",  "ह्म",  "ह्र",  "ह्",   "द्द",  "क्ष", "क्ष्", "त्र", "त्र्",   
            "छ्य",  "ट्य",  "ठ्य",  "ड्य",  "ढ्य", "द्य", "ज्ञ", "द्व",  
            "श्र",  "ट्र",    "ड्र",    "ढ्र",    "छ्र",   "क्र",  "फ्र", "र्द्र",  "द्र",   "प्र", "प्र",  "ग्र", "रु",  "रू",  
            "ऑ",   "ओ",  "औ",  "आ",   "अ", "ईं", "ई",  "ई",   "इ",  "उ",   "ऊ",  "ऐ",  "ए", "ऋ",  
            "क्क", "क", "क", "क्", "ख", "ख्", "ग", "ग", "ग्", "घ", "घ", "घ्", "ङ",  
            "चै",  "च", "च", "च्", "छ", "ज", "ज", "ज्",  "झ",  "झ्", "ञ",  
            "ट्ट",   "ट्ठ",   "ट",   "ठ",   "ड्ड",   "ड्ढ",  "ड़", "ढ़", "ड",   "ढ", "ण", "ण्",     
            "त", "त", "त्", "थ", "थ्",  "द्ध",  "द", "ध", "ध", "ध्", "ध्", "ध्", "न", "न", "न्",  
            "प", "प", "प्",  "फ", "फ्",  "ब", "ब", "ब्",  "भ", "भ्",  "म",  "म", "म्",    
            "य", "य्",  "र", "ल", "ल", "ल्",  "ळ",  "व", "व", "व्",     
            "श", "श्",  "ष", "ष्", "स", "स", "स्", "ह",   
            "ीं", "्र",      
            "द्द", "ट्ट","ट्ठ","ड्ड","कृ","भ","्य","ड्ढ","झ्","क्र","त्त्","श","श्",  
            "ॉ",  "ो",   "ौ",   "ा",   "ी",   "ु",   "ू",   "ृ",   "े",   "ै",  
            "ं",   "ँ",   "ः",   "ॅ",  "ऽ", "ऽ", "ऽ", "ऽ", "्र",  "्", "?", "़",":",  
            "‘",   "’",   "“",   "”",  ";",  "(",    ")",   "{",    "}",   "=", "।", ".", "-",  "µ", "॰", ",","् ","/"]  
          
        array_one += ["@", "%"]
        array_two += ["/", ":"]
          
        array_one_length = len(array_one)  
          
        # Specialty characters  
          
        # Move "f"  to correct position and replace  
        modified_substring = "  " + modified_substring + "  "  
        position_of_f = modified_substring.rfind("f")  
        while position_of_f != -1:  
            if position_of_f + 1 >= len(modified_substring):  
                position_of_f = modified_substring.rfind("f", 0, position_of_f - 1)  
                continue  
            next_char = modified_substring[position_of_f + 1]  
            modified_substring = modified_substring[:position_of_f] + next_char + "f" + modified_substring[position_of_f + 2:]  
            old_pos = position_of_f  
            position_of_f = old_pos + 1  
            if next_char != "z":  
                position_of_f = modified_substring.rfind("f", 0, old_pos - 1)  
        modified_substring = modified_substring.replace("f","ि")  
        modified_substring = modified_substring.strip()  
          
        # Replace Z with ्र  
        modified_substring = modified_substring.replace("z", "्र")  
          
        # Replace ASCII with Unicode  
        for input_symbol_idx in range(0, array_one_length):  
            modified_substring = modified_substring.replace(array_one[input_symbol_idx ] , array_two[input_symbol_idx] )  
          
        return modified_substring
    except Exception as e:
        logger.error(f"KrutiDev_to_Unicode error: {str(e)}", exc_info=True)
        return krutidev_substring  # Fallback to original

def Unicode_to_KrutiDev(unicode_substring):
    """
    Converts Unicode Devanagari (Mangal) to KrutiDev encoded text.
    Handles special shifts for 'f' (matra left-shift), 'r' (reph as Z with right-shift).
    Added lock: Skip Z right-shift if previous char is 'b' (for 'ई').
    """
    try:
        logger.info("Starting Unicode_to_KrutiDev")
        modified_substring = unicode_substring  
          
        # First, handle punctuation to avoid conflicts
        modified_substring = modified_substring.replace("/", "@")
        modified_substring = modified_substring.replace(":", "%")
        modified_substring = modified_substring.replace("+", "$")
        modified_substring = modified_substring.replace("_", "-")  # New: _ to -
        logger.info("Punctuation handled")
          
        # f shift logic (before replacing ि and ्)
        modified_substring += "  "  # add two spaces
        f_count = 0
        position_of_f = 0
        while True:
            position_of_f = modified_substring.find("ि", position_of_f)
            if position_of_f == -1:
                break
            f_count += 1
            if position_of_f == 0:
                position_of_f += 1
                continue
            char_left = modified_substring[position_of_f - 1]
            # Replace char_left + "ि" with "f" + char_left
            start = position_of_f - 1
            modified_substring = modified_substring[:start] + "f" + char_left + modified_substring[position_of_f + 1:]
            position_of_f = start  # now position of 'f'
            # Handle halant loop
            halant_count = 0
            while position_of_f > 0 and modified_substring[position_of_f - 1] == "्":
                halant_count += 1
                if position_of_f - 2 < 0:
                    break
                prev_consonant = modified_substring[position_of_f - 2]
                string_to_be_replaced = prev_consonant + "्"
                # Replace string_to_be_replaced + "f" with "f" + string_to_be_replaced
                start2 = position_of_f - 2
                modified_substring = modified_substring[:start2] + "f" + string_to_be_replaced + modified_substring[position_of_f + 1:]
                position_of_f = start2  # new position of 'f'
            logger.debug(f"f move: halants {halant_count}")
            position_of_f += 1
        logger.info(f"f shift handled, count: {f_count}")
        modified_substring = modified_substring[:-2].strip()  # remove added spaces
          
        # Now array replace (includes replacing ् to ~ after f logic)
        array_one = ["‘",   "’",   "“",   "”",   "(",    ")",   "{",    "}",   "=", "।",  "?",  "-",  "µ", "॰", ",", ".", "् ",   
        "०",  "१",  "२",  "३",     "४",   "५",  "६",   "७",   "८",  "९", "x",   
        "\u095e\u094d",  "\u0958",  "\u0959",  "\u095a", "\u095b\u094d", "\u095b",  "\u095c",  "\u095d",   "\u095e",  "\u095f",  "\u0930\u093c",  "\u0919\u093c",    
        "त्त्",   "त्त",     "क्त",  "दृ",  "कृ",  
        "ह्न",  "ह्य",  "हृ",  "ह्म",  "ह्र",  "ह्",   "द्द",  "क्ष्", "क्ष", "त्र्", "त्र","ज्ञ",  
        "छ्य",  "ट्य",  "ठ्य",  "ड्य",  "ढ्य", "द्य","द्व",  
        "श्र",  "ट्र",    "ड्र",    "ढ्र",    "छ्र",   "क्र",  "फ्र",  "द्र",   "प्र",   "ग्र", "रु",  "रू",  
        "्र",  
        "ओ",  "औ",  "आ",   "अ",   "ई",   "इ",  "उ",   "ऊ",  "ऐ",  "ए", "ऋ",  
        "क्",  "क",  "क्क",  "ख्",   "ख",    "ग्",   "ग",  "घ्",  "घ",    "ङ",  
        "चै",   "च्",   "च",   "छ",  "ज्", "ज",   "झ्",  "झ",   "ञ",  
        "ट्ट",   "ट्ठ",   "ट",   "ठ",   "ड्ड",   "ड्ढ",  "ड",   "ढ",  "ण्", "ण",    
        "त्",  "त",  "थ्", "थ",  "द्ध",  "द", "ध्", "ध",  "न्",  "न",    
        "प्",  "प",  "फ्", "फ",  "ब्",  "ब", "भ्",  "भ",  "म्",  "म",  
        "य्",  "य",  "र",  "ल्", "ल",  "ळ",  "व्",  "व",   
        "श्", "श",  "ष्", "ष",  "स्",   "स",   "ह",       
        "ऑ",   "ॉ",  "ो",   "ौ",   "ा",   "ी",   "ु",   "ू",   "ृ",   "े",   "ै",  
        "ं",   "ँ",   "ः",   "ॅ",    "ऽ",  "् ", "्", "़" ]  
          
        array_two = ["^", "*",  "Þ", "ß", "¼", "½", "¿", "À", "¾", "A", "\\", "&", "&", "Œ", "]","-","~ ",   
        "å",  "ƒ",  "„",   "…",   "†",   "‡",   "ˆ",   "‰",   "Š",   "‹","Û",  
        "¶",   "d",    "[k",  "x",  "T",  "t",   "M+", "<+", "Q",  ";",    "j",   "u",  
        "Ù",   "Ùk",   "Dr",    "–",   "—",         
        "à",   "á",    "â",   "ã",   "ºz",  "º",   "í", "{", "{k",  "«", "=","K",   
        "Nî",   "Vî",    "Bî",   "Mî",   "<î", "|","}",  
        "J",   "Vª",   "Mª",  "<ªª",  "Nª",   "Ø",  "Ý",   "æ", "ç", "xz", "#", ":",  
        "z",   # Changed to z
        "vks",  "vkS",  "vk",    "v",   "bZ",  "b",  "m",  "Å",  ",s",  ",",   "_",  
        "D",  "d",    "ô",     "[",     "[k",    "X",   "x",  "?",    "?k",   "³",   
        "pkS",  "P",    "p",  "N",   "T",    "t",   "÷",  ">",   "¥",  
        "ê",      "ë",      "V",  "B",   "ì",       "ï",     "M",  "<",  ".", ".k",     
        "R",  "r",   "F", "Fk",  ")",    "n", "/",  "/k",  "U", "u",     
        "I",  "i",   "¶", "Q",   "C",  "c",  "H",  "Hk", "E",   "e",  
        "¸",   ";",    "j",  "Y",   "y",  "G",  "O",  "o",  
        "'", "'k",  "\"", "\"k", "L",   "l",   "g",        
        "v‚",    "‚",    "ks",   "kS",   "k",     "h",    "q",   "w",   "`",    "s",    "S",  
        "a",    "¡",    "%",     "W",   "·",   "~ ", "~", "+" ]  
          
        array_one_length = len(array_one)  
          
        # Specialty characters (after f, before array replace)
        modified_substring = modified_substring.replace ("\u0958", "\u0958")     
        modified_substring = modified_substring.replace ("\u0959", "\u0959")  
        modified_substring = modified_substring.replace ("\u095a", "\u095a")  
        modified_substring = modified_substring.replace ("\u095b", "\u095b")  
        modified_substring = modified_substring.replace ("\u095c", "\u095c")  
        modified_substring = modified_substring.replace ("\u095d", "\u095d")  
        modified_substring = modified_substring.replace ("\u0919\u093c", "\u0919\u093c")  
        modified_substring = modified_substring.replace ("\u095e", "\u095e")  
        modified_substring = modified_substring.replace ("\u095f", "\u095f")  
        modified_substring = modified_substring.replace ("\u0930\u093c", "\u0930\u093c")  
          
        # Replace Unicode with ASCII  
        for input_symbol_idx in range(0, array_one_length):  
            modified_substring = modified_substring.replace(array_one[input_symbol_idx ] , array_two[input_symbol_idx] )  
          
        # Post-processing for j~ to Z and right-shift
        modified_substring += "  "  # add spaces for boundary handling
        # First, replace all "j~" with "Z"
        modified_substring = modified_substring.replace("j~", "Z")
        # Now, handle right-shift for Z
        z_count = 0
        position_of_z = 0
        while True:
            position_of_z = modified_substring.find("Z", position_of_z)
            if position_of_z == -1:
                break
            z_count += 1
            if position_of_z + 1 >= len(modified_substring):
                position_of_z += 1
                continue
            next_char = modified_substring[position_of_z + 1]
            if next_char == " " or next_char == "~":
                # Don't shift if next is space or halant
                position_of_z += 1
                continue
            # Lock: Skip shift if previous char is 'b' (for 'bZ' -> 'ई')
            prev_char = modified_substring[position_of_z - 1] if position_of_z > 0 else " "
            if prev_char == "b":
                logger.debug(f"Lock applied: Skipping shift for bZ at pos {position_of_z}")
                position_of_z += 1
                continue
            # Right-shift: replace "Z" + next_char with next_char + "Z"
            start = position_of_z
            modified_substring = modified_substring[:start] + next_char + "Z" + modified_substring[position_of_z + 2:]
            position_of_z = start + 2  # now position after the moved Z
        logger.info(f"Z right-shift handled, count: {z_count}")
        # Additional shift for "Zk" to "kZ"
        modified_substring = modified_substring.replace("AZ", "ZA")
        modified_substring = modified_substring.replace("Zk", "kZ")
        # Final extra Z right-shift: Only if "Zh" after all shifts, swap to "hZ" (once per occurrence, word-safe)
        pos = 0
        while True:
            pos = modified_substring.find("Zh", pos)
            if pos == -1:
                break
            # Check word boundary: only prev not space (allow end-of-word)
            prev_char = modified_substring[pos-1] if pos > 0 else " "
            if prev_char != " ":
                # Swap "Zh" to "hZ"
                modified_substring = modified_substring[:pos] + "hZ" + modified_substring[pos+2:]
                pos += 2  # Skip after swap
            else:
                pos += 2
        logger.info("Final 'Zh' extra shift done")
        modified_substring = modified_substring.strip()  # remove added spaces
          
        logger.info("Unicode_to_KrutiDev completed")
        return modified_substring
    except Exception as e:
        logger.error(f"Unicode_to_KrutiDev error: {str(e)}", exc_info=True)
        return unicode_substring  # Fallback to original
