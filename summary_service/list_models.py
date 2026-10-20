# Shows which models your Groq key can use right now.
# Run it from the main folder:  python summary_service/list_models.py

import os

from groq import Groq

# read the key from the .env file (same as summarize.py)
if os.path.exists(".env"):
    for line in open(".env", encoding="utf-8-sig").read().split("\n"):
        if "=" in line and not line.startswith("#"):
            key_name, key_value = line.split("=", 1)
            os.environ[key_name.strip()] = key_value.strip().strip('"').strip("'")

client = Groq()
models = client.models.list()

for model in models.data:
    print(model.id)
