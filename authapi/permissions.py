from restfw_composed_permissions.base import (
    BaseComposedPermision, BasePermissionComponent, And, Or, Not)
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
        return permissions.exists()


class AllowObjectPermission(AllowPermission):
    '''This component checks whether a user has a specific permission type,
    and that the object id matches the permission object id. A custom
    location to look for the object id can be specified by supplying a function
    to location, that takes in the object as a variable.'''
    def __init__(self, permission_type, location=None):
        self.permission_type = permission_type
        if location is None:
            self.location = self.get_pk
        else:
            self.location = location

    def get_pk(self, obj):
        return obj.pk

    def has_object_permission(self, permission, request, view, obj):
        user = request.user
        permissions = get_user_permissions(user)
        obj_id = self.location(obj)
        permissions = find_permission(
            permissions, self.permission_type, obj_id)
        return permissions.exists()


class AllowUpdate(BasePermissionComponent):
    '''Only allows PUT and PATCH requests.'''
    def has_permission(self, permission, request, view):
        return request.method in ('PUT', 'PATCH')


class AllowDelete(BasePermissionComponent):
    '''Only allows DELETE requests.'''
    def has_permission(self, permission, request, view):
        return request.method == 'DELETE'


AllowModify = Or(AllowUpdate, AllowDelete)


class AllowCreate(BasePermissionComponent):
    '''Only allows POST requests with no object.'''
    def has_permission(self, permission, request, view):
        return request.method == 'POST'


class AllowAdmin(BasePermissionComponent):
    '''
    This component will always allow admin users, and deny all other users.
    '''
    def has_permission(self, permission, request, view):
        return request.user.is_superuser


class ObjAttrTrue(BasePermissionComponent):
    '''
    This component will pass when the function 'attribute' returns true.
    The function is given (request, obj) as parameters. It will also pass
    all global permissions.
    '''
    def __init__(self, attribute):
        self.attribute = attribute

    def has_permission(self, permission, request, view):
        return self.attribute(request, None)

    def has_object_permission(self, permission, request, view, obj):
        return self.attribute(request, obj)


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


class OrganizationUsersPermission(BaseComposedPermision):
    '''Permissions for the OrganizationUsersViewSet.'''
    def global_permission_set(self):
        '''All users must be authenticated.'''
        return And(
            AllowOnlyAuthenticated,
            self.object_permission_set()
        )

    def object_permission_set(self):
        '''
        admins can add users to any organization. org:admin and org:write can
        add users to the organization that they are admin for.
        '''
        return Or(
            AllowOnlySafeHttpMethod,
            AllowAdmin,
            AllowObjectPermission('org:write'),
            AllowObjectPermission('org:admin')
        )


TeamCreatePermission = OrganizationUsersPermission


class TeamPermission(BaseComposedPermision):
    '''Permissions for the TeamViewSet.'''
    def global_permission_set(self):
        '''All users must be authenticated.'''
        return AllowOnlyAuthenticated

    def object_permission_set(self):
        '''
        admins, users with team:admin for the team, and users with org:admin,
        or org:write permission for the team's organization have full access
        to teams. Users with team:read permission for the team, or are a member
        of the team, or are a member of the team's organization, have read
        access to the team.
        '''
        return Or(
            AllowAdmin,
            AllowObjectPermission('team:admin'),
            AllowObjectPermission('org:admin', lambda t: t.organization_id),
            AllowObjectPermission('org:write', lambda t: t.organization_id),
            And(
                AllowOnlySafeHttpMethod,
                Or(
                    AllowObjectPermission('team:read'),
                    ObjAttrTrue(
                        lambda r, t: t.users.filter(pk=r.user.pk).exists()),
                    ObjAttrTrue(
                        lambda r, t: t.organization.users.filter(
                            pk=r.user.pk).exists())
                )
            )
        )


class UserPermission(BaseComposedPermision):
    '''Permissions for the UserViewSet.'''
    def global_permission_set(self):
        '''All users must be authenticated. Only admins can create other admin
        users.'''
        only_admins_create_admins = Or(
            AllowAdmin,
            And(
                ObjAttrTrue(lambda r, _: r.data.get('admin').lower() != 'true'),
                Or(
                    AllowPermission('user:create'),
                    AllowPermission('org:admin')
                )
            )
        )

        return And(
            AllowOnlyAuthenticated,
            Or(
                Not(AllowCreate),
                only_admins_create_admins
            )
        )

    def object_permission_set(self):
        '''All users have view permissions. Admin users, and users with
        org:admin can create, update, and delete any user. Any user can update
        or delete themselves. Users with user:create permission can create
        new users. Only admins can create or modify other admin users.'''
        return Or(
            AllowOnlySafeHttpMethod,
            AllowAdmin,
            And(
                AllowPermission('org:admin'),
                ObjAttrTrue(lambda _, u: not u.is_superuser),
                ObjAttrTrue(
                    lambda r, _: r.data.get('admin', '').lower() != 'true')
            ),
            And(
                AllowModify,
                ObjAttrTrue(
                    lambda req, user: user == req.user),
                ObjAttrTrue(
                    lambda r, _: r.data.get('admin', '').lower() != 'true')
            ),
        )
