from django.db import models


class DefaultModel(models.Model):
    """Абстрактная базовая модель для всех объектов проекта"""

    class Meta:
        abstract = True


# class TimestampedModel(DefaultModel, Timestamped):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._meta.get_field('created').verbose_name = 'дата создания'
#         self._meta.get_field('author').verbose_name = 'автор'
#
#     class Meta:
#         abstract = True