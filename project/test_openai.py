from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.4",
    input="Reply with exactly: OPENAI_OK"
)

print(response.output_text)
