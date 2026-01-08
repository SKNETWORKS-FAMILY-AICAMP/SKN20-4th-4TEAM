# chat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import ChatSession, ChatMessage, BusinessPlan
import requests
import json
import time
import uuid
import re

# FastAPI 서버 주소
FASTAPI_URL = "http://localhost:8000"

# ========================================
# 페이지 Views
# ========================================

def login_page(request):
    """로그인/회원가입 페이지"""
    return render(request, 'login.html')

def chat_page(request):
    """채팅 페이지 (인증된 사용자만 접근 가능)"""
    if not request.user.is_authenticated:
        return redirect('/')
    return render(request, 'chat.html')

# ========================================
# 인증 관련 Views
# ========================================

@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    """회원가입 API (username + password만 사용)"""
    try:
        # JSON / form 모두 처리
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST

        print("[REGISTER] data:", data)

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return JsonResponse({
                'error': '아이디와 비밀번호를 입력해주세요.'
            }, status=400)

        # 사용자명 규칙
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return JsonResponse({
                'error': '아이디는 영문, 숫자, _만 사용하여 3-20자로 입력해주세요.'
            }, status=400)

        # 비밀번호 규칙
        if len(password) < 8:
            return JsonResponse({
                'error': '비밀번호는 최소 8자 이상이어야 합니다.'
            }, status=400)

        # 중복 아이디 검사
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'error': '이미 사용 중인 아이디입니다.'
            }, status=400)

        # 사용자 생성 (email은 비워둠)
        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)
        print(f"[REGISTER] 사용자 생성 성공: {username}")

        return JsonResponse({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username
            }
        })

    except Exception as e:
        print("[REGISTER ERROR]", e)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """로그인 API"""
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST

        print("[LOGIN] data:", data)

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return JsonResponse({
                'error': '아이디와 비밀번호를 입력해주세요.'
            }, status=400)

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({
                'error': '아이디 또는 비밀번호가 올바르지 않습니다.'
            }, status=400)

        login(request, user)
        print(f"[LOGIN] 로그인 성공: {username}")
        last_session = ChatSession.objects.filter(
        user_identifier=user.username,
        is_active=True
        ).order_by('-updated_at').first()

        if last_session:
            request.session['chat_session_id'] = str(last_session.session_id)
        return JsonResponse({
            'success': True,
            'message': '로그인되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username
            }
        })

    except Exception as e:
        print("[LOGIN ERROR]", e)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """로그아웃 API"""
    try:
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            print(f"[Django] 사용자 로그아웃: {username}")
            
            return JsonResponse({
                'success': True,
                'message': '로그아웃되었습니다.'
            })
        else:
            return JsonResponse({
                'error': '로그인되지 않은 상태입니다.'
            }, status=400)
            
    except Exception as e:
        print(f"[Django] 로그아웃 오류: {e}")
        return JsonResponse({
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def user_status(request):
    """현재 사용자 상태 확인 API"""
    try:
        if request.user.is_authenticated:
            return JsonResponse({
                'authenticated': True,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email
                }
            })
        else:
            return JsonResponse({
                'authenticated': False
            })
            
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

# ========================================
# 채팅 관련 Views (세션 관리 개선)
# ========================================

def get_or_create_session(request):
    """세션 가져오기 또는 생성 (사용자 인증 고려)"""
    session_id = request.session.get('chat_session_id')
    
    # 로그인한 사용자면 username 사용, 아니면 세션키 사용
    if request.user.is_authenticated:
        user_identifier = request.user.username
        old_session_id = request.session.get('chat_session_id')
        if old_session_id:
            ChatSession.objects.filter(
            session_id=old_session_id
            ).update(user_identifier=user_identifier)
        
    else:
        user_identifier = request.session.session_key or str(uuid.uuid4())[:8]
    
    if session_id:
        try:
            session = ChatSession.objects.get(session_id=session_id, is_active=True)
            # 사용자 식별자가 바뀌었으면 (로그인/로그아웃) 업데이트
            if session.user_identifier != user_identifier:
                session.user_identifier = user_identifier
                session.save()
            return session
        except ChatSession.DoesNotExist:
            pass
    
    # 새 세션 생성
    session = ChatSession.objects.create(
        user_identifier=user_identifier,
        title="새로운 대화"
    )
    request.session['chat_session_id'] = str(session.session_id)
    return session

@csrf_exempt  # 개발용 (나중에 CSRF 토큰 추가)
def chat_api(request):
    """Django API: 프론트엔드 → Django → FastAPI → DB 저장"""
    if request.method == 'POST':
        start_time = time.time()  # 응답 시간 측정 시작
        
        try:
            # 1. 요청 데이터 파싱
            data = json.loads(request.body)
            question = data.get('question')
            chat_history = data.get('chat_history', [])
            
            if not question:
                return JsonResponse({
                    'error': '질문이 비어있습니다.'
                }, status=400)
            
            print(f"[Django] 질문 받음: {question}")
            print(f"[Django] 히스토리 길이: {len(chat_history)}")
            
            # 2. 세션 관리
            session = get_or_create_session(request)
            print(f"[Django] 세션: {session.session_id}")
            
            # 3. FastAPI에 전달
            print(f"[Django] FastAPI 호출 중...")
            fastapi_session_id = request.session.get("fastapi_session_id")
            response = requests.post(
                f"{FASTAPI_URL}/chat",
                json={
                    'question': question,
                    'chat_history': chat_history,  # 👈 히스토리 전달
                    "session_id": fastapi_session_id,
                },
                timeout=120  # 2분 (RAG 처리 시간)
            )
            
            if response.ok:
                result = response.json()
                if result.get("session_id") is not None:
                    request.session["fastapi_session_id"] = result["session_id"]
                    
                ai_answer = result.get('answer', '')
                source_type = result.get('source_type', 'unknown')
                
                # 4. 응답 시간 계산
                response_time = time.time() - start_time
                
                print(f"[Django] FastAPI 응답 받음: {source_type} ({response_time:.2f}s)")
                
                # 5. 데이터베이스 저장
                try:
                    chat_message = ChatMessage.objects.create(
                        session=session,
                        user_message=question,
                        ai_response=ai_answer,
                        source_type=source_type,
                        response_time=response_time
                    )
                    
                    # 세션 제목 자동 설정 (첫 번째 질문으로)
                    if session.message_count == 1 and session.title == "새로운 대화":
                        session.title = question[:50] + ('...' if len(question) > 50 else '')
                        session.save()
                    
                    print(f"[Django] DB 저장 완료: Message ID {chat_message.id}")
                    
                except Exception as db_error:
                    print(f"[Django] DB 저장 오류: {db_error}")
                    # DB 저장 실패해도 응답은 반환
                
                return JsonResponse(result)
            else:
                # FastAPI 오류 시에도 DB에 기록 (선택사항)
                error_msg = f'FastAPI 오류: {response.status_code}'
                
                try:
                    session = get_or_create_session(request)
                    ChatMessage.objects.create(
                        session=session,
                        user_message=question,
                        ai_response=error_msg,
                        source_type='error',
                        response_time=time.time() - start_time
                    )
                except:
                    pass
                
                return JsonResponse({'error': error_msg}, status=500)
                
        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'error': 'FastAPI 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.'
            }, status=503)
        except requests.exceptions.Timeout:
            return JsonResponse({
                'error': '요청 시간이 초과되었습니다. 다시 시도해주세요.'
            }, status=504)
        except Exception as e:
            print(f"[Django] 오류 발생: {e}")
            return JsonResponse({
                'error': f'서버 오류: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'error': 'POST 요청만 허용됩니다.'
    }, status=405)

