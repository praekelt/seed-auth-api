from django.contrib.auth.models import User
from django.db import models


class SeedOrganization(models.Model):
    name = models.CharField(max_length=64)
    users = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)


class SeedPermission(models.Model):
    permission_type = models.CharField(max_length=128)
    object_id = models.CharField(max_length=64)
    namespace = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)


class SeedTeam(models.Model):
    name = models.CharField(max_length=64)
    organization = models.ForeignKey(SeedOrganization)
    users = models.ManyToManyField(User)
    permissions = models.ManyToManyField(SeedPermission)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
