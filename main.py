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
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

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

class AddKeyRequest(BaseModel):
    username: str
    key: str
    hwid: Optional[str] = ""

class DeleteKeyRequest(BaseModel):
    key: str

class ResetHWIDRequest(BaseModel):
    key: str

class License(BaseModel):
    username: str
    key: str
    hwid: str
    created_at: Optional[str] = None

class LicenseListResponse(BaseModel):
    success: bool
    count: int
    licenses: List[License]

class GenerateKeyRequest(BaseModel):
    username: str
    days_valid: Optional[int] = 30  # Optional validity period in days

# Hilfsfunktion zum Laden der Lizenzdaten
def load_license_data() -> List[Dict[str, Any]]:
    if not os.path.exists(KEYS_FILE):
        # Erstelle leere Datei, wenn nicht vorhanden
        with open(KEYS_FILE, "w") as f:
            json.dump([], f)
        return []
    
    try:
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Bei fehlerhafter JSON-Datei leere Liste zurückgeben
        return []

# Hilfsfunktion zum Speichern der Lizenzdaten
def save_license_data(data: List[Dict[str, Any]]):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Fehlerhandler für ungültiges JSON
@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": "Ungültiges JSON-Format"}
    )

def generate_secure_key(length: int = 29) -> str:
    """Generate a secure license key in format XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-X"""
    alphabet = string.ascii_uppercase + string.digits
    key_parts = []
    
    # Generate 7 groups of 4 characters
    for i in range(7):
        if i == 6:  # Last group is only 1 character
            part = ''.join(secrets.choice(alphabet) for _ in range(1))
        else:
            part = ''.join(secrets.choice(alphabet) for _ in range(4))
        key_parts.append(part)
    
    return '-'.join(key_parts)

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
    
    # Lizenzdaten laden
    licenses = load_license_data()
    
    # Nach übereinstimmendem Benutzer und Schlüssel suchen
    for license in licenses:
        if license["username"] == username and license["key"] == key:
            # Prüfen ob die Lizenz abgelaufen ist
            if "valid_until" in license:
                valid_until = time.strptime(license["valid_until"], "%Y-%m-%d %H:%M:%S")
                if time.time() > time.mktime(valid_until):
                    raise HTTPException(status_code=403, detail={
                        "success": False,
                        "message": "License has expired"
                    })
            
            # Prüfen, ob die HWID übereinstimmt
            if license.get("hwid_hash") == hwid_hash:
                return {
                    "success": True,
                    "message": "Key valid",
                    "username": username,
                    "hwid": hwid
                }
            elif not license.get("hwid_hash"):
                # HWID registrieren, wenn noch keine gesetzt ist
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
                # HWID stimmt nicht überein
                raise HTTPException(status_code=403, detail={
                    "success": False,
                    "message": "HWID mismatch - This key is already registered on another device"
                })
    
    # Kein passender Schlüssel gefunden
    raise HTTPException(status_code=401, detail={
        "success": False,
        "message": "Invalid key or username"
    })

