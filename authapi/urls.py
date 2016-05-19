from django.conf.urls import include, url
from rest_framework import routers

from authapi import views

router = routers.DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
