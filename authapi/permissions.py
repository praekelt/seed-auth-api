from django.conf import settings
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission
from restfw_composed_permissions.base import (
    BaseComposedPermision, BasePermissionComponent, And, Or, Not)
from restfw_composed_permissions.generic.components import (
    AllowOnlyAuthenticated, AllowOnlySafeHttpMethod)

from authapi.utils import get_user_permissions, find_permission
from authapi.models import SeedTeam


class AllowPermission(BasePermissionComponent):
    '''
    This component checks whether a user has a specific permission type.
    '''
    def __init__(self, permission_type):
        self.permission_type = permission_type

    def has_permission(self, permission, request, view):
        user = request.user
        permissions = get_user_permissions(user)
        permissions = find_permission(
            permissions, self.permission_type,
            namespace=settings.PERMISSION_NAMESPACE)
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
            permissions, self.permission_type, obj_id,
            settings.PERMISSION_NAMESPACE)
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
    '''Only allows POST requests.'''
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
    The function is given (request, obj) as parameters. obj may be None for
    global permission views.
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
        All users can read. admins and org:admins with permission for the
        specific organization can update. admins can create.
        '''
        return Or(
            AllowOnlySafeHttpMethod,
            AllowAdmin,
            And(
                AllowModify,
                Or(
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
        admins can add users to any organization. org:admin can add users to
        the organization that they are admin for.
        '''
        return Or(
            AllowOnlySafeHttpMethod,
            AllowAdmin,
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
        team's organization have full access to teams. Users who are a member
        of the team, or are a member of the team's organization, have read
        access to the team.
        '''
        return Or(
            AllowAdmin,
            AllowObjectPermission('team:admin'),
            AllowObjectPermission('org:admin', lambda t: t.organization_id),
            And(
                AllowOnlySafeHttpMethod,
                Or(
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
                ObjAttrTrue(
                    lambda r, _: r.data.get('admin') is not True),
                Or(
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
        or delete themselves. Only admins can create or modify other admin
        users.'''
        return Or(
            AllowOnlySafeHttpMethod,
            AllowAdmin,
            And(
                AllowPermission('org:admin'),
                ObjAttrTrue(lambda _, u: not u.is_superuser),
                ObjAttrTrue(
                    lambda r, _: r.data.get('admin') is not True)
            ),
            And(
                AllowModify,
                ObjAttrTrue(
                    lambda req, user: user == req.user),
                ObjAttrTrue(
                    lambda r, _: r.data.get('admin') is not True)
            ),
        )


class TeamPermissionPermission(BasePermission):
    '''Permissions for adding or removing permissions from teams.'''
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.method == 'POST':
            return self.handle_create(request)
        if request.method == 'DELETE':
            # We don't need to do any checks at the view level, only at the
            # object level.
            return True

    def has_object_permission(self, request, view, obj):
        return self.handle_delete(request, obj)

    def user_has_permission(self, user, permission_type, object_id=None):
        permissions = get_user_permissions(user)
        permissions = find_permission(
            permissions, permission_type, object_id,
            settings.PERMISSION_NAMESPACE)
        return permissions.exists()

    def check_permissions(self, user, ptype, object_id, namespace):
        if namespace != settings.PERMISSION_NAMESPACE:
            return True
        if user.is_superuser:
            return True
        if ptype == 'org:admin':
            return self.user_has_permission(user, ptype, object_id)
        elif ptype == 'team:admin':
            if self.user_has_permission(user, 'team:admin', object_id):
                return True
            org_id = get_object_or_404(SeedTeam, pk=object_id).organization_id
            return self.user_has_permission(user, 'org:admin', org_id)
        else:
            return True

    def handle_create(self, request):
        user = request.user
        ptype = request.data.get('type')
        object_id = request.data.get('object_id')
        namespace = request.data.get('namespace')
        return self.check_permissions(user, ptype, object_id, namespace)

    def handle_delete(self, request, obj):
        user = request.user
        ptype = obj.type
        object_id = obj.object_id
        namespace = obj.namespace
        return self.check_permissions(user, ptype, object_id, namespace)
