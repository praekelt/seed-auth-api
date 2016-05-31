from restfw_composed_permissions.base import (
    BaseComposedPermision, BasePermissionComponent, And, Or)
from restfw_composed_permissions.generic.components import (
    AllowOnlyAuthenticated, AllowOnlySafeHttpMethod)

from authapi.utils import get_user_permissions, find_permission


class AllowPermission(BasePermissionComponent):
    '''
    This component checks whether a user has a specific permission type.
    '''
    def __init__(self, permission_type, object_id=None):
        self.permission_type = permission_type

    def has_permission(self, permission, request, view):
        user = request.user
        permissions = get_user_permissions(user)
        permissions = find_permission(permissions, self.permission_type)
        if permissions.count() >= 1:
            return True
        return False

    def has_object_permission(self, permission, request, view, obj):
        return self.has_permission(permission, request, view)


class AllowObjectPermission(AllowPermission):
    '''This component checks whether a user has a specific permission type,
    and that the object id matches the permission object id.'''
    def has_object_permission(self, permission, request, view, obj):
        user = request.user
        permissions = get_user_permissions(user)
        permissions = find_permission(
            permissions, self.permission_type, str(obj.pk))
        if permissions.count() >= 1:
            return True
        return False


class AllowAdmin(BasePermissionComponent):
    '''
    This component will always allow admin users, and deny all other users.
    '''
    def has_object_permission(self, permission, request, view, obj):
        return request.user.is_superuser

    def has_permission(self, permission, request, view):
        return request.user.is_superuser


class OrganizationPermission(BaseComposedPermision):
    '''Permissions for the OrganizationViewSet.'''
    def global_permission_set(self):
        '''All users can read, admins and org:admins can create.'''
        return And(
            AllowOnlyAuthenticated,
            Or(
                AllowOnlySafeHttpMethod,
                AllowAdmin,
                lambda _: AllowPermission('org:admin')
            )
        )

    def object_permission_set(self):
        '''
        All users can read, admins, org:admins, and users with org:write
        permission for the specific organization can update.'''
        return And(
            AllowOnlyAuthenticated,
            Or(
                AllowOnlySafeHttpMethod,
                AllowAdmin,
                lambda _: AllowPermission('org:admin'),
                lambda _: AllowObjectPermission('org:write')
            )
        )
