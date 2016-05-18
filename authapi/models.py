from django.contrib.auth.models import User
from django.db import models


class SeedOrganization(models.Model):
    # TODO: Implement SeedOrganization model
    users = models.ManyToManyField(User)


class SeedPermission(models.Model):
    # TODO: Implement SeedPermission model
    pass


class SeedTeam(models.Model):
    # TODO: Implement SeedTeam model
    organization = models.ForeignKey(SeedOrganization)
    users = models.ManyToManyField(User)
    permissions = models.ManyToManyField(SeedPermission)
