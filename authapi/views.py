from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import viewsets, status, serializers
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.request import clone_request
from rest_framework.response import Response
from rest_framework.mixins import (
    DestroyModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin,
    ListModelMixin)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from authapi.models import SeedOrganization, SeedTeam, SeedPermission
from authapi import permissions
from authapi.serializers import (
    OrganizationSerializer, TeamSerializer, UserSerializer, NewUserSerializer,
    PermissionSerializer, CreateTokenSerializer, PermissionsUserSerializer)


def get_true_false_both(query_params, field_name, default):
    '''Tries to get and return a valid of true, false, or both from the field
    name in the query string, raises a ValidationError for invalid values.'''
    valid = ('true', 'false', 'both')
    value = query_params.get(field_name, default).lower()
    if value in valid:
        return value
    v = ', '.join(sorted(valid))
    raise serializers.ValidationError({
        field_name: ['Must be one of [%s]' % v],
    })


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = SeedOrganization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (permissions.OrganizationPermission,)

    def get_queryset(self):
        '''We want to still be able to modify archived organizations, but they
        shouldn't show up on list views.

        We have an archived query param, where 'true' shows archived, 'false'
        omits them, and 'both' shows both.'''
        if self.action == 'list':
            archived = get_true_false_both(
                self.request.query_params, 'archived', 'false')
            if archived == 'true':
                return self.queryset.filter(archived=True)
            if archived == 'false':
                return self.queryset.filter(archived=False)
        return self.queryset

    def destroy(self, request, pk=None):
        '''For DELETE actions, archive the organization, don't delete.'''
        org = self.get_object()
        org.archived = True
        org.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationUsersViewSet(NestedViewSetMixin, viewsets.ViewSet):
    '''Nested viewset that allows users to add or remove users from
    organizations.'''
    permission_classes = (permissions.OrganizationUsersPermission,)

    def update(self, request, pk=None, parent_lookup_organization=None):
        '''Add a user to an organization.'''
        user = get_object_or_404(User, pk=pk)
        org = get_object_or_404(
            SeedOrganization, pk=parent_lookup_organization)
        self.check_object_permissions(request, org)
        org.users.add(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None, parent_lookup_organization=None):
        '''Remove a user from an organization.'''
        user = get_object_or_404(User, pk=pk)
        org = get_object_or_404(
            SeedOrganization, pk=parent_lookup_organization)
        self.check_object_permissions(request, org)
        org.users.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseTeamViewSet(
        NestedViewSetMixin, RetrieveModelMixin, UpdateModelMixin,
        DestroyModelMixin, ListModelMixin, GenericViewSet):
    queryset = SeedTeam.objects.all()
    serializer_class = TeamSerializer
    permission_classes = (permissions.TeamPermission,)

    def get_queryset(self):
        '''We want to still be able to modify archived organizations, but they
        shouldn't show up on list views.

        We have an archived query param, where 'true' shows archived, 'false'
        omits them, and 'both' shows both.

        We also have the query params permission_contains and object_id, which
        allow users to filter the teams based on the permissions they
        contain.'''
        queryset = super(BaseTeamViewSet, self).get_queryset()
        if self.action == 'list':
            archived = get_true_false_both(
                self.request.query_params, 'archived', 'false')
            if archived == 'true':
                queryset = queryset.filter(archived=True)
            elif archived == 'false':
                queryset = queryset.filter(archived=False)

            permission = self.request.query_params.get(
                'permission_contains', None)
            if permission is not None:
                queryset = queryset.filter(
                    permissions__type__contains=permission).distinct()

            object_id = self.request.query_params.get('object_id', None)
            if object_id is not None:
                queryset = queryset.filter(
                    permissions__object_id=object_id).distinct()

            namespace = self.request.query_params.get('namespace', None)
            if namespace is not None:
                queryset = queryset.filter(
                    permissions__namespace=namespace).distinct()

            permission = permissions.TeamPermission()
            queryset = [
                team for team in queryset if
                permission.has_object_permission(self.request, self, team)]

        return queryset

    def perform_destroy(self, instance):
        instance.archived = True
        instance.save()


class TeamViewSet(BaseTeamViewSet):
    pass


