import os
import json
import time
import uuid
import secrets
import string
import hashlib
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Pfad zur JSON-Datei mit den Lizenzdaten
KEYS_FILE = "keys.json"

app = FastAPI(title="License Key API", description="API zur Verifizierung von Lizenzschlüsseln und HWID")

# CORS middleware konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In einer Produktionsumgebung einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statische Dateien einbinden
app.mount("/static", StaticFiles(directory="."), name="static")

# Datenmodelle
class VerifyRequest(BaseModel):
    username: str
    key: str
    hwid: str

class VerifyResponse(BaseModel):
    success: bool
    message: str
    username: Optional[str] = None
    hwid: Optional[str] = None

# Hilfsfunktion zum Laden der Lizenzdaten
def load_license_data() -> List[Dict[str, Any]]:
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w") as f:
            json.dump([], f)
        return []
    
    try:
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# Hilfsfunktion zum Speichern der Lizenzdaten
def save_license_data(data: List[Dict[str, Any]]):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_hwid(hwid: str) -> str:
    """Create a SHA-256 hash of the HWID"""
    return hashlib.sha256(hwid.encode()).hexdigest()

# API-Endpunkt für Schlüsselverifizierung
@app.post("/api/verify", response_model=VerifyResponse)
async def verify_key(request: VerifyRequest):
    username = request.username
    key = request.key
    hwid = request.hwid
    hwid_hash = hash_hwid(hwid)
    
    licenses = load_license_data()
    
    for license in licenses:
        if license["username"] == username and license["key"] == key:
            if "valid_until" in license:
                valid_until = time.strptime(license["valid_until"], "%Y-%m-%d %H:%M:%S")
                if time.time() > time.mktime(valid_until):
                    raise HTTPException(status_code=403, detail={
                        "success": False,
                        "message": "License has expired"
                    })
            
            if license.get("hwid_hash") == hwid_hash:
                return {
                    "success": True,
                    "message": "Key valid",
                    "username": username,
                    "hwid": hwid
                }
            elif not license.get("hwid_hash"):
                license["hwid"] = hwid
                license["hwid_hash"] = hwid_hash
                save_license_data(licenses)
                return {
                    "success": True,
                    "message": "Key valid and HWID registered",
                    "username": username,
                    "hwid": hwid
                }
            else:
                raise HTTPException(status_code=403, detail={
                    "success": False,
                    "message": "HWID mismatch - This key is already registered on another device"
                })
    
    raise HTTPException(status_code=401, detail={
        "success": False,
        "message": "Invalid key or username"
    })

# Serve static files
@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("dashboard.html")

@app.get("/admin")
async def admin():
    return FileResponse("admin.html")

# Standard-Route für die API-Dokumentation
@app.get("/api")
async def api_root():
    return {"message": "License Key API. See /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    
    # Erstelle die Lizenzdatei, falls sie nicht existiert
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w") as f:
            json.dump([], f)
        print(f"Leere Lizenzdatei '{KEYS_FILE}' erstellt.")
    
    # Starte den Server
    uvicorn.run(app, host="0.0.0.0", port=10000)