@require_http_methods(["GET"])
def get_chat_history(request):
    """현재 세션의 채팅 기록 가져오기"""
    try:
        session_id = request.session.get('chat_session_id')
        if not session_id:
            return JsonResponse({'messages': []})
        
        session = ChatSession.objects.get(session_id=session_id, is_active=True)
        messages = session.messages.all().order_by('timestamp')
        
        history = []
        for msg in messages:
            history.extend([
                {
                    'type': 'user',
                    'content': msg.user_message,
                    'timestamp': msg.timestamp.isoformat()
                },
                {
                    'type': 'bot',
                    'content': msg.ai_response,
                    'source_type': msg.source_type,
                    'response_time': msg.response_time,
                    'timestamp': msg.timestamp.isoformat()
                }
            ])
        
        return JsonResponse({
            'session_id': str(session.session_id),
            'session_title': session.title,
            'messages': history,
            'total_count': len(history)
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'messages': []})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_session_list(request):
    """사용자의 모든 채팅 세션 목록"""
    try:
        user_identifier = request.session.session_key
        if not user_identifier:
            return JsonResponse({'sessions': []})
        
        sessions = ChatSession.objects.filter(
            user_identifier=user_identifier,
            is_active=True
        ).order_by('-updated_at')
        
        session_list = []
        for session in sessions:
            session_list.append({
                'session_id': str(session.session_id),
                'title': session.title,
                'message_count': session.message_count,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat()
            })
        
        return JsonResponse({'sessions': session_list})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def new_session(request):
    """새 채팅 세션 시작"""
    try:
        # 현재 세션 비활성화
        session_id = request.session.get('chat_session_id')
        if session_id:
            try:
                old_session = ChatSession.objects.get(session_id=session_id)
                # 필요시 old_session.is_active = False 처리
            except ChatSession.DoesNotExist:
                pass
        
        # 새 세션 생성
        user_identifier = request.session.session_key or str(uuid.uuid4())[:8]
        new_session = ChatSession.objects.create(
            user_identifier=user_identifier,
            title="새로운 대화"
        )
        
        request.session['chat_session_id'] = str(new_session.session_id)
        
        return JsonResponse({
            'session_id': str(new_session.session_id),
            'message': '새 대화가 시작되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def health_check(request):
    """서버 상태 확인"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=3)
        if response.ok:
            return JsonResponse({
                'status': 'ok',
                'message': '서버 정상'
            })
    except:
        pass
    
    return JsonResponse({
        'status': 'error',
        'message': '백엔드 서버 연결 안 됨'
    }, status=503)

@login_required
def my_chats(request):
    """채팅 기록 페이지 - 사용자별 최근 50개 메시지"""
    try:
        # 로그인된 사용자와 연관된 채팅 세션들을 찾습니다
        # user_identifier로 사용자를 식별 (여기서는 username 사용)
        user_sessions = ChatSession.objects.filter(
            user_identifier=request.user.username
        ).prefetch_related('messages')
        
        # 해당 세션들의 메시지들을 최신순으로 가져옵니다
        messages = ChatMessage.objects.filter(
            session__in=user_sessions
        ).order_by('-timestamp')[:50]
        
        return render(request, 'my_chats.html', {
            'messages': messages,
            'user': request.user
        })
    except Exception as e:
        return render(request, 'my_chats.html', {
            'messages': [],
            'error': f"채팅 기록을 불러오는 중 오류가 발생했습니다: {str(e)}",
            'user': request.user
        })


# ========================================
# 마이페이지 관련 Views
# ========================================

# chat/views.py의 business_plan_create 함수 수정 버전
# 기존 함수를 이것으로 교체하세요

@login_required
def business_plan_create(request):
    """사업계획서 생성"""
    if request.method == 'POST':
        try:
            # 기본 정보
            title = request.POST.get('title', '새로운 사업계획서')
            business_name = request.POST.get('business_name', '')
            business_type = request.POST.get('business_type', 'tech')
            current_stage = request.POST.get('current_stage', 'idea')
            
            # 입력 필드
            business_idea = request.POST.get('business_idea', '')
            main_product = request.POST.get('main_product', '')
            target_customer = request.POST.get('target_customer', '')
            differentiation = request.POST.get('differentiation', '')
            revenue_plan = request.POST.get('revenue_plan', '')
            
            # 재무 정보 (선택사항)
            required_funding = request.POST.get('required_funding', '')
            if required_funding:
                required_funding = int(required_funding.replace(',', ''))
            else:
                required_funding = None
            
            # 사업계획서 생성
            plan = BusinessPlan.objects.create(
                user=request.user,
                title=title,
                business_name=business_name,
                business_type=business_type,
                current_stage=current_stage,
                business_idea=business_idea,
                main_product=main_product,
                target_customer=target_customer,
                differentiation=differentiation,
                revenue_plan=revenue_plan,
                required_funding=required_funding
            )
            
            return redirect('business_plan_detail', plan_id=plan.id)
            
        except ValueError as e:
            return render(request, 'business_plan_create.html', {
                'error': f'입력값 오류: {str(e)}'
            })
        except Exception as e:
            return render(request, 'business_plan_create.html', {
                'error': f'사업계획서 생성 중 오류가 발생했습니다: {str(e)}'
            })
    
    return render(request, 'business_plan_create.html')

@login_required
def my_page(request):
    """마이페이지"""
    try:
        # 사용자의 사업계획서 목록
        business_plans = BusinessPlan.objects.filter(user=request.user).order_by('-updated_at')[:5]
        total_plans = BusinessPlan.objects.filter(user=request.user).count()
        completed_plans = BusinessPlan.objects.filter(user=request.user, is_complete=True).count()
        
        # 최근 채팅 기록
        user_sessions = ChatSession.objects.filter(
            user_identifier=request.user.username
        ).order_by('-updated_at')[:5]
        
        return render(request, 'mypage.html', {
            'recent_plans': business_plans,
            'total_plans': total_plans,
            'completed_plans': completed_plans,
            'recent_sessions': user_sessions
        })
    except Exception as e:
        return render(request, 'mypage.html', {
            'error': f'마이페이지 로딩 중 오류가 발생했습니다: {str(e)}'
        })

@login_required
def business_plan_list(request):
    """사업계획서 목록"""
    try:
        plans = BusinessPlan.objects.filter(user=request.user).order_by('-updated_at')
        return render(request, 'business_plan_list.html', {
            'plans': plans
        })
    except Exception as e:
        return render(request, 'business_plan_list.html', {
            'plans': [],
            'error': f'사업계획서 목록을 불러오는 중 오류가 발생했습니다: {str(e)}'
        })

@login_required
def business_plan_detail(request, plan_id):
    """사업계획서 상세/편집"""
    plan = get_object_or_404(BusinessPlan, id=plan_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # 기본 정보 업데이트
            plan.title = request.POST.get('title', plan.title)
            plan.business_name = request.POST.get('business_name', plan.business_name)
            plan.business_type = request.POST.get('business_type', plan.business_type)
            plan.current_stage = request.POST.get('current_stage', plan.current_stage)
            
            # AI 입력용 기본 정보 업데이트
            plan.business_idea = request.POST.get('business_idea', plan.business_idea)
            plan.main_product = request.POST.get('main_product', plan.main_product)
            plan.target_customer = request.POST.get('target_customer', plan.target_customer)
            plan.differentiation = request.POST.get('differentiation', plan.differentiation)
            plan.revenue_plan = request.POST.get('revenue_plan', plan.revenue_plan)
            
            # AI 생성 컨텐츠 업데이트
            plan.executive_summary = request.POST.get('executive_summary', plan.executive_summary)
            plan.business_model = request.POST.get('business_model', plan.business_model)
            plan.target_market = request.POST.get('target_market', plan.target_market)
            plan.competitive_advantage = request.POST.get('competitive_advantage', plan.competitive_advantage)
            
            # 재무 정보 업데이트
            for field in ['required_funding', 'expected_revenue_year1', 'expected_revenue_year3']:
                value = request.POST.get(field, '')
                if value:
                    try:
                        setattr(plan, field, int(value.replace(',', '')))
                    except ValueError:
                        setattr(plan, field, None)
                else:
                    setattr(plan, field, None)
            
            # 완료 여부 업데이트
            plan.is_complete = bool(request.POST.get('is_complete'))
            
            plan.save()
            
            return render(request, 'business_plan_detail.html', {
                'plan': plan,
                'success': '사업계획서가 성공적으로 저장되었습니다.'
            })
            
        except Exception as e:
            return render(request, 'business_plan_detail.html', {
                'plan': plan,
                'error': f'저장 중 오류가 발생했습니다: {str(e)}'
            })
    
    return render(request, 'business_plan_detail.html', {
        'plan': plan
    })

@login_required
def business_plan_delete(request, plan_id):
    """사업계획서 삭제"""
    if request.method == 'POST':
        try:
            plan = get_object_or_404(BusinessPlan, id=plan_id, user=request.user)
            plan.delete()
            return JsonResponse({'success': True, 'message': '사업계획서가 삭제되었습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 방식만 지원됩니다.'})

@login_required
def business_plan_analysis(request):
    """AI 분석 결과 표시 페이지"""
    return render(request, 'business_plan_analysis.html')

@login_required
def business_plan_analyze(request, plan_id):
    """AI 전문가가 사업계획서를 분석"""
    plan = get_object_or_404(BusinessPlan, id=plan_id, user=request.user)
    
    # 분석할 내용이 충분한지 확인
    if not plan.business_idea or not plan.main_product:
        return redirect('business_plan_detail', plan_id=plan_id)
    
    try:
        # AI 분석 프롬프트 생성
        analysis_prompt = f"""
당신은 20년 경력의 벤처 투자 전문가이자 사업 컨설턴트입니다.
다음 사업계획서를 전문가 관점에서 철저히 분석하고 평가해주세요.

[사업 기본 정보]
- 사업명: {plan.business_name}
- 분야: {plan.get_business_type_display()}
- 단계: {plan.get_current_stage_display()}

[사업 내용]
- 사업 아이디어: {plan.business_idea}
- 주요 제품/서비스: {plan.main_product}
- 타겟 고객: {plan.target_customer}
- 차별화 포인트: {plan.differentiation}
{f"- 수익 모델: {plan.revenue_plan}" if plan.revenue_plan else ""}

[작성된 사업계획서]
- 사업개요: {plan.executive_summary if plan.executive_summary else "미작성"}
- 비즈니스모델: {plan.business_model if plan.business_model else "미작성"}
- 목표시장: {plan.target_market if plan.target_market else "미작성"}
- 경쟁우위: {plan.competitive_advantage if plan.competitive_advantage else "미작성"}

다음 형식으로 상세히 분석해주세요:

=== 종합 점수 ===
투자매력도: [0-100점]
시장성: [0-100점]
실현가능성: [0-100점]
차별성: [0-100점]
완성도: [0-100점]

=== 시장 동향 분석 ===
[해당 업종의 시장 규모, 성장률, 최근 트렌드를 구체적으로 분석]
- 시장 규모:
- 성장률:
- 주요 트렌드:
- 경쟁 환경:

=== 실현 가능성 평가 ===
[기술적, 재무적, 시장 진입 가능성을 평가]
- 기술적 실현 가능성:
- 자금 조달 현실성:
- 시장 진입 장벽:
- 예상 타임라인 적정성:

=== 강점 분석 ===
1. [구체적인 강점]
2. [구체적인 강점]
3. [구체적인 강점]

=== 보완 필요 사항 ===
1. [구체적인 약점 및 개선 방향]
2. [구체적인 약점 및 개선 방향]
3. [구체적인 약점 및 개선 방향]

=== 리스크 요인 ===
1. [주요 리스크 요인과 대응 방안]
2. [주요 리스크 요인과 대응 방안]
3. [주요 리스크 요인과 대응 방안]

=== 개선 제안 ===
[단기 개선안]
-

[중기 개선안]
-

[장기 전략]
-

=== 종합 의견 ===
[투자자/심사위원 관점에서의 종합 평가 및 조언]
"""

        print(f"[Django] AI 분석 요청 중... Plan ID: {plan_id}")
        
        # FastAPI에 분석 요청
        response = requests.post(
            f"{FASTAPI_URL}/analyze",
            json={
                'question': analysis_prompt,
                'chat_history': []
            },
            timeout=120
        )
        
        if response.ok:
            result = response.json()
            analysis_text = result.get('answer', '')
            
            print(f"[Django] AI 분석 완료")
            
            # 분석 결과 파싱
            parsed_analysis = parse_analysis(analysis_text)
            
            return render(request, 'business_plan_analysis.html', {
                'plan': plan,
                'analysis': parsed_analysis,
                'raw_analysis': analysis_text
            })
        else:
            error_msg = f'분석 중 오류 발생: {response.status_code}'
            return render(request, 'business_plan_detail.html', {
                'plan': plan,
                'error': error_msg
            })
            
    except requests.exceptions.ConnectionError:
        return render(request, 'business_plan_detail.html', {
            'plan': plan,
            'error': 'FastAPI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.'
        })
    except requests.exceptions.Timeout:
        return render(request, 'business_plan_detail.html', {
            'plan': plan,
            'error': 'AI 분석 시간이 초과되었습니다. 다시 시도해주세요.'
        })
    except Exception as e:
        print(f"[Django] 분석 오류: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'business_plan_detail.html', {
            'plan': plan,
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        })


def parse_analysis(analysis_text):
    """AI 분석 결과를 파싱"""
    import re
    
    parsed = {
        'scores': {},
        'market_analysis': '',
        'feasibility': '',
        'strengths': [],
        'weaknesses': [],
        'risks': [],
        'suggestions': {},
        'conclusion': ''
    }
    
    try:
        # 점수 파싱
        score_section = re.search(r'=== 종합 점수 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if score_section:
            score_text = score_section.group(1)
            scores = re.findall(r'([가-힣]+):\s*(\d+)', score_text)
            for name, score in scores:
                parsed['scores'][name] = int(score)
        
        # 시장 동향 분석
        market_section = re.search(r'=== 시장 동향 분석 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if market_section:
            parsed['market_analysis'] = market_section.group(1).strip()
        
        # 실현 가능성
        feasibility_section = re.search(r'=== 실현 가능성 평가 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if feasibility_section:
            parsed['feasibility'] = feasibility_section.group(1).strip()
        
        # 강점
        strengths_section = re.search(r'=== 강점 분석 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if strengths_section:
            strengths_text = strengths_section.group(1).strip()
            parsed['strengths'] = [s.strip() for s in re.findall(r'\d+\.\s*(.+)', strengths_text)]
        
        # 보완 필요
        weaknesses_section = re.search(r'=== 보완 필요 사항 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if weaknesses_section:
            weaknesses_text = weaknesses_section.group(1).strip()
            parsed['weaknesses'] = [w.strip() for w in re.findall(r'\d+\.\s*(.+)', weaknesses_text)]
        
        # 리스크
        risks_section = re.search(r'=== 리스크 요인 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if risks_section:
            risks_text = risks_section.group(1).strip()
            parsed['risks'] = [r.strip() for r in re.findall(r'\d+\.\s*(.+)', risks_text)]
        
        # 개선 제안
        suggestions_section = re.search(r'=== 개선 제안 ===\s*(.*?)(?===|$)', analysis_text, re.DOTALL)
        if suggestions_section:
            suggestions_text = suggestions_section.group(1).strip()
            
            short_term = re.search(r'\[단기 개선안\]\s*(.*?)(?=\[|$)', suggestions_text, re.DOTALL)
            if short_term:
                parsed['suggestions']['short_term'] = short_term.group(1).strip()
            
            mid_term = re.search(r'\[중기 개선안\]\s*(.*?)(?=\[|$)', suggestions_text, re.DOTALL)
            if mid_term:
                parsed['suggestions']['mid_term'] = mid_term.group(1).strip()
            
            long_term = re.search(r'\[장기 전략\]\s*(.*?)(?=\[|$)', suggestions_text, re.DOTALL)
            if long_term:
                parsed['suggestions']['long_term'] = long_term.group(1).strip()
        
        # 종합 의견
        conclusion_section = re.search(r'=== 종합 의견 ===\s*(.*?)$', analysis_text, re.DOTALL)
        if conclusion_section:
            parsed['conclusion'] = conclusion_section.group(1).strip()
        
    except Exception as e:
        print(f"[Django] 파싱 오류: {e}")
    
    return parsed