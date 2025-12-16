# import json
# import base64
# import os
# from django.http import JsonResponse
# from django.utils.deprecation import MiddlewareMixin

# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_OAEP, AES
# from Crypto.Hash import SHA256
                             

# # Load the frontend PUBLIC KEY (for encrypting AES key)
# public_key = RSA.import_key(open("public.pem").read())
# rsa_cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)


# def aes_encrypt(plaintext: str):
#     aes_key = os.urandom(32)        # AES-256
#     aes = AES.new(aes_key, AES.MODE_GCM)

#     cipher_bytes, tag = aes.encrypt_and_digest(plaintext.encode())

#     return {
#         "aes_key": aes_key,
#         "cipher": base64.b64encode(cipher_bytes).decode(),
#         "nonce": base64.b64encode(aes.nonce).decode(),
#         "tag": base64.b64encode(tag).decode()
#     }


# def encrypt_response_payload(data_obj):
#     """
#     Takes Python dict/list → AES encrypts → RSA encrypts AES key.
#     Returns JSON-ready encrypted payload.
#     """

#     # Convert Python object → compact JSON string
#     json_text = json.dumps(data_obj, default=str, separators=(",", ":"))

#     aes_data = aes_encrypt(json_text)

#     encrypted_aes_key = rsa_cipher.encrypt(aes_data["aes_key"])

#     return {
#         "encrypted_key": base64.b64encode(encrypted_aes_key).decode(),
#         "cipher": aes_data["cipher"],
#         "nonce": aes_data["nonce"],
#         "tag": aes_data["tag"],
#     }

# response_crypto.py
# import base64
# import json
# from django.http import JsonResponse
# from Crypto.Cipher import AES
# import json
# import base64
# from django.http import JsonResponse
# from django.utils.deprecation import MiddlewareMixin

# def encrypt_response_with_aes(data, aes_key):
#     """Encrypt the DRF response payload using AES-GCM."""
#     json_text = json.dumps(data, default=str, separators=(",", ":")).encode()

#     cipher = AES.new(aes_key, AES.MODE_GCM)
#     ciphertext, tag = cipher.encrypt_and_digest(json_text)

#     return {
#         "cipher": base64.b64encode(ciphertext).decode(),
#         "nonce": base64.b64encode(cipher.nonce).decode(),
#         "tag": base64.b64encode(tag).decode(),
#     }
# class ResponseEncryptionMiddleware(MiddlewareMixin):
#     def process_response(self, request, response):
#         aes_key_b64 = request.session.get("aes_session_key")

#         if not aes_key_b64:  # No encryption for this session
#             return response

#         try:
#             aes_key = base64.b64decode(aes_key_b64)

#             if hasattr(response, "render"):
#                 response.render()

#             data = None
#             if hasattr(response, "data"):
#                 data = response.data
#             elif isinstance(response, JsonResponse):
#                 data = json.loads(response.content.decode())
#             else:
#                 return response

#             encrypted_payload = encrypt_response_with_aes(data, aes_key)

#             return JsonResponse(encrypted_payload, status=response.status_code, safe=True)

#         except Exception as e:
#             print("❌ AES Response Encryption Error:", e)
#             return response
        



# class ResponseEncryptionMiddleware(MiddlewareMixin):

#     def process_response(self, request, response):


#         content_type = response.headers.get("Content-Type", "")

#         # Only process JSON responses
#         if not content_type.startswith("application/json"):
#             return response

#         try:
#             # Render DRF responses if needed
#             if hasattr(response, "render"):
#                 response.render()
    
#             # Extract JSON payload
#             if hasattr(response, "data"):
#                 original_data = response.data
#             elif isinstance(response, JsonResponse):
#                 original_data = json.loads(response.content.decode())
#             else:
#                 return response

#             # Encrypt JSON payload
#             encrypted_payload = encrypt_response_payload(original_data)

#             return JsonResponse(
#                 encrypted_payload,
#                 status=response.status_code,
#                 safe=True
#             )

