import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from shazamio import Shazam

API_KEY = os.getenv("API_KEY", "")
app = FastAPI(title="Shazam Proxy")

def _check_auth(x_api_key):
    if not API_KEY:
        return True
    return x_api_key == API_KEY

@app.get("/")
async def root():
    return {"status": "ok", "service": "shazam-proxy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/recognize")
async def recognize(file: UploadFile = File(...), x_api_key: str = Header(None, alias="X-API-Key")):
    if not _check_auth(x_api_key):
        raise HTTPException(401, "unauthorized")
    content = await file.read()
    if not content:
        raise HTTPException(400, "empty file")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "too large")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        shazam = Shazam()
        result = await shazam.recognize(tmp_path)
        return {"ok": True, "result": result}
    except Exception as e:
        print(f"[ERR] {type(e).__name__}: {e}")
        return {"ok": False, "error": str(e)[:300]}
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
