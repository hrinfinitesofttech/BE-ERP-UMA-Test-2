from rest_framework import serializers
from .models import ApprovalItem, ERPAlertItem


class ApprovalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalItem
        fields = '__all__'


class ERPAlertItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERPAlertItem
        fields = '__all__'
