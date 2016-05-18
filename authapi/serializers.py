from django.contrib.auth.models import User
from rest_framework import serializers

from authapi.models import SeedOrganization, SeedTeam, SeedPermission


class OrganizationSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SeedOrganization
        fields = ('id', 'url')


class UserSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url')


class TeamSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SeedTeam
        fields = ('id', 'url')


class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SeedPermission


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    teams = TeamSummarySerializer(
        many=True, source='seedteam_set', read_only=True)
    users = UserSummarySerializer(many=True, read_only=True)

    class Meta:
        model = SeedOrganization
        fields = ('id', 'url', 'teams', 'users')


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    users = UserSummarySerializer(many=True, read_only=True)
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = SeedTeam
        fields = ('id', 'permissions', 'users', 'url', 'organization')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    teams = TeamSummarySerializer(
        many=True, source='seedteam_set', read_only=True)
    organizations = OrganizationSummarySerializer(
        many=True, source='seedorganization_set', read_only=True)
    email = serializers.EmailField(source='username')
    admin = serializers.BooleanField(source='is_superuser')

    class Meta:
        model = User
        fields = (
            'id', 'url', 'first_name', 'last_name', 'email', 'admin', 'teams',
            'organizations')
