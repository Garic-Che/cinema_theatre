from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponse


def test_view(request):
    return HttpResponse("Django работает!")


urlpatterns = [
    path("notifications_admin/", admin.site.urls),
    path("notifications_admin/test/", test_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
