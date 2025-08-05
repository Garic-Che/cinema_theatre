from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Mailing, MessageTemplate
from .serializers import MailingSerializer, MessageTemplateSerializer
import requests
from django.conf import settings


class MessageTemplateViewSet(viewsets.ModelViewSet):
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(created_by=self.request.user)


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def send_now(self, request, pk=None):
        mailing = self.get_object()
        from .tasks import send_mailing

        send_mailing.delay(mailing.id)
        return Response({"status": "Рассылка запущена"})

    @action(detail=False, methods=["get"])
    def users(self, request):
        # Получаем список пользователей из сервиса аутентификации
        auth_response = requests.get(
            f"{settings.AUTH_SERVICE['URL']}/api/users/",
            headers={"Authorization": f"Bearer {request.auth}"},
        )

        if auth_response.status_code == 200:
            return Response(auth_response.json())
        return Response(
            {"error": "Не удалось получить список пользователей"},
            status=auth_response.status_code,
        )
