from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response

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

    def get_queryset(self):
        '''We want to still directly manage deactivated users, but not show
        them on our list of users.'''
        if self.action == 'list':
            return User.objects.filter(is_active=True)
        return self.queryset

    def destroy(self, request, pk=None):
        '''For DELETE actions, actually deactivate the user, don't delete.'''
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
