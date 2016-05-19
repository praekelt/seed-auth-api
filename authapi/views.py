from django.contrib.auth.models import User
from rest_framework import viewsets

from authapi.models import SeedOrganization, SeedTeam
from authapi.serializers import (
    OrganizationSerializer, TeamSerializer, UserSerializer)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = SeedOrganization.objects.all()
    serializer_class = OrganizationSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = SeedTeam.objects.all()
    serializer_class = TeamSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
