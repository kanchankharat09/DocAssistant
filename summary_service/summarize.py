# S3: read each transcript, ask Groq for a summary, save it as a json file.
#
# Setup:   pip install groq
#          put your key in a file called .env in the main folder:  GROQ_API_KEY=your_key
# Run:     python3 summary_service/summarize.py        (all transcripts)
#          python3 summary_service/summarize.py T01    (only one)

import json
import os
import sys

from groq import Groq

# read the key from the .env file if it is there
# (the .env file has one line like:  GROQ_API_KEY=your_key )
if os.path.exists(".env"):
    for line in open(".env").read().split("\n"):
        if "=" in line and not line.startswith("#"):
            key_name, key_value = line.split("=", 1)
            os.environ[key_name.strip()] = key_value.strip().strip('"')

# the model name can be changed from outside, check the Groq website for names
model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
# option b (smaller model, use it if you get a "rate limit" error):
# model_name = "llama-3.1-8b-instant"

test_data_folder = "test_data"
output_folder = "results/summaries"

# this tells the AI what to do
prompt = """You summarise a doctor-patient consultation transcript.
Return ONLY a JSON object with these keys:
chief_complaint, duration, associated_symptoms, past_history, allergies, doctor_instructions (all strings, use "" if not said)
and medicines: a list, each item has name, dose, frequency, duration (all strings).
Copy medicine names and doses exactly as written in the transcript. Do not correct them.
Do not add anything that is not in the transcript."""

text_keys = ["chief_complaint", "duration", "associated_symptoms", "past_history", "allergies", "doctor_instructions"]
medicine_keys = ["name", "dose", "frequency", "duration"]

client = Groq()
os.makedirs(output_folder, exist_ok=True)

# which transcripts to run: the ones typed after the command, or all
wanted = sys.argv[1:]
files = []
for name in os.listdir(test_data_folder):
    if name.endswith("_transcript.txt"):
        files.append(name)
files.sort()

good_count = 0
for file_name in files:
    case_id = file_name[:3]          # T01, T02 ...
    if len(wanted) > 0 and case_id not in wanted:
        continue

    transcript = open(test_data_folder + "/" + file_name).read()

    # ask the AI (temperature 0 so the answer stays the same every time)
    answer = client.chat.completions.create(
        model=model_name,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
    )
    # print(answer.choices[0].message.content)
    summary = json.loads(answer.choices[0].message.content)

    # check that the json has all the keys we need (this is the S3 test)
    shape_ok = True
    for key in text_keys:
        if not isinstance(summary.get(key), str):
            shape_ok = False
    if not isinstance(summary.get("medicines"), list):
        shape_ok = False
    else:
        for medicine in summary["medicines"]:
            for key in medicine_keys:
                if not isinstance(medicine.get(key), str):
                    shape_ok = False

    if shape_ok:
        good_count = good_count + 1

    result = {"model": model_name, "temperature": 0, "shape_ok": shape_ok, "summary": summary}
    out_file = open(output_folder + "/" + case_id + ".json", "w")
    out_file.write(json.dumps(result, indent=2, ensure_ascii=False))
    out_file.close()

    print(case_id, "shape ok:", shape_ok)

print("shape ok for", good_count, "transcripts (model:", model_name, ")")
