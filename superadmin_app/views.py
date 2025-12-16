from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core_app.models import *
from django.db.models import Count


# Create your views here.
class SuperadminEmployeeDesignationCountView(APIView):
    """
    Returns count of INACTIVE employees grouped by their designation.
    Example response:
    {
      "success": true,
      "total_inactive_employees": 4,
      "data": [
        {"designation": "Software Engineer", "employee_count": 3},
        {"designation": "HR Manager", "employee_count": 1}
      ]
    }
    """

    def get(self, request):
        # Query inactive employees grouped by designation
        data = (
            EmployeeDetail.objects
            .filter(user__is_active=False)
            .values('designation')
            .annotate(employee_count=Count('id'))
            .order_by('designation')
        )

        # Handle null or blank designations
        formatted_data = [
            {
                "designation": item['designation'] if item['designation'] else "Not Assigned",
                "employee_count": item['employee_count']
            }
            for item in data
        ]

        # ✅ Calculate total inactive employee count
        total_inactive = sum(item['employee_count'] for item in formatted_data)

        # ✅ Include success flag and total count in response
        return Response(
            {
                "success": True,
                "total_inactive_employees": total_inactive,
                "data": formatted_data
            },
            status=status.HTTP_200_OK
        )