# worksheets/views.py
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
from web_app.serializers import *
from django.shortcuts import get_object_or_404
from core_app.models import *

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

class WorksheetListCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET - List all worksheets
    def get(self, request):
        worksheets = Worksheet.objects.all().order_by('-uploaded_at')
        serializer = WorksheetSerializer(worksheets, many=True)

        return Response({
            "success": True,
            "message": "Worksheet list fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # POST - Upload new worksheet
    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
                print("Decrypted Request:", decrypted_data)
                # Replace request.data with decrypted version
                data = decrypted_data
        else:
                print("Normal  Request:", request.data)
                data = request.data
        serializer = WorksheetSerializer(data=data)

        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response({
                "success": True,
                "message": "Worksheet uploaded successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
        
        
class WorksheetAllListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        worksheets = Worksheet.objects.all().order_by('-uploaded_at')
        serializer = WorksheetSerializer(worksheets, many=True)

        return Response({
            "success": True,
            "message": "All worksheets fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
        
        
class WorksheetDeleteAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            worksheet = Worksheet.objects.get(id=pk)
        except Worksheet.DoesNotExist:
            return Response({
                "success": False,
                "message": "Worksheet not found"
            }, status=status.HTTP_404_NOT_FOUND)

        worksheet.delete()

        return Response({
            "success": True,
            "message": "Worksheet deleted successfully"
        }, status=status.HTTP_200_OK)  
        
        
class WorksheetTitleUpdateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
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
            worksheet = Worksheet.objects.get(id=pk)
        except Worksheet.DoesNotExist:
            return Response({
                "success": False,
                "message": "Worksheet not found"
            }, status=status.HTTP_404_NOT_FOUND)

        new_title = request.data.get("title")
        if not new_title:
            return Response({
                "success": False,
                "message": "Title field is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        worksheet.title = new_title
        worksheet.save(update_fields=["title"])

        return Response({
            "success": True,
            "message": "Worksheet title updated successfully"
        }, status=status.HTTP_200_OK)
    
    #training video add , list 
class TrainingVideoUploadAPIView(APIView):

    def post(self, request):
        serializer = TrainingVideoSerializer(data=request.data)

        if serializer.is_valid():
            video = serializer.save(uploaded_by=request.user)

            return Response({
                "success": True,
                "message": "Video uploaded successfully",
                "data": TrainingVideoSerializer(video).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
class TrainingVideoListAPIView(APIView):

    def get(self, request):
        videos = TrainingVideo.objects.all().order_by('-uploaded_at')
        serializer = TrainingVideoSerializer(videos, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
 # TARINING VIDEOS  edit delete 
class TrainingVideosEditDeletAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]   
    def patch(self, request, pk):
      
        
        training_video = TrainingVideo.objects.get(id=pk)  
        serializer = TrainingVideoSerializer(training_video, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Training video",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        

    def delete(self, request, pk):
        training_video = get_object_or_404(TrainingVideo, id=pk)

        training_video.delete()

        return Response({
            "success": True,
            "message": "Training video deleted successfully"
        }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_shifts(request):
    shifts = ShiftTable.objects.all().order_by("id")
    serializer = ShiftviewSerializer(shifts, many=True)

    return Response(
        {"status": "success", "shifts": serializer.data},
        status=status.HTTP_200_OK
    )      
    
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_shift(request, pk):
    try:
        shift = ShiftTable.objects.get(pk=pk)
    except ShiftTable.DoesNotExist:
        return Response(
            {"status": "error", "message": "Shift not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    shift.delete()

    return Response(
        {"status": "success", "message": "Shift deleted successfully"},
        status=status.HTTP_200_OK,
    )


class TrainingVideoUploadAPIView(APIView):

    def post(self, request):
        serializer = TrainingVideoSerializer(data=request.data)

        if serializer.is_valid():
            video = serializer.save(uploaded_by=request.user)

            return Response({
                "success": True,
                "message": "Video uploaded successfully",
                "data": TrainingVideoSerializer(video).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
class TrainingVideoListAPIView(APIView):

    def get(self, request):
        videos = TrainingVideo.objects.all().order_by('-uploaded_at')
        serializer = TrainingVideoSerializer(videos, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
        
#  Create , list , update  and delete  questions form for the polls and reviews
class FeedbackQuestionFormCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):
        question_forms = Form.objects.prefetch_related(
            'questions__options'
        ).all().order_by('-created_at')

        serializer = FormSerializer(question_forms, many=True)

        return Response({
            "success": True,
            "message": "Question forms fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

   
    def post(self, request):
        serializer = FormSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save() 
            return Response({
                "success": True,
                "message": "Question form created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        
        return Response({
            "success": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

        



# EDIT DELETE FEEDBACK QUESTIONS 
class EditDeleteFeedbackQuestionFormAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        try:
            question_form = Form.objects.get(id=pk)
        except Form.DoesNotExist:
            return Response({
                "success": False,
                "message": "Question form not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = FormSerializer(question_form, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Question form updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)  

    def delete(self , request , pk):
             form = Form.objects.get(id=pk)
             form.delete()
             return Response({
                    "success": True,
                    "message": "Question form deleted successfully"
                }, status=status.HTTP_200_OK)
             
  # shift add on - shift edit section                
class ShiftaddonListCreate(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        shifts = Shiftaddon.objects.all()
        serializer = ShiftaddonSerializer(shifts, many=True)
        return Response({"success": True, "message" : "Shifts add on listed successfully","data": serializer.data})

    def post(self, request):
        serializer = ShiftaddonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)        


# edit and delete shift
class ShiftaddonEditDelete(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, pk):
        try:
            shift_addon = Shiftaddon.objects.get(id=pk)
        except Shiftaddon.DoesNotExist:
            return Response({"success": False, "message": "Shift add-on not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ShiftaddonSerializer(shift_addon, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            shift_addon = Shiftaddon.objects.get(id=pk)
        except Shiftaddon.DoesNotExist:
            return Response({"success": False, "message": "Shift add-on not found"}, status=status.HTTP_404_NOT_FOUND)

        shift_addon.delete()
        return Response({"success": True, "message": "Shift add-on deleted successfully"}, status=status.HTTP_200_OK)

# delete shift api 
class ShiftDeleteAPIView(APIView):
    def delete(self, request, id):
        try:
            shift = ShiftTable.objects.get(id=id)
            shift.delete()
            return Response(
                {"message": "Shift deleted successfully"},
                status=status.HTTP_200_OK
            )
        except ShiftTable.DoesNotExist:
            return Response(
                {"error": "Shift not found"},
                status=status.HTTP_404_NOT_FOUND
            )