#         except Exception as e:
#             print("Response encryption error:", e)
#             return response

# class ResponseEncryptionMiddleware(MiddlewareMixin):
#     def process_response(self, request, response):
#         # Only encrypt JSON responses
#         content_type = response.headers.get("Content-Type", "")
#         if not content_type.startswith("application/json"):
#             return response

#         aes_key_b64 = request.session.get("aes_session_key")
#         if not aes_key_b64:
#             # No AES key registered, return response as-is
#             return response

#         try:
#             aes_key = base64.b64decode(aes_key_b64)

#             # Render DRF response if needed
#             if hasattr(response, "render"):
#                 response.render()

#             # Extract JSON data
#             if hasattr(response, "data"):
#                 data = response.data
#             elif isinstance(response, JsonResponse):
#                 data = json.loads(response.content.decode())
#             else:
#                 return response

#             # Convert to JSON string
#             json_text = json.dumps(data, default=str, separators=(",", ":")).encode()

#             # AES-GCM encryption
#             cipher = AES.new(aes_key, AES.MODE_GCM)
#             ciphertext, tag = cipher.encrypt_and_digest(json_text)

#             # Send encrypted payload
#             encrypted_payload = {
#                 "cipher": base64.b64encode(ciphertext).decode(),
#                 "nonce": base64.b64encode(cipher.nonce).decode(),
#                 "tag": base64.b64encode(tag).decode()
#             }

#             return JsonResponse(encrypted_payload, status=response.status_code, safe=True)

#         except Exception as e:
#             print("AES encryption middleware error:", e)
#             return response



# corrected code last
import json
import base64
import os
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256, SHA1



# Load the frontend PUBLIC KEY (for encrypting AES key)
public_key = RSA.import_key(open("public.pem").read())
rsa_cipher_sha256 = PKCS1_OAEP.new(public_key , hashAlgo=SHA256)
rsa_cipher_sha1 = PKCS1_OAEP.new(public_key , hashAlgo=SHA1)


def aes_encrypt(plaintext: str):
    aes_key = os.urandom(32)     
    aes = AES.new(aes_key, AES.MODE_GCM)

    cipher_bytes, tag = aes.encrypt_and_digest(plaintext.encode())

    return {
        "aes_key": aes_key,
        "cipher": base64.b64encode(cipher_bytes).decode(),
        "nonce": base64.b64encode(aes.nonce).decode(),
        "tag": base64.b64encode(tag).decode()
    }


def encrypt_response_payload(data_obj, use_sha256=True):

    json_text = json.dumps(data_obj, default=str, separators=(",", ":"))
    aes_data = aes_encrypt(json_text)

    # AES key to encrypt
    aes_key = aes_data["aes_key"]

    # React uses SHA-256 → so default to SHA-256
    if use_sha256:
        encrypted_aes_key = rsa_cipher_sha256.encrypt(aes_key)
    else:
        encrypted_aes_key = rsa_cipher_sha1.encrypt(aes_key)

    return {
        "encrypted_key": base64.b64encode(encrypted_aes_key).decode(),
        "cipher": aes_data["cipher"],
        "nonce": aes_data["nonce"],
        "tag": aes_data["tag"],
    }
class ResponseEncryptionMiddleware(MiddlewareMixin):

    def process_response(self, request, response):

        # Only encrypt if the view explicitly requests it
        if not getattr(response, "encrypt_payload", False):
            return response

        content_type = response.headers.get("Content-Type", "")

        if not content_type.startswith("application/json"):
            return response

        try:
            if hasattr(response, "render"):
                response.render()

            if hasattr(response, "data"):
                original_data = response.data
            elif isinstance(response, JsonResponse):
                original_data = json.loads(response.content.decode())
            else:
                return response

            encrypted_payload = encrypt_response_payload(original_data)

            return JsonResponse(
                encrypted_payload,
                status=response.status_code,
                safe=True
            )

        except Exception as e:
            print("Response encryption error:", e)
            return response


