import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from core_app.utils.react_crypto import *

class ReactCryptoMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.path == "/api/register-session-key/":
            return None
        if request.headers.get("X-Client", "").lower() != "react":
            return None

        decrypted, aes_key = decrypt_react_payload(request)
        request.react_aes_key = aes_key

        if decrypted:
            request._body = json.dumps(decrypted).encode()
            request.data = decrypted

        return None


    def process_response(self, request, response):
        if not hasattr(request, "react_aes_key") or request.react_aes_key is None:
            return response

        if not isinstance(response, JsonResponse):
            return response

        plain = json.loads(response.content.decode())
        encrypted = aes_gcm_encrypt(plain, request.react_aes_key)

        return JsonResponse(encrypted)
