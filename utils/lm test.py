# Example: reuse your existing OpenAI setup
from openai import OpenAI, APIConnectionError
import sys

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

try:
    completion = client.chat.completions.create(
        model="bartowski/nvidia_Llama-3.1-8B-UltraLong-4M-Instruct-GGUF",
        messages=[
            {"role": "system", "content": "Always answer in rhymes."},
            {"role": "user", "content": "Introduce yourself."}
        ],
        temperature=0.7,
    )
except APIConnectionError:
    print("Connection error: could not connect to local server at http://localhost:1234. Ensure the server is running.")
    sys.exit(1)

print(completion.choices[0].message)