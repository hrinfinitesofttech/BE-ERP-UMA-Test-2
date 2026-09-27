from rest_framework import serializers
from .models import (
    ManufacturingJob, ProductionPlan, WorkCenter, RoutingOperation,
    WorkOrder, ProductionOrder, ProductionScheduleItem, ProductionEntry,
    WIPRecord, ProductionHold, ReworkOrder, ProductionScrap, FinishedGoodsItem
)


class ManufacturingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingJob
        fields = '__all__'


class ProductionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionPlan
        fields = '__all__'


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = '__all__'


class RoutingOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingOperation
        fields = '__all__'


class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'


class ProductionOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrder
        fields = '__all__'


class ProductionScheduleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionScheduleItem
        fields = '__all__'


class ProductionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionEntry
        fields = '__all__'


class WIPRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WIPRecord
        fields = '__all__'


class ProductionHoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionHold
        fields = '__all__'


class ReworkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReworkOrder
        fields = '__all__'


class ProductionScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionScrap
        fields = '__all__'


class FinishedGoodsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishedGoodsItem
        fields = '__all__'
