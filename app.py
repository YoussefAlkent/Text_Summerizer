import os, asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(
    api_key = os.getenv("GROQ_API_KEY")
)

print("Connection Established with Groq")

full_text = input("What prompt do you want to Summarize ?\n")

to_summarize=f"Prompt to Summarize : {full_text}"

message_content="You're an English Langauge Specialist. You will get a text paragraph, Your job is to shorten that Paragraph, make sure that all the main points are articulated, but do not add any more information than available to you. You should not output anything else but the summarized text.\n\n"

async def firstRequest() -> None:
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": (message_content + to_summarize)
            }
        ],
        model=os.getenv("MODEL_NAME")
    )
    print(chat_completion.choices[0].message.content)
    f = open("output.txt", "a")
    f.write(chat_completion.choices[0].message.content)
    f.close()

asyncio.run(firstRequest())
