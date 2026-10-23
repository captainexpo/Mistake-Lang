import json
import os
import time

import requests

from mistake.tokenizer.lexer import keywords_en

TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_RETRIES = 5
BATCH_SIZE = 40   # words per request

def _request(text: str, dest_language: str) -> str:
    params = {"client": "gtx", "sl": "en", "tl": dest_language, "dt": "t", "q": text}
    for attempt in range(MAX_RETRIES):
        response = requests.get(TRANSLATE_URL, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 429:
            delay = min(2 ** attempt, 30)
            print(f"Google is rate-limiting; waiting {delay}s...")
            time.sleep(delay)
            continue
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:   # errors sometimes come back as an HTML page
            raise RuntimeError("unexpected non-JSON response (possibly blocked)")

        return "".join(seg[0] for seg in data[0] if seg and seg[0])
    raise RuntimeError("still rate-limited after retries")

def translate_keyword(keyword: str, dest_language: str) -> str:
    try:
        return _request(keyword, dest_language).strip()
    except (requests.RequestException, RuntimeError, IndexError, TypeError) as e:
        print(f"Failed to translate {keyword}: {e}")
        return keyword

def translate_keywords(keywords: list[str], dest_language: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(keywords), BATCH_SIZE):
        batch = keywords[i:i + BATCH_SIZE]
        try:
            lines = _request("\n".join(batch), dest_language).split("\n")
        except (requests.RequestException, RuntimeError, IndexError, TypeError) as e:
            print(f"Batch failed ({e}). Translating one at a time")
            lines = []
        if len(lines) == len(batch):
            out.update({kw: line.strip() or kw for kw, line in zip(batch, lines)})
        else:
            for kw in batch:
                out[kw] = translate_keyword(kw, dest_language)
                time.sleep(0.5)
        if i + BATCH_SIZE < len(keywords):
            time.sleep(1)
    return out

def purge_localizations():
    localizations_path = os.path.join(os.path.dirname(__file__), "./tokenizer/.localizations")
    if os.path.exists(localizations_path):
        for file in os.listdir(localizations_path):
            file_path = os.path.join(localizations_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Purged all localization files in {localizations_path}")
        os.rmdir(localizations_path)
    else:
        print(f"No localization files found in {localizations_path}")

def translate(dest_language: str):
    localizations_path = os.path.join(os.path.dirname(__file__), f"./tokenizer/.localizations/{dest_language}.json")
    os.makedirs(os.path.dirname(localizations_path), exist_ok=True)

    ret = {}

    if dest_language == "en_US":
        ret = {i: i for i in keywords_en}
        print("English keywords built in: no translation needed.")
    else:
        english = list(keywords_en.keys())

        translated_keywords = translate_keywords(english, dest_language)

        ret = {}
        for en_word, translated in translated_keywords.items():
            key = translated.lower().replace(" ", "_")
            while key in ret:
                print(f"Warning: '{en_word}' and '{ret[key]}' both translate to '{key}'. {en_word} will be translated to _{key}")
                key = "_"+key
            ret[key] = en_word.lower()
        print(f"Translated keywords saved to {localizations_path}")

    with open(localizations_path, "w", encoding="utf-8") as f:
        json.dump(ret, f, ensure_ascii=False, indent=4)

    return ret

if __name__ == "__main__":
    translate("es")