class OrganizationTeamViewSet(BaseTeamViewSet, CreateModelMixin):
    def create(self, request, parent_lookup_organization=None):
        org = get_object_or_404(
            SeedOrganization, pk=parent_lookup_organization)
        permission = permissions.TeamCreatePermission()
        if not permission.has_object_permission(request, self, org):
            self.permission_denied(
                request, message=getattr(permission, 'message', None)
            )
        request.data['organization'] = org.pk

        return super(OrganizationTeamViewSet, self).create(request)


class TeamPermissionViewSet(
        NestedViewSetMixin, DestroyModelMixin, GenericViewSet):
    '''Nested viewset to add and remove permissions from teams.'''
    queryset = SeedPermission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (permissions.TeamPermissionPermission,)

    def check_team_permissions(self, request, teamid, orgid=None):
        if orgid is not None:
            team = get_object_or_404(
                SeedTeam, pk=teamid, organization_id=orgid)
        else:
            team = get_object_or_404(SeedTeam, pk=teamid)

        permission = permissions.TeamPermission()
        fake_request = clone_request(request, 'GET')
        if not permission.has_object_permission(fake_request, self, team):
            self.permission_denied(
                request, message=getattr(permission, 'message', None)
            )
        return team

    def create(
            self, request, parent_lookup_seedteam=None,
            parent_lookup_seedteam__organization=None):
        '''Add a permission to a team.'''
        team = self.check_team_permissions(
            request, parent_lookup_seedteam,
            parent_lookup_seedteam__organization)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = team.permissions.create(**serializer.validated_data)
        serializer = self.get_serializer(instance=permission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(
            self, request, pk=None, parent_lookup_seedteam=None,
            parent_lookup_seedteam__organization=None):
        '''Remove a permission from a team.'''
        self.check_team_permissions(
            request, parent_lookup_seedteam,
            parent_lookup_seedteam__organization)
        return super(TeamPermissionViewSet, self).destroy(
            request, pk, parent_lookup_seedteam,
            parent_lookup_seedteam__organization)


class TeamUsersViewSet(NestedViewSetMixin, GenericViewSet):
    '''Nested viewset that allows users to add or remove users from teams.'''
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def check_team_permissions(self, request, teamid, orgid=None):
        if orgid is not None:
            team = get_object_or_404(
                SeedTeam, pk=teamid, organization_id=orgid)
        else:
            team = get_object_or_404(SeedTeam, pk=teamid)

        permission = permissions.TeamPermission()
        fake_request = clone_request(request, 'PUT')
        if not permission.has_object_permission(fake_request, self, team):
            self.permission_denied(
                request, message=getattr(permission, 'message', None)
            )
        return team

    def update(
            self, request, pk=None, parent_lookup_seedteam=None,
            parent_lookup_seedteam__organization=None):
        '''Add a user to a team.'''
        user = get_object_or_404(User, pk=pk)
        team = self.check_team_permissions(
            request, parent_lookup_seedteam,
            parent_lookup_seedteam__organization)
        team.users.add(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(
            self, request, pk=None, parent_lookup_seedteam=None,
            parent_lookup_seedteam__organization=None):
        '''Remove a user from an organization.'''
        user = self.get_object()
        team = self.check_team_permissions(
            request, parent_lookup_seedteam,
            parent_lookup_seedteam__organization)
        team.users.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (permissions.UserPermission,)

    def get_serializer_class(self):
        if self.action == 'create':
            return NewUserSerializer
        else:
            return UserSerializer

    def get_queryset(self):
        '''We want to still be able to modify archived users, but they
        shouldn't show up on list views.

        We have an archived query param, where 'true' shows archived, 'false'
        omits them, and 'both' shows both.'''
        if self.action == 'list':
            active = get_true_false_both(
                self.request.query_params, 'active', 'true')
            if active == 'true':
                return self.queryset.filter(is_active=True)
            if active == 'false':
                return self.queryset.filter(is_active=False)
        return self.queryset

    def destroy(self, request, pk=None):
        '''For DELETE actions, actually deactivate the user, don't delete.'''
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        '''Create a token, given an email and password. Removes all other
        tokens for that user.'''
        serializer = CreateTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = authenticate(username=email, password=password)
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response(
            status=status.HTTP_201_CREATED, data={'token': token.key})


class UserPermissionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''Get user information, with a list of permissions for that user.'''
        user = request.user
        serializer = PermissionsUserSerializer(
            instance=user, context={'request': request})
        return Response(data=serializer.data)
