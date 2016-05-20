from django.contrib.auth.models import User
from rest_framework import serializers

from authapi.models import SeedOrganization, SeedTeam, SeedPermission


class OrganizationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedOrganization
        fields = ('id', 'url')


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url')


class TeamSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedTeam
        fields = ('id', 'url')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedPermission


class OrganizationSerializer(serializers.ModelSerializer):
    teams = TeamSummarySerializer(
        many=True, source='seedteam_set', read_only=True)
    users = UserSummarySerializer(many=True, read_only=True)

    class Meta:
        model = SeedOrganization
        fields = ('id', 'url', 'teams', 'users')


class TeamSerializer(serializers.ModelSerializer):
    users = UserSummarySerializer(many=True, read_only=True)
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = SeedTeam
        fields = ('id', 'permissions', 'users', 'url', 'organization')


class UserSerializer(serializers.ModelSerializer):
    teams = TeamSummarySerializer(
        many=True, source='seedteam_set', read_only=True)
    organizations = OrganizationSummarySerializer(
        many=True, source='seedorganization_set', read_only=True)
    email = serializers.EmailField()
    admin = serializers.BooleanField(source='is_superuser', required=False)
    password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)
    active = serializers.BooleanField(default=True, source='is_active')

    class Meta:
        model = User
        fields = (
            'id', 'url', 'first_name', 'last_name', 'email', 'admin', 'teams',
            'organizations', 'password', 'active')

    def create(self, validated_data):
        '''We want to set the username to be the same as the email, and use the
        correct create function to make use of password hashing.'''
        validated_data['username'] = validated_data['email']
        admin = validated_data.pop('is_superuser', None)

        if admin is True:
            user = User.objects.create_superuser(**validated_data)
        else:
            user = User.objects.create_user(**validated_data)

        return user

    def update(self, instance, validated_data):
        '''We want to set all the required fields if admin is set, and we want
        to use the password hashing method if password is set.'''
        admin = validated_data.pop('is_superuser', None)
        password = validated_data.pop('password', None)
        if validated_data.get('email') is not None:
            validated_data['username'] = validated_data['email']

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if admin is not None:
            instance.is_staff = admin
            instance.is_superuser = admin
        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance
