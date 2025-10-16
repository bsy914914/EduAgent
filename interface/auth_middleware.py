"""
认证中间件
Authentication Middleware
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from services.auth_service import AuthService

auth_service = AuthService()


def require_auth(f):
    """认证装饰器 - 需要登录才能访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查Flask-Login的current_user
        if not current_user.is_authenticated:
            return jsonify({'error': '请先登录', 'code': 'AUTH_REQUIRED'}), 401
        
        # 检查用户是否激活
        if not current_user.is_active:
            return jsonify({'error': '账户已被禁用', 'code': 'ACCOUNT_DISABLED'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 首先检查是否已登录
        if not current_user.is_authenticated:
            return jsonify({'error': '请先登录', 'code': 'AUTH_REQUIRED'}), 401
        
        # 检查是否为管理员
        if not current_user.is_admin:
            return jsonify({'error': '需要管理员权限', 'code': 'ADMIN_REQUIRED'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """可选认证装饰器 - 如果已登录则获取用户信息，否则继续执行"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 将当前用户信息添加到请求上下文
        request.current_user = current_user if current_user.is_authenticated else None
        return f(*args, **kwargs)
    
    return decorated_function


def token_auth(f):
    """Token认证装饰器 - 通过Authorization头验证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取Authorization头
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '缺少认证令牌', 'code': 'TOKEN_MISSING'}), 401
        
        # 解析Bearer token
        try:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header
        except IndexError:
            return jsonify({'error': '认证令牌格式错误', 'code': 'TOKEN_INVALID_FORMAT'}), 401
        
        # 验证token
        user = auth_service.verify_session(token)
        if not user:
            return jsonify({'error': '认证令牌无效或已过期', 'code': 'TOKEN_INVALID'}), 401
        
        # 检查用户是否激活
        if not user.is_active:
            return jsonify({'error': '账户已被禁用', 'code': 'ACCOUNT_DISABLED'}), 403
        
        # 将用户信息添加到请求上下文
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(max_requests=100, window_seconds=3600):
    """简单的速率限制装饰器"""
    from collections import defaultdict, deque
    import time
    
    # 存储请求记录
    request_counts = defaultdict(lambda: deque())
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取客户端IP
            client_ip = request.remote_addr
            current_time = time.time()
            
            # 清理过期的请求记录
            while request_counts[client_ip] and request_counts[client_ip][0] < current_time - window_seconds:
                request_counts[client_ip].popleft()
            
            # 检查请求频率
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({
                    'error': f'请求过于频繁，请{window_seconds}秒后再试',
                    'code': 'RATE_LIMIT_EXCEEDED'
                }), 429
            
            # 记录当前请求
            request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_json_content_type(f):
    """验证Content-Type为application/json"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                return jsonify({
                    'error': '请求内容类型必须是application/json',
                    'code': 'INVALID_CONTENT_TYPE'
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def handle_cors(f):
    """处理CORS的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 处理预检请求
        if request.method == 'OPTIONS':
            response = jsonify({'message': 'OK'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            return response
        
        # 执行原函数
        result = f(*args, **kwargs)
        
        # 如果是响应对象，添加CORS头
        if hasattr(result, 'headers'):
            result.headers.add('Access-Control-Allow-Origin', '*')
            result.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            result.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        
        return result
    
    return decorated_function


def log_api_access(f):
    """API访问日志装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 记录访问日志
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        method = request.method
        path = request.path
        
        # 这里可以添加日志记录逻辑
        # 例如：写入数据库、发送到日志服务等
        print(f"API访问: {method} {path} - 用户: {user_id} - IP: {ip_address}")
        
        return f(*args, **kwargs)
    
    return decorated_function


# 组合装饰器
def api_protected(f):
    """API保护装饰器组合"""
    return handle_cors(validate_json_content_type(require_auth(log_api_access(f))))


def api_public(f):
    """公开API装饰器组合"""
    return handle_cors(validate_json_content_type(log_api_access(f)))


def api_admin(f):
    """管理员API装饰器组合"""
    return handle_cors(validate_json_content_type(require_admin(log_api_access(f))))
