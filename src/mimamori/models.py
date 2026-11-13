import secrets
import uuid
 
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Greatest, Least
from django.utils import timezone
# Create your models here.


def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)

class Photo(models.Model):
    # who_id = models.IntegerField()
    posted_user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            default=None
    )
    image = models.ImageField(upload_to='photos/')
    created_at = models.DateTimeField(default=timezone.now)
    task = models.ForeignKey(
        "notifications.NotificationSetting",
        on_delete=models.CASCADE,
        related_name="photos",
        null=True,
        blank=True
    )


FRIEND_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
 
class Invitation(models.Model):
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    token = models.CharField(
        max_length=64, unique=True, default=generate_invitation_token, editable=False
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = "invitations"
 
    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()


class PairRelationship(models.Model):
    a_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="a_links",
    )
    b_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="b_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = "pair_relationships"
        constraints = [
            models.UniqueConstraint(
                Least("a_user", "b_user"),
                Greatest("a_user", "b_user"),
                name="pair_relationship_unique",
            ),
            models.CheckConstraint(
                condition=~Q(a_user=F("b_user")),
                name="pair_relationship_no_self",
            ),
    ]
 