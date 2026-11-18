from django.urls import path
from accounts.views import (
    CSRFTokenView,
    LoginView,
    LogoutView,
    CurrentUserView,
    ChangePasswordView,
    UserManagementViewSet,
    AuditLogListView,
)

user_list = UserManagementViewSet.as_view({'get': 'list', 'post': 'create'})
user_detail = UserManagementViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

urlpatterns = [
    path('csrf/', CSRFTokenView.as_view(), name='csrf-token'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('users/', user_list, name='user-list'),
    path('users/<int:pk>/', user_detail, name='user-detail'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit-logs'),
]
