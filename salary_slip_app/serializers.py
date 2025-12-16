from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from core_app.models import *
from datetime import datetime
from django.utils.timezone import make_naive
from django.utils.timezone import now, make_naive,is_aware
from datetime import datetime, time


class SalarypdfSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryHistory
        fields = ['id', 'employee', 'pdf_file', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


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

