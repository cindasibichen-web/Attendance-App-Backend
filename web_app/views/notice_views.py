from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from web_app.serializers import *
from core_app.models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from core_app.models import *
from core_app.utils.encrypt_decrypt_data import *
from core_app.utils.transit_encryption import *



class NoticeListCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET -> list all notices (pinned first)
    def get(self, request):
        notices = Notice.objects.all().order_by('-is_pinned', '-created_at')
        serializer = NoticeSerializer(notices, many=True)

        return Response({
            "success": True,
            "message": "Notices fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # POST -> create notice
    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
            
        serializer = NoticeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)

            return Response({
                "success": True,
                "message": "Notice created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
        
        
class NoticeDeleteAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        try:
            notice = Notice.objects.get(pk=pk)
        except Notice.DoesNotExist:
            return Response({
                "success": False,
                "message": "Notice not found"
            }, status=status.HTTP_404_NOT_FOUND)

        notice.delete()

        return Response({
            "success": True,
            "message": "Notice deleted successfully"
        }, status=status.HTTP_200_OK)
        
        
        
class NoticeUpdateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        try:
            notice = Notice.objects.get(pk=pk)
        except Notice.DoesNotExist:
            return Response({
                "success": False,
                "message": "Notice not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = NoticeSerializer(notice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Notice updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)