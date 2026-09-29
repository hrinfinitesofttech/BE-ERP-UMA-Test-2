from rest_framework import serializers
from .models import (
    ApprovalItem,
    ERPAlertItem,
    Job360Overview,
    ExecutiveDashboardKPI,
    Customer360Summary,
    Supplier360Summary,
    ItemMaterial360Summary,
    Employee360Summary,
    GlobalActivityLog,
    ERPReportCenterItem,
    JobProfitabilityRecord,
)


class ApprovalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalItem
        fields = '__all__'


class ERPAlertItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERPAlertItem
        fields = '__all__'


class Job360OverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job360Overview
        fields = '__all__'


class ExecutiveDashboardKPISerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveDashboardKPI
        fields = '__all__'


class Customer360SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer360Summary
        fields = '__all__'


class Supplier360SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier360Summary
        fields = '__all__'


class ItemMaterial360SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMaterial360Summary
        fields = '__all__'


class Employee360SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee360Summary
        fields = '__all__'


class GlobalActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalActivityLog
        fields = '__all__'


class ERPReportCenterItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERPReportCenterItem
        fields = '__all__'


class JobProfitabilityRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobProfitabilityRecord
        fields = '__all__'