# Admin-API-Endpunkt zum Hinzufügen neuer Lizenzen
@app.post("/api/admin/add_key")
async def add_key(request: AddKeyRequest):
    # Hier sollte in einer produktiven Umgebung eine Admin-Authentifizierung sein
    
    username = request.username
    key = request.key
    hwid = request.hwid
    
    # Lizenzdaten laden
    licenses = load_license_data()
    
    # Prüfen, ob der Schlüssel bereits existiert
    for license in licenses:
        if license["key"] == key:
            raise HTTPException(status_code=409, detail={
                "success": False,
                "message": "Key already exists"
            })
    
    # Neuen Schlüssel hinzufügen
    new_license = {
        "username": username,
        "key": key,
        "hwid": hwid,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    licenses.append(new_license)
    save_license_data(licenses)
    
    return {
        "success": True,
        "message": "License key added successfully",
        "license": new_license
    }

# Admin-API-Endpunkt zum Auflisten aller Lizenzen
@app.get("/api/admin/list_keys", response_model=LicenseListResponse)
async def list_keys():
    # Hier sollte in einer produktiven Umgebung eine Admin-Authentifizierung sein
    
    licenses = load_license_data()
    return {
        "success": True,
        "count": len(licenses),
        "licenses": licenses
    }

# Admin-API-Endpunkt zum Löschen einer Lizenz
@app.post("/api/admin/delete_key")
async def delete_key(request: DeleteKeyRequest):
    # Hier sollte in einer produktiven Umgebung eine Admin-Authentifizierung sein
    
    key_to_delete = request.key
    
    # Lizenzdaten laden
    licenses = load_license_data()
    initial_count = len(licenses)
    
    # Schlüssel filtern
    licenses = [license for license in licenses if license["key"] != key_to_delete]
    
    if len(licenses) < initial_count:
        save_license_data(licenses)
        return {
            "success": True,
            "message": f"License key '{key_to_delete}' deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail={
            "success": False,
            "message": f"License key '{key_to_delete}' not found"
        })

# Admin-API-Endpunkt zum Zurücksetzen einer HWID
@app.post("/api/admin/reset_hwid")
async def reset_hwid(request: ResetHWIDRequest):
    # Hier sollte in einer produktiven Umgebung eine Admin-Authentifizierung sein
    
    key_to_reset = request.key
    
    # Lizenzdaten laden
    licenses = load_license_data()
    
    # Nach Schlüssel suchen und HWID zurücksetzen
    for license in licenses:
        if license["key"] == key_to_reset:
            license["hwid"] = ""
            save_license_data(licenses)
            return {
                "success": True,
                "message": f"HWID for key '{key_to_reset}' reset successfully"
            }
    
    raise HTTPException(status_code=404, detail={
        "success": False,
        "message": f"License key '{key_to_reset}' not found"
    })

# Admin-API-Endpunkt zum Generieren eines neuen Schlüssels
@app.post("/api/admin/generate_key")
async def generate_key(request: GenerateKeyRequest):
    # Hier sollte in einer produktiven Umgebung eine Admin-Authentifizierung sein
    
    username = request.username
    
    # Generiere einen neuen, eindeutigen Schlüssel
    while True:
        new_key = generate_secure_key()
        licenses = load_license_data()
        if not any(license["key"] == new_key for license in licenses):
            break
    
    # Erstelle neue Lizenz
    new_license = {
        "username": username,
        "key": new_key,
        "hwid": "",
        "hwid_hash": "",  # Will be set when HWID is first registered
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "valid_until": time.strftime("%Y-%m-%d %H:%M:%S", 
                                   time.localtime(time.time() + request.days_valid * 86400))
    }
    
    # Füge die neue Lizenz hinzu
    licenses.append(new_license)
    save_license_data(licenses)
    
    return {
        "success": True,
        "message": "License key generated successfully",
        "license": new_license
    }

# Neuer Endpunkt zum Abrufen der HWID einer Lizenz
@app.get("/api/copy_hwid/{key}")
async def copy_hwid(key: str):
    licenses = load_license_data()
    
    for license in licenses:
        if license["key"] == key:
            return {
                "success": True,
                "hwid": license.get("hwid", ""),
                "username": license["username"]
            }
    
    raise HTTPException(status_code=404, detail={
        "success": False,
        "message": "License key not found"
    })

# Serve static files (wie in deiner aktuellen main.py)
@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("dashboard.html")

@app.get("/admin")
async def admin():
    return FileResponse("admin.html")

if __name__ == "__main__":
    import uvicorn
    
    # Erstelle die Lizenzdatei, falls sie nicht existiert
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w") as f:
            json.dump([], f)
        print(f"Leere Lizenzdatei '{KEYS_FILE}' erstellt.")
    
    # Starte den Server
    uvicorn.run(app, host="0.0.0.0", port=10000)
