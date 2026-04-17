from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
from rate_limiter import APIRateLimiter, InMemoryStorage

app = FastAPI(title="API Protection Layer", description="Rate Limiting & Backpressure handling")

# 1. Initialize Storage Backend (Can be swapped with Redis in production)
storage = InMemoryStorage()

# 2. Configure Rate Limiter:
#   - capacity: 5 tokens max burst
#   - refill_rate: 2 tokens per second
#   - max_delay: 2.0s maximum acceptable queue delay
rate_limiter = APIRateLimiter(storage=storage, capacity=5.0, refill_rate=2.0, max_delay=2.0)

@app.middleware("http")
async def enforce_backpressure_and_rate_limit(request: Request, call_next):
    # Using client IP as a unique identifier (Can use user token/jwt in real apps)
    client_ip = request.client.host if request.client else "unknown"
    
    # 3. Check limitations
    state = await rate_limiter.check_limit(client_ip)
    
    # If the delay is too long (queue overloaded), reject request early
    if not state.allowed:
        return JSONResponse(
            status_code=429, 
            content={
                "error": "Too Many Requests", 
                "message": "System is experiencing heavy load. Request rejected due to capacity."
            }
        )
        
    # If a delay was issued, apply backpressure delay (Queueing mechanism)
    if state.delay > 0:
        await asyncio.sleep(state.delay)
        
    # Process the actual request after passing the protection layer
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"message": "Success! Request processed normally."}

@app.get("/data")
async def data():
    # Simulating standard workload
    await asyncio.sleep(0.05)
    return {"data": "Protected valuable data payload"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

