from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
  path("", views.Home.as_view(), name="home"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("resources/", views.ResourceListView.as_view(), name="resource_list"),
    path('resources/<int:resource_id>/', views.resource_detail, name='resource-detail'),
    path("resources/add/", views.ResourceCreateView.as_view(), name="resource_create"),
    path(
        "resources/edit/<int:pk>/",
        views.ResourceUpdateView.as_view(),
        name="resource_update",
    ),
    path(
        "resources/delete/<int:pk>/",
        views.ResourceDeleteView.as_view(),
        name="resource_delete",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
]
