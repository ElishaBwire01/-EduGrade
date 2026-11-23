from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    """Custom user model — replaces django.contrib.auth.User.

    Explicit related_name on groups/user_permissions prevents E304 clashes
    with auth.User if Django ever loads both models (e.g. during migration).
    """
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='customuser_groups',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='customuser_permissions',
        related_query_name='customuser',
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.get_full_name() or self.username
