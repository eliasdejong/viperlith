import os 
import asyncio
from cerebras.cloud.sdk import AsyncCerebras


client = AsyncCerebras(
	api_key=os.getenv("CEREBRAS_API_KEY"),
)

async def main() -> None:
	stream = await client.chat.completions.create(
		model="gpt-oss-120b",
		messages=[
			{
				"role": "user",
				"content": "Why is fast inference important?",
			}
		],
		stream=True,
	)
	chunks = []
	async for chunk in stream:
		print(chunk.model_dump_json(indent=2) or "", end="")
		# print(chunk.choices[0].delta.content or "", end="")
		# chunks.append(chunk.choices[0].delta.content or "")


asyncio.run(main())