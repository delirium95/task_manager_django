from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Worker
from users.models import Profile

User = get_user_model()


@receiver(post_save, sender=Worker)
def create_profile(instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
