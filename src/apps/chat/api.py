from rest_framework import permissions, viewsets

from .models import Chat
from .serializers import ChatSerializer


class ChatViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Chat objects to be
    viewed, created, edited or deleted.
    """

    queryset = Chat.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = ChatSerializer
