from fastapi import FastAPI

app = FastAPI()

@app.post("/webhook")
async def receive_webhook():
    return {"message": "Hello World"}
