from fastapi import Request, HTTPException
from app.core.qstash import receiver
async def verify_qstash_request(request: Request):
    signature = request.headers.get("Upstash-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing QStash signature")
    body = await request.body()
    try:
        receiver.verify(
            body=body,
            signature=signature,
            url=str(request.url),  # optional but recommended
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid QStash signature")

    # Optional: return payload so handler can use it
    return body