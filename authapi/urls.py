from django.conf.urls import include, url
from rest_framework_extensions import routers

from authapi import views

router = routers.ExtendedSimpleRouter()

org_router = router.register(r'organizations', views.OrganizationViewSet)
team_router = router.register(r'teams', views.TeamViewSet)
router.register(r'users', views.UserViewSet)

org_router.register(
    r'users', views.OrganizationUsersViewSet,
    base_name='seedorganization-users',
    parents_query_lookups=['organization'])
orgteam_router = org_router.register(
    r'teams', views.OrganizationTeamViewSet,
    base_name='seedorganization-teams',
    parents_query_lookups=['organization'])

orgteam_router.register(
    r'permissions', views.TeamPermissionViewSet,
    base_name='seedorganization-teams-permissions',
    parents_query_lookups=['seedteam__organization', 'seedteam'])
orgteam_router.register(
    r'users', views.TeamUsersViewSet,
    base_name='seedorganization-teams-users',
    parents_query_lookups=['seedteam__organization', 'seedteam'])


team_router.register(
    r'permissions', views.TeamPermissionViewSet,
    base_name='seedteam-permissions',
    parents_query_lookups=['seedteam'])
team_router.register(
    r'users', views.TeamUsersViewSet,
    base_name='seedteam-users',
    parents_query_lookups=['seedteam'])

urlpatterns = [
    url(r'^', include(router.urls)),
]
