from rest_framework.routers import DefaultRouter

from .views import (
    ReportTemplateViewSet,
    ReportScheduleViewSet,
    ReportHistoryViewSet,
    DashboardWidgetViewSet,
    DashboardLayoutViewSet,
    ReportExportViewSet,
    ReportLogViewSet,
    ReportMetricViewSet,
)


router = DefaultRouter()


router.register(
    'report-templates',
    ReportTemplateViewSet
)

router.register(
    'report-schedules',
    ReportScheduleViewSet
)

router.register(
    'report-history',
    ReportHistoryViewSet
)

router.register(
    'dashboard-widgets',
    DashboardWidgetViewSet
)

router.register(
    'dashboard-layouts',
    DashboardLayoutViewSet
)

router.register(
    'report-exports',
    ReportExportViewSet
)

router.register(
    'report-logs',
    ReportLogViewSet
)

router.register(
    'report-metrics',
    ReportMetricViewSet
)


urlpatterns = router.urls