from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and search
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Ad management
    path('create/', views.create_ad, name='create_ad'),
    path('ad/<int:pk>/', views.ad_detail, name='ad_detail'),
    path('ad/<int:pk>/edit/', views.edit_ad, name='edit_ad'),
    path('ad/<int:pk>/delete/', views.delete_ad, name='delete_ad'),
    path('my-ads/', views.my_ads, name='my_ads'),
    
    # Categories
    path('category/<int:category_id>/', views.category_view, name='category'),
]