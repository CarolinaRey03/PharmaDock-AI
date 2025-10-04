from rest_framework import serializers

from .models import Chat


class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer for the Chat model.
    Converts Chat model instances to JSON
    and validates incoming data.
    """

    class Meta:
        model = Chat
        fields = "__all__"
