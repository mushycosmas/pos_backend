from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

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

from .serializers import (
    ReportTemplateSerializer,
    ReportScheduleSerializer,
    ReportHistorySerializer,
    DashboardWidgetSerializer,
    DashboardLayoutSerializer,
    ReportExportSerializer,
    ReportLogSerializer,
    ReportMetricSerializer
)


class ReportTemplateViewSet(ModelViewSet):
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [AllowAny]


class ReportScheduleViewSet(ModelViewSet):
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [AllowAny]


class ReportHistoryViewSet(ModelViewSet):
    queryset = ReportHistory.objects.all()
    serializer_class = ReportHistorySerializer
    permission_classes = [AllowAny]


class DashboardWidgetViewSet(ModelViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [AllowAny]


class DashboardLayoutViewSet(ModelViewSet):
    queryset = DashboardLayout.objects.all()
    serializer_class = DashboardLayoutSerializer
    permission_classes = [AllowAny]


class ReportExportViewSet(ModelViewSet):
    queryset = ReportExport.objects.all()
    serializer_class = ReportExportSerializer
    permission_classes = [AllowAny]


class ReportLogViewSet(ModelViewSet):
    queryset = ReportLog.objects.all()
    serializer_class = ReportLogSerializer
    permission_classes = [AllowAny]


class ReportMetricViewSet(ModelViewSet):
    queryset = ReportMetric.objects.all()
    serializer_class = ReportMetricSerializer
    permission_classes = [AllowAny]