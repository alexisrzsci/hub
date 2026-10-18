#!/usr/bin/env python3
"""Encrypt / decrypt Alexis Hub data.

Usage (key comes from the HUB_KEY environment variable):
  python3 hub/tools/hubcrypt.py decrypt hub/data.enc.json  > state.json
  python3 hub/tools/hubcrypt.py encrypt state.json hub/data.enc.json

state.json shape: {"daily": {...}, "jobs": {...}}
Format: AES-256-GCM, key from PBKDF2-HMAC-SHA256 (250000 iterations, random 16-byte salt).
Needs: pip install cryptography
"""
import base64, json, os, sys, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 250000


def _key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER)
    return kdf.derive(passphrase.encode())


def encrypt(passphrase: str, data: dict) -> dict:
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_key(passphrase, salt)).encrypt(iv, json.dumps(data, ensure_ascii=False).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct),
            "stamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}


def decrypt(passphrase: str, blob: dict) -> dict:
    d = base64.b64decode
    key = _key(passphrase, d(blob["salt"]))
    return json.loads(AESGCM(key).decrypt(d(blob["iv"]), d(blob["ct"]), None))


if __name__ == "__main__":
    passphrase = os.environ.get("HUB_KEY")
    if not passphrase:
        sys.exit("Set HUB_KEY")
    mode = sys.argv[1]
    if mode == "decrypt":
        print(json.dumps(decrypt(passphrase, json.load(open(sys.argv[2]))), ensure_ascii=False, indent=1))
    elif mode == "encrypt":
        blob = encrypt(passphrase, json.load(open(sys.argv[2])))
        json.dump(blob, open(sys.argv[3], "w"))
    else:
        sys.exit("mode must be encrypt or decrypt")
