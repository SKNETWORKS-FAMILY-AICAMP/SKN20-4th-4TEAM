# chat/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import ChatSession, ChatMessage
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
    """회원가입 API"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        password_confirm = data.get('password_confirm', '').strip()
        
        # 입력값 검증
        if not all([username, email, password, password_confirm]):
            return JsonResponse({
                'error': '모든 필드를 입력해주세요.'
            }, status=400)
        
        # 사용자명 검증 (영문, 숫자, _ 만 허용, 3-20자)
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return JsonResponse({
                'error': '사용자명은 영문, 숫자, _만 사용하여 3-20자로 입력해주세요.'
            }, status=400)
        
        # 이메일 검증
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'error': '유효한 이메일 주소를 입력해주세요.'
            }, status=400)
        
        # 비밀번호 확인
        if password != password_confirm:
            return JsonResponse({
                'error': '비밀번호가 일치하지 않습니다.'
            }, status=400)
        
        # 비밀번호 강도 검증 (최소 8자, 영문+숫자 포함)
        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            return JsonResponse({
                'error': '비밀번호는 최소 8자이며, 영문과 숫자를 포함해야 합니다.'
            }, status=400)
        
        # 중복 사용자명 확인
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'error': '이미 사용 중인 사용자명입니다.'
            }, status=400)
        
        # 중복 이메일 확인
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'error': '이미 사용 중인 이메일 주소입니다.'
            }, status=400)
        
        # 사용자 생성
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        print(f"[Django] 새 사용자 생성: {username}")
        
        # 자동 로그인
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': '잘못된 요청 형식입니다.'
        }, status=400)
    except Exception as e:
        print(f"[Django] 회원가입 오류: {e}")
        return JsonResponse({
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """로그인 API"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return JsonResponse({
                'error': '사용자명과 비밀번호를 입력해주세요.'
            }, status=400)
        
        # 사용자 인증
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                print(f"[Django] 사용자 로그인: {username}")
                
                return JsonResponse({
                    'success': True,
                    'message': '로그인되었습니다.',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                return JsonResponse({
                    'error': '비활성화된 계정입니다.'
                }, status=400)
        else:
            return JsonResponse({
                'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': '잘못된 요청 형식입니다.'
        }, status=400)
    except Exception as e:
        print(f"[Django] 로그인 오류: {e}")
        return JsonResponse({
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)

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
            
            if not question:
                return JsonResponse({
                    'error': '질문이 비어있습니다.'
                }, status=400)
            
            print(f"[Django] 질문 받음: {question}")
            
            # 2. 세션 관리
            session = get_or_create_session(request)
            print(f"[Django] 세션: {session.session_id}")
            
            # 3. FastAPI에 전달
            print(f"[Django] FastAPI 호출 중...")
            response = requests.post(
                f"{FASTAPI_URL}/chat",
                json={'question': question},
                timeout=120  # 2분 (RAG 처리 시간)
            )
            
            if response.ok:
                result = response.json()
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