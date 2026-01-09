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
    
    # 채팅 내역 페이지
    path('my-chats/', views.my_chats, name='my_chats'),
    
    # 마이페이지
    path('mypage/', views.my_page, name='mypage'),
    path('business-plans/', views.business_plan_list, name='business_plan_list'),
    path('business-plans/create/', views.business_plan_create, name='business_plan_create'),
    path('business-plans/analysis/', views.business_plan_analysis, name='business_plan_analysis'),
    path('business-plans/<int:plan_id>/', views.business_plan_detail, name='business_plan_detail'),
    path('business-plans/<int:plan_id>/delete/', views.business_plan_delete, name='business_plan_delete'),

    path('business-plans/<int:plan_id>/analyze/', views.business_plan_analyze, name='business_plan_analyze'),
    
    # 캘린더 API
    path('my-calendar/', views.my_calendar_page, name='my_calendar'),
    path('api/calendar/events/', views.get_calendar_events, name='get_calendar_events'),
    path('api/calendar/events/add/', views.add_calendar_event, name='add_calendar_event'),
    path('api/calendar/events/<int:event_id>/delete/', views.delete_calendar_event, name='delete_calendar_event'),
    path('api/calendar/events/<int:event_id>/toggle/', views.toggle_event_complete, name='toggle_event_complete'),
    path('api/calendar/events/upcoming/', views.get_upcoming_events, name='get_upcoming_events'),
]
