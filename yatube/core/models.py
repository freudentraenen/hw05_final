from django.db import models
from django.utils import timezone
from django.utils.timezone import make_aware


class CreatedModel(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    class Meta:
        abstract = True
