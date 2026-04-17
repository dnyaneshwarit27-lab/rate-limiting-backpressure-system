import asyncio
import httpx
import time

URL = "http://127.0.0.1:8000/"

async def fetch(client, index):
    start_time = time.time()
    try:
        response = await client.get(URL)
        duration = time.time() - start_time
        print(f"Request {index:02d}: {response.status_code:<4} | Took {duration:.2f}s")
        return response.status_code
    except Exception as e:
        print(f"Request {index:02d}: Failed - {e}")
        return 0

async def main():
    async with httpx.AsyncClient() as client:
        print("====== Sending 15 concurrent requests ======\n")
        
        # Fire 15 requests concurrently to hammer the API
        tasks = [fetch(client, i) for i in range(15)]
        results = await asyncio.gather(*tasks)
        
        # Summarize results
        success = results.count(200)
        rejected = results.count(429)
        
        print("\n====== Summary ======")
        print(f"Successful processes (200 OK): {success} (some may have been transparently delayed)")
        print(f"Rejected requests   (429)   : {rejected} (dropped entirely due to backpressure)")

if __name__ == "__main__":
    asyncio.run(main())
