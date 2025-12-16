from django.db import models
from rest_framework import serializers
from core_app.models import SalaryComponent
# Create your models here.



class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = [
            "id",
            "component_type",
            "title",
            "rate_type",
            "rate_value",
            "description",
            "employee_contribution",
            "employer_contribution",
            "example_text",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]