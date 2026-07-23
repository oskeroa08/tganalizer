
from groq import Groq
import asyncio


async def analyze_message(text: str, api_key: str) -> dict:
    if not api_key:
        return {
            "relevant": False,
            "reason": "API key not set"
        }

    try:
        client = Groq(api_key=api_key)
        loop = asyncio.get_event_loop()
        
        # Run synchronous Groq call in executor to not block
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a message analyzer. Analyze if the message is relevant to buying/selling items or is urgent. Respond in JSON format only with keys: 'relevant' (boolean) and 'reason' (short string)."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this message:\n{text}"
                    }
                ],
                model="llama3-8b-8192",
                response_format={"type": "json_object"}
            )
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"AI Analysis error: {e}")
        return {
            "relevant": False,
            "reason": str(e)
        }

