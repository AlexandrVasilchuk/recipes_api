from typing import Callable

from django.db import models
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsOwner(BasePermission):
    """Only author have access for update/delete."""

    def has_object_permission(
        self, request: Request, view: Callable, obj: models.Model,
    ) -> bool:
        return request.method in SAFE_METHODS or obj.author == request.user
