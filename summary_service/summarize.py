"""S3: turn each transcript in test_data/ into a structured JSON summary with Groq.

Usage (from repo root):
    pip install groq
    export GROQ_API_KEY=your_key
    export GROQ_MODEL=llama-3.3-70b-versatile   # optional; check the Groq console for current model names
    python3 summary_service/summarize.py            # all transcripts
    python3 summary_service/summarize.py T01 T04    # only some
"""
import json, os, pathlib, sys

from groq import Groq

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_DATA = ROOT / "test_data"
OUT = ROOT / "results" / "summaries"
MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

PROMPT = """You summarise a doctor-patient consultation transcript.
Return ONLY a JSON object with exactly these keys:
- "chief_complaint": string
- "duration": string ("" if not stated)
- "associated_symptoms": string ("" if not stated)
- "past_history": string ("" if not stated)
- "allergies": string ("" if not stated)
- "medicines": list of objects, each with "name", "dose", "frequency", "duration" (strings, "" if not stated)
- "doctor_instructions": string
Copy medicine names and doses exactly as written in the transcript. Do not correct them.
Do not add anything that is not in the transcript. Do not diagnose or recommend medicines."""

STR_KEYS = ["chief_complaint", "duration", "associated_symptoms", "past_history",
            "allergies", "doctor_instructions"]
MED_KEYS = ["name", "dose", "frequency", "duration"]


def schema_ok(d):
    """True if d has the agreed JSON shape (S3 test: 20 of 20 must pass)."""
    if not isinstance(d, dict):
        return False
    if not all(isinstance(d.get(k), str) for k in STR_KEYS):
        return False
    meds = d.get("medicines")
    return isinstance(meds, list) and all(
        isinstance(m, dict) and all(isinstance(m.get(k), str) for k in MED_KEYS) for m in meds
    )


def summarise(client, text):
    r = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": text}],
    )
    return json.loads(r.choices[0].message.content)


def main(ids):
    client = Groq()  # reads GROQ_API_KEY
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(TEST_DATA.glob("T??_transcript.txt"))
    ok = 0
    for f in files:
        tid = f.name[:3]
        if ids and tid not in ids:
            continue
        try:
            data = summarise(client, f.read_text())
        except Exception as e:  # bad JSON or API error counts as a schema failure
            print(f"{tid}: ERROR {e}")
            continue
        good = schema_ok(data)
        ok += good
        (OUT / f"{tid}.json").write_text(json.dumps(
            {"model": MODEL, "temperature": 0, "schema_ok": good, "summary": data},
            indent=2, ensure_ascii=False))
        print(f"{tid}: schema {'OK' if good else 'FAIL'}")
    print(f"schema OK on {ok} transcripts (model {MODEL}, temperature 0)")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
