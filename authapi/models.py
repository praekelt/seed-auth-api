from django.contrib.auth.models import User
from django.db import models


class SeedOrganization(models.Model):
    title = models.TextField()
    users = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)

    def get_active_teams(self):
        return self.seedteam_set.filter(archived=False)

    def get_active_users(self):
        return self.users.filter(is_active=True)


class SeedPermission(models.Model):
    type = models.TextField()
    object_id = models.TextField(null=True)
    namespace = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SeedTeam(models.Model):
    title = models.TextField()
    organization = models.ForeignKey(SeedOrganization)
    users = models.ManyToManyField(User)
    permissions = models.ManyToManyField(SeedPermission)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)

    def get_active_users(self):
        return self.users.filter(is_active=True)
