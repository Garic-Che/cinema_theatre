from django.contrib import admin
from django.urls import path, include

from . import settings

urlpatterns = [
    path('subs_admin/', admin.site.urls)
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
