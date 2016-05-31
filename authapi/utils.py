from authapi.models import SeedPermission


def get_user_permissions(self, user):
    '''Returns the queryset of permissions for the given user.'''
    permissions = SeedPermission.objects.all()
    # User must be on a team that grants the permission
    permissions = permissions.filter(seedteam__users=user)
    # The team must be active
    permissions = permissions.filter(seedteam__archived=False)
    # The organization of that team must be active
    permissions = permissions.filter(
        seedteam__organization__archived=False)
    return permissions
