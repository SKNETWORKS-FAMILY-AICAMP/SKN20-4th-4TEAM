from django.contrib import admin
from .models import ChatMessage, ChatSession

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user_identifier', 'message_count', 'created_at', 'updated_at', 'is_active']
    list_filter = ['created_at', 'is_active']
    search_fields = ['title', 'user_identifier']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    def message_count(self, obj):
        return obj.message_count
    message_count.short_description = '메시지 수'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'session_title', 'question_preview', 'source_type', 'response_time']
    list_filter = ['source_type', 'timestamp', 'session']
    search_fields = ['user_message', 'ai_response']
    readonly_fields = ['timestamp']
    raw_id_fields = ['session']  # 세션이 많을 때 성능 향상
    
    def question_preview(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    question_preview.short_description = '질문'
    
    def session_title(self, obj):
        return obj.session.title
    session_title.short_description = '세션'