from django.db import models


class Chat(models.Model):
    """
    Model representing a chat message from a user.
    """

    user_request = models.TextField(null=False, blank=True)
