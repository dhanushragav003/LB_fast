import os
from openai import OpenAI

client = OpenAI(
    base_url="https://ollama.com/v1",
    api_key="e9739b1968c7475abe7757c2637c3343.9u0wzYAooPG4wknJLs0t2oA0"
)

messages = [
    {
        "role": "user",
        "content": "Why is the sky blue?"
    }
]

stream = client.chat.completions.create(
    model="gpt-oss:120b",
    messages=messages,
    stream=True
)

for chunk in stream:
    delta = chunk.choices[0].delta
    if delta and delta.content:
        print(delta.content, end="", flush=True)
