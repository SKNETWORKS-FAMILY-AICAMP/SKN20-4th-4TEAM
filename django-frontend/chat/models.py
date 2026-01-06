from django.db import models
from django.utils import timezone
import uuid

# Create your models here.

class ChatSession(models.Model):
    """채팅 세션 모델 - 대화방 개념"""
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_identifier = models.CharField(max_length=100, help_text="사용자 식별자 (IP 또는 세션 키)")
    title = models.CharField(max_length=200, default="새로운 대화", help_text="대화 제목")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="활성 세션 여부")
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "채팅 세션"
        verbose_name_plural = "채팅 세션들"
    
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%m/%d %H:%M')})"
    
    @property
    def message_count(self):
        return self.messages.count()

class ChatMessage(models.Model):
    """개별 채팅 메시지 모델"""
    SOURCE_CHOICES = [
        ('internal-rag', '내부 문서'),
        ('web-search', '웹 검색'),
        ('fallback', 'AI 지식'),
        ('error', '오류')
    ]
    
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    user_message = models.TextField(help_text="사용자 질문")
    ai_response = models.TextField(help_text="AI 답변")
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='internal-rag')
    response_time = models.FloatField(null=True, blank=True, help_text="응답 시간(초)")
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지들"
    
    def __str__(self):
        return f"{self.session.title}: {self.user_message[:50]}..."
