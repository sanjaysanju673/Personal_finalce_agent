from groq import Groq
from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL

client_args = {}
if GROQ_API_KEY:
    client_args["api_key"] = GROQ_API_KEY
if GROQ_BASE_URL:
    client_args["base_url"] = GROQ_BASE_URL

client = Groq(**client_args) if client_args else Groq()

response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Say hello"}
    ],
    model=GROQ_MODEL,
)

print(response.choices[0].message.content)
PermissionError