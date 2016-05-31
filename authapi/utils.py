from authapi.models import SeedPermission


def get_user_permissions(user):
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


def find_permission(permissions, permission_type, object_id=None):
    '''Given a queryset of permissions, filters depending on the permission
    type, and optionally an object id.'''
    if object_id is not None:
        return permissions.filter(type=permission_type, object_id=object_id)
    return permissions.filter(type=permission_type)
