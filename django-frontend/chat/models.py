from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
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


class BusinessPlan(models.Model):
    """사업계획서 모델"""
    BUSINESS_TYPE_CHOICES = [
        ('tech', '기술창업'),
        ('service', '서비스업'),
        ('manufacturing', '제조업'),
        ('retail', '유통/소매'),
        ('food', '음식/외식'),
        ('education', '교육'),
        ('healthcare', '헬스케어'),
        ('finance', '핀테크'),
        ('other', '기타')
    ]
    
    STAGE_CHOICES = [
        ('idea', '아이디어 단계'),
        ('planning', '계획 수립'),
        ('prototype', '프로토타입'),
        ('mvp', 'MVP 개발'),
        ('launch', '출시 준비'),
        ('operating', '운영 중')
    ]
    
    user = models.ForeignKey(User, related_name='business_plans', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, help_text="사업계획서 제목")
    business_name = models.CharField(max_length=200, help_text="사업명/회사명")
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='tech')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='idea')
    
    # AI 입력용 기본 정보
    business_idea = models.TextField(blank=True, help_text="사업 아이디어 설명")
    main_product = models.TextField(blank=True, help_text="주요 제품/서비스")
    target_customer = models.TextField(blank=True, help_text="타겟 고객")
    differentiation = models.TextField(blank=True, help_text="차별화 포인트")
    revenue_plan = models.TextField(blank=True, help_text="수익 모델")
    
    # AI 생성 컨텐츠
    executive_summary = models.TextField(blank=True, help_text="사업 개요")
    business_model = models.TextField(blank=True, help_text="비즈니스 모델")
    target_market = models.TextField(blank=True, help_text="목표 시장")
    competitive_advantage = models.TextField(blank=True, help_text="경쟁 우위")
    
    # 재무 정보
    required_funding = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, help_text="필요 자금(원)")
    expected_revenue_year1 = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, help_text="1년차 예상 매출")
    expected_revenue_year3 = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, help_text="3년차 예상 매출")
    
    # 메타 정보
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(default=False, help_text="작성 완료 여부")
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "사업계획서"
        verbose_name_plural = "사업계획서들"
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"
    
    @property
    def completion_percentage(self):
        """완성도 계산"""
        fields_to_check = [
            self.executive_summary, self.business_model, 
            self.target_market, self.competitive_advantage
        ]
        completed_fields = sum(1 for field in fields_to_check if field.strip())
        return (completed_fields / len(fields_to_check)) * 100
    
    @property
    def has_ai_input_data(self):
        """AI 자동완성에 필요한 데이터가 있는지 확인"""
        return bool(
            self.business_idea and 
            self.main_product and 
            self.target_customer and 
            self.differentiation
        )