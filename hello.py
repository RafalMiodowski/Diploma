from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

odpowiedz = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "Cześć! Przedstaw się w dwóch zdaniach."}
    ],
)

print(odpowiedz.content[0].text)
print()
print("Tokeny wejściowe:", odpowiedz.usage.input_tokens)
print("Tokeny wyjściowe:", odpowiedz.usage.output_tokens)