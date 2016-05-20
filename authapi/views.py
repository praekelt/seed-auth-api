from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from authapi.models import SeedOrganization, SeedTeam
from authapi.serializers import (
    OrganizationSerializer, TeamSerializer, UserSerializer,
    OrganizationUserSerializer)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = SeedOrganization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        '''We want to still be able to modify archived organizations, but they
        shouldn't show up on list views.'''
        if self.action == 'list':
            return SeedOrganization.objects.filter(archived=False)
        return self.queryset

    def destroy(self, request, pk=None):
        '''For DELETE actions, archive the organization, don't delete.'''
        org = self.get_object()
        org.archived = True
        org.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationUsersViewSet(viewsets.ViewSet):
    '''Nested viewset that allows users to add or remove users from
    organizations.'''
    def create(self, request, organization_pk=None):
        '''Add a user to an organization.'''
        serializer = OrganizationUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, pk=serializer.data['user_id'])
        org = get_object_or_404(SeedOrganization, pk=organization_pk)
        org.users.add(user)
        org.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None, organization_pk=None):
        '''Remove a user from an organization.'''
        user = get_object_or_404(User, pk=pk)
        org = get_object_or_404(SeedOrganization, pk=organization_pk)
        org.users.remove(user)
        org.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = SeedTeam.objects.all()
    serializer_class = TeamSerializer

    def get_queryset(self):
        '''Add query parameters permission_contains and object_id.'''
        if self.action == 'list':
            queryset = SeedTeam.objects.filter(archived=False)
        else:
            queryset = self.queryset

        permission = self.request.query_params.get('permission_contains', None)
        if permission is not None:
            # TODO: Implement when permissions are implemented
            pass

        object_id = self.request.query_params.get('object_id', None)
        if object_id is not None:
            # TODO: Implement when permissions are implemented.
            pass

        return queryset

    def destroy(self, request, pk=None):
        team = self.get_object()
        team.archived = True
        team.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
