# API Protection Layer: Rate Limiting & Backpressure

This project implements an advanced API protection layer using FastAPI. It uses the Token Bucket algorithm to manage traffic efficiently while preventing server overloads.

## Features implemented:
1. **Rate Limiting**: Limits requests per identifier (e.g., User ID or IP).
2. **Backpressure (Queue/Delay)**: Slightly overloaded requests are safely queued and delayed using `asyncio.sleep()`.
3. **Backpressure (Reject)**: If the system gets massively bombarded and the virtual queue becomes too long (greater than max accepted delay), it short-circuits and rejects requests with a `429 Too Many Requests`.
4. **Logging**: Native python logging handles throttled and delayed requests gracefully.
5. **Modular Design**: Uses an Abstract Base Class (`RateLimiterStorage`) making it extremely easy to plug in Redis for distributed tracking across multiple server nodes.

## How to run the application

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the API Server:
   ```bash
   uvicorn main:app --reload
   ```

3. Open a separate terminal and run the load-test to see the limiter in action:
   ```bash
   python test_client.py
   ```

Watch the API Server terminal. You will see traffic flowing, then being dynamically delayed (backpressure implemented via async wait), and finally being rejected with logs indicating an overloaded queue.
