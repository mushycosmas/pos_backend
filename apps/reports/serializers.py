from rest_framework import serializers
from .models import (
    ReportTemplate,
    ReportSchedule,
    ReportHistory,
    DashboardWidget,
    DashboardLayout,
    ReportExport,
    ReportLog,
    ReportMetric
)


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'


class ReportScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSchedule
        fields = '__all__'


class ReportHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportHistory
        fields = '__all__'


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = '__all__'


class DashboardLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardLayout
        fields = '__all__'


class ReportExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportExport
        fields = '__all__'


class ReportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportLog
        fields = '__all__'


class ReportMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportMetric
        fields = '__all__'