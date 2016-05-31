from restfw_composed_permissions.base import (
    BaseComposedPermision, BasePermissionComponent, And, Or)
from restfw_composed_permissions.generic.components import (
    AllowOnlyAuthenticated, AllowOnlySafeHttpMethod)

from authapi.utils import get_user_permissions, find_permission


class AllowPermission(BasePermissionComponent):
    '''
    This component checks whether a user has a specific permission type.
    '''
    def __init__(self, permission_type):
        self.permission_type = permission_type

    def has_permission(self, permission, request, view):
        user = request.user
        permissions = get_user_permissions(user)
        permissions = find_permission(permissions, self.permission_type)
        return permissions.count() >= 1


class AllowObjectPermission(AllowPermission):
    '''This component checks whether a user has a specific permission type,
    and that the object id matches the permission object id.'''
    def has_object_permission(self, permission, request, view, obj):
        user = request.user
        permissions = get_user_permissions(user)
        permissions = find_permission(
            permissions, self.permission_type, str(obj.pk))
        return permissions.count() >= 1


class AllowUpdate(BasePermissionComponent):
    '''Only allows PUT and PATCH requests.'''
    def has_permission(self, permission, request, view):
        return request.method in ('PUT', 'PATCH')


class AllowDelete(BasePermissionComponent):
    '''Only allows DELETE requests.'''
    def has_permission(self, permission, request, view):
        return request.method == 'DELETE'


AllowModify = Or(AllowUpdate, AllowDelete)


class AllowAdmin(BasePermissionComponent):
    '''
    This component will always allow admin users, and deny all other users.
    '''
    def has_permission(self, permission, request, view):
        return request.user.is_superuser


class OrganizationPermission(BaseComposedPermision):
    '''Permissions for the OrganizationViewSet.'''
    def global_permission_set(self):
        '''All users must be authenticated.'''
        return And(
            AllowOnlyAuthenticated,
            self.object_permission_set()
        )

    def object_permission_set(self):
        '''
        All users can read. admins, org:admins, and users with org:write
        permission for the specific organization can update. admins can create.
        '''
        return Or(
            AllowOnlySafeHttpMethod,
            AllowAdmin,
            And(
                AllowModify,
                Or(
                    AllowObjectPermission('org:write'),
                    AllowObjectPermission('org:admin'),
                )
            )
        )
