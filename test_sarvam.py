import asyncio
import httpx
import json
import config

async def test():
    headers = {
        "Authorization": f"Bearer {config.SARVAM_API_KEY}",
        "api-subscription-key": config.SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.SARVAM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Keep your answers very short."},
            {"role": "user", "content": "Hello"}
        ],
        "temperature": 0.1,
        "max_tokens": 8192
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            config.SARVAM_BASE_URL,
            headers=headers,
            json=payload
        )
        print("Status code:", response.status_code)
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)

asyncio.run(test())
