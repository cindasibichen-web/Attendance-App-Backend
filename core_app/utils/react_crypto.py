import json
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Load RSA PRIVATE KEY
private_key = RSA.import_key(open("private.pem").read())
rsa_cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)


# -------------------------------------------------------------------
# RSA KEY DECRYPT
# -------------------------------------------------------------------
def rsa_decrypt_key(encrypted_key: str) -> bytes:
    encrypted_bytes = base64.b64decode(encrypted_key)
    return rsa_cipher.decrypt(encrypted_bytes)


# -------------------------------------------------------------------
# AES-GCM DECRYPT (React → Django)
# -------------------------------------------------------------------
def aes_gcm_decrypt(cipher: str, nonce: str, tag: str, key: bytes):

    cipher_bytes = base64.b64decode(cipher)
    nonce_bytes = base64.b64decode(nonce)
    tag_bytes = base64.b64decode(tag)

    aes = AES.new(key, AES.MODE_GCM, nonce=nonce_bytes)
    plain = aes.decrypt_and_verify(cipher_bytes, tag_bytes)

    return json.loads(plain.decode())


# -------------------------------------------------------------------
# AES-GCM ENCRYPT (Django → React)
# -------------------------------------------------------------------
def aes_gcm_encrypt(data: dict, key: bytes):
    plaintext = json.dumps(data).encode()
    nonce = get_random_bytes(12)

    aes = AES.new(key, AES.MODE_GCM, nonce=nonce)

    ciphertext, tag = aes.encrypt_and_digest(plaintext)

    return {
        "cipher": base64.b64encode(ciphertext).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
    }


# -------------------------------------------------------------------
# PROCESS INCOMING PAYLOAD FROM REACT
# -------------------------------------------------------------------
def decrypt_react_payload(request):
    try:
        data = json.loads(request.body.decode() or "{}")
    except:
        data = {}

    cipher = data.get("cipher")
    nonce = data.get("nonce")
    tag = data.get("tag")
    encrypted_key = data.get("encrypted_key")

    if not cipher or not nonce or not tag:
        return None, None

    try:
        if encrypted_key:
            aes_key = rsa_decrypt_key(encrypted_key)
        else:
            key_b64 = request.session.get("aes_session_key")
            if not key_b64:
                print("No AES key found in session!")
                return None, None

            aes_key = base64.b64decode(key_b64)

        decrypted = aes_gcm_decrypt(cipher, nonce, tag, aes_key)
        return decrypted, aes_key

    except Exception as e:
        print("React Decryption FAILED:", e)
        return None, None
