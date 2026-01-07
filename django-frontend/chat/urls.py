# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 페이지 
    path('', views.login_page, name='login'), # 메인 페이지는 로그인
    path('chat/', views.chat_page, name='chat'), # 채팅 페이지
    
    # 인증 API
    path('api/register/', views.register_view, name='register'),
    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),
    path('api/user-status/', views.user_status, name='user_status'),
    
    # 채팅 API - 이미 있음! ✅
    path('api/chat/', views.chat_api, name='chat_api'),  # 👈 여기!
    path('api/health/', views.health_check, name='health'),
    
    # 채팅 기록 관리
    path('api/history/', views.get_chat_history, name='chat_history'),
    path('api/sessions/', views.get_session_list, name='session_list'),
    path('api/new-session/', views.new_session, name='new_session'),
]