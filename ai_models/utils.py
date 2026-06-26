import re
from datetime import datetime


def clean_text(text):
    """
    Clean OCR text by removing extra spaces and converting to uppercase.
    Example:
        "Paracetamol   500mg \n Exp 12/2027"
    becomes:
        "PARACETAMOL 500MG EXP 12/2027"
    """
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()


def extract_expiry_date(text):
    """
    Find expiry date from OCR text.

    Supported examples:
    - EXP 12/2027
    - EXP: 05-2026
    - EXPIRY 11/25
    - USE BEFORE 08/2027
    """

    if not text:
        return None

    patterns = [
        r'EXP[:\s]*([0-9]{1,2}[/-][0-9]{2,4})',
        r'EXPIRY[:\s]*([0-9]{1,2}[/-][0-9]{2,4})',
        r'USE BEFORE[:\s]*([0-9]{1,2}[/-][0-9]{2,4})',
        r'([0-9]{1,2}[/-][0-9]{2,4})'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]

    return None


def parse_expiry_date(expiry_str):
    """
    Convert expiry string into datetime object.

    Examples:
    "12/2027" -> datetime(2027, 12, 1)
    "05-26"   -> datetime(2026, 5, 1)
    """

    if not expiry_str:
        return None

    expiry_str = expiry_str.replace("-", "/").strip()

    try:
        parts = expiry_str.split("/")
        if len(parts) == 2:
            month = int(parts[0])
            year = int(parts[1])

            if year < 100:
                year += 2000

            if 1 <= month <= 12:
                return datetime(year, month, 1)

    except:
        return None

    return None


def is_expired(expiry_date):
    """
    Check whether medicine is expired based on current month and year.
    Returns:
        True  -> expired
        False -> not expired
        None  -> if expiry_date is missing
    """

    if expiry_date is None:
        return None

    today = datetime.today()

    if expiry_date.year < today.year:
        return True

    if expiry_date.year == today.year and expiry_date.month < today.month:
        return True

    return False


def extract_medicine_name(text):
    """
    Try to find medicine name from OCR text.

    This is a simple rule-based approach:
    - remove common medicine label words
    - return first meaningful word
    """

    if not text:
        return "UNKNOWN"

    ignore_words = {
        "TABLET", "TABLETS", "CAPSULE", "CAPSULES", "SYRUP",
        "BATCH", "MFG", "EXP", "EXPIRY", "DATE", "USE",
        "BEFORE", "MG", "ML", "G", "MRP", "RS", "PRICE"
    }

    words = text.split()
    candidates = []

    for word in words:
        word = word.strip().upper()

        # skip very short words
        if len(word) <= 2:
            continue

        # skip ignored label words
        if word in ignore_words:
            continue

        # skip pure numbers
        if word.isdigit():
            continue

        candidates.append(word)

    if candidates:
        return candidates[0]

    return "UNKNOWN"