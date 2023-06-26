from django.db import models


class DefaultModel(models.Model):
    """Абстрактная базовая модель для всех моделей проекта."""

    class Meta:
        abstract = True
        ordering = ('id',)
