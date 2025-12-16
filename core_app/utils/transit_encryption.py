
import base64
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256



private_key = RSA.import_key(open("private.pem").read())
rsa_cipher = PKCS1_OAEP.new(private_key , hashAlgo=SHA256)

def rsa_decrypt_key(encrypted_key):
    return rsa_cipher.decrypt(base64.b64decode(encrypted_key))

def aes_decrypt(cipher, nonce, tag, aes_key):
    aes = AES.new(aes_key, AES.MODE_GCM, nonce=base64.b64decode(nonce))
    plain = aes.decrypt_and_verify(
        base64.b64decode(cipher),
        base64.b64decode(tag)
    )
    return plain.decode()

def decrypt_request_payload(request):
    """
    Extracts encrypted payload (JSON only) and returns decrypted dict.
    Image in multipart is NOT encrypted.
    """
    encrypted_key = request.data.get("encrypted_key")
    cipher = request.data.get("cipher")
    nonce = request.data.get("nonce")
    tag = request.data.get("tag")

    if not all([encrypted_key, cipher, nonce, tag]):
        return None

    try:
        aes_key = rsa_decrypt_key(encrypted_key)
        decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
        return json.loads(decrypted_json)

    except Exception as e:
        print("Decryption Error:", str(e))
        return None
    
# crypto_utils.py
# import base64
# import json
# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_OAEP, AES
# from Crypto.Hash import SHA256

# # Load backend private RSA key (to decrypt AES key sent by frontend)
# private_key = RSA.import_key(open("private.pem").read())
# rsa_cipher_private = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)

# def rsa_decrypt_key(encrypted_key_b64: str) -> bytes:
#     """Decrypt AES key sent by frontend using RSA private key."""
#     encrypted_bytes = base64.b64decode(encrypted_key_b64)
#     return rsa_cipher_private.decrypt(encrypted_bytes)

# def aes_decrypt(cipher: str, nonce: str, tag: str, aes_key: bytes) -> str:
#     """AES-GCM decrypt a request payload."""
#     aes = AES.new(aes_key, AES.MODE_GCM, nonce=base64.b64decode(nonce))
#     plaintext = aes.decrypt_and_verify(
#         base64.b64decode(cipher),
#         base64.b64decode(tag)
#     )
#     return plaintext.decode()

# def decrypt_request_payload(request):
#     """Decrypt encrypted API request JSON body."""
#     aes_key_b64 = request.session.get("aes_session_key")
#     if not aes_key_b64:
#         return None  # request not encrypted

#     aes_key = base64.b64decode(aes_key_b64)

#     cipher = request.data.get("cipher")
#     nonce = request.data.get("nonce")
#     tag = request.data.get("tag")

#     if not all([cipher, nonce, tag]):
#         return None

#     try:
#         decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
#         return json.loads(decrypted_json)
#     except Exception as e:
#         print("❌ AES Request Decryption Error:", e)
#         return None



# import base64
# import json
# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_OAEP, AES
# from Crypto.Hash import SHA256

# # Load private key once
# private_key = RSA.import_key(open("private.pem").read())
# rsa_cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)


# def rsa_decrypt_key(encrypted_key):
#     """
#     Decrypt AES key using RSA private key
#     """
#     encrypted_bytes = base64.b64decode(encrypted_key)
#     return rsa_cipher.decrypt(encrypted_bytes)


# def aes_decrypt(cipher, nonce, tag, aes_key):
#     """
#     AES GCM decrypt response or request
#     """
#     aes = AES.new(aes_key, AES.MODE_GCM, nonce=base64.b64decode(nonce))
#     plain = aes.decrypt_and_verify(
#         base64.b64decode(cipher),
#         base64.b64decode(tag)
#     )
#     return plain.decode()



# def decrypt_request_payload(request):
#     """
#     Decrypt AES encrypted JSON request using stored session key.
#     """
#     # Get stored AES key
#     aes_key_b64 = request.session.get("aes_session_key")
#     if not aes_key_b64:
#         return None  # No encryption on this request

#     # Convert Base64 → bytes
#     aes_key = base64.b64decode(aes_key_b64)

#     cipher = request.data.get("cipher")
#     nonce = request.data.get("nonce")
#     tag = request.data.get("tag")

#     if not all([cipher, nonce, tag]):
#         return None

#     try:
#         decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
#         return json.loads(decrypted_json)
#     except Exception as e:
#         print("AES Request Decryption Failed:", str(e))
#         return None
