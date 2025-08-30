from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from django.urls import path, include

from . import views

router = DefaultRouter()

router.register('register', views.RegisterView, basename='register')
router.register('', views.UserProfileView, basename='profile')
router.register('login', views.LoginView, basename='login')
router.register('forgot-password', views.ForgotPasswordView, basename='forgot-password')
router.register('reset-password', views.ResetPasswordView, basename='reset-password')


urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]