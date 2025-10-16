"""
认证路由
Authentication Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from services.auth_service import AuthService
from services.verification_service import VerificationService
from models.user import User, db
from datetime import datetime
import os

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 初始化认证服务
auth_service = AuthService()
verification_service = VerificationService()


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否有Authorization头
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '缺少认证令牌'}), 401
        
        # 解析Bearer token
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({'error': '认证令牌格式错误'}), 401
        
        # 验证token
        user = auth_service.verify_session(token)
        if not user:
            return jsonify({'error': '认证令牌无效或已过期'}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        result = auth_service.register_user(username, email, password, full_name)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        username_or_email = data.get('username_or_email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not username_or_email or not password:
            return jsonify({'error': '用户名/邮箱和密码不能为空'}), 400
        
        result = auth_service.login_user(username_or_email, password, remember_me)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """用户登出"""
    try:
        # 获取token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        
        result = auth_service.logout_user(token)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'登出失败: {str(e)}'}), 500


@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """获取用户资料"""
    try:
        user = request.current_user
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': f'获取资料失败: {str(e)}'}), 500


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """更新用户资料"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        full_name = data.get('full_name')
        avatar_url = data.get('avatar_url')
        
        result = auth_service.update_profile(user, full_name, avatar_url)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'更新资料失败: {str(e)}'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """修改密码"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'error': '原密码和新密码不能为空'}), 400
        
        result = auth_service.change_password(user, old_password, new_password)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'修改密码失败: {str(e)}'}), 500


@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_sessions():
    """获取用户会话列表"""
    try:
        user = request.current_user
        sessions = auth_service.get_user_sessions(user)
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
        
    except Exception as e:
        return jsonify({'error': f'获取会话列表失败: {str(e)}'}), 500


@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@require_auth
def revoke_session(session_id):
    """撤销指定会话"""
    try:
        user = request.current_user
        result = auth_service.revoke_session(user, session_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'撤销会话失败: {str(e)}'}), 500


@auth_bp.route('/verify', methods=['GET'])
@require_auth
def verify_token():
    """验证令牌有效性"""
    try:
        user = request.current_user
        return jsonify({
            'success': True,
            'valid': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': f'验证失败: {str(e)}'}), 500


@auth_bp.route('/check-username', methods=['POST'])
def check_username():
    """检查用户名是否可用"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': '用户名不能为空'}), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        available = existing_user is None
        
        return jsonify({
            'success': True,
            'available': available,
            'message': '用户名可用' if available else '用户名已存在'
        })
        
    except Exception as e:
        return jsonify({'error': f'检查用户名失败: {str(e)}'}), 500


@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    """检查邮箱是否可用"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        # 验证邮箱格式
        if not auth_service.validate_email(email):
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        available = existing_user is None
        
        return jsonify({
            'success': True,
            'available': available,
            'message': '邮箱可用' if available else '邮箱已被注册'
        })
        
    except Exception as e:
        return jsonify({'error': f'检查邮箱失败: {str(e)}'}), 500


@auth_bp.route('/validate-password', methods=['POST'])
def validate_password():
    """验证密码强度"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': '密码不能为空'}), 400
        
        validation_result = auth_service.validate_password(password)
        
        return jsonify({
            'success': True,
            'valid': validation_result['valid'],
            'errors': validation_result['errors']
        })
        
    except Exception as e:
        return jsonify({'error': f'验证密码失败: {str(e)}'}), 500


# ==================== 邮箱验证码相关路由 ====================

@auth_bp.route('/send-verification-code', methods=['POST'])
def send_verification_code():
    """发送邮箱验证码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        code_type = data.get('code_type', 'register')
        username = data.get('username', '').strip()
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        result = verification_service.send_verification_code(
            email=email,
            code_type=code_type,
            username=username
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'发送验证码失败: {str(e)}'}), 500


@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """验证邮箱验证码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        code_type = data.get('code_type', 'register')
        
        if not email or not code:
            return jsonify({'error': '邮箱和验证码不能为空'}), 400
        
        result = verification_service.verify_code(
            email=email,
            code=code,
            code_type=code_type
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'验证失败: {str(e)}'}), 500


@auth_bp.route('/resend-verification-code', methods=['POST'])
def resend_verification_code():
    """重新发送验证码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        code_type = data.get('code_type', 'register')
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        result = verification_service.resend_verification_code(
            email=email,
            code_type=code_type
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'重新发送失败: {str(e)}'}), 500


@auth_bp.route('/verification-stats', methods=['POST'])
def get_verification_stats():
    """获取验证码统计信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        stats = verification_service.get_verification_stats(email)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500


@auth_bp.route('/register-with-verification', methods=['POST'])
def register_with_verification():
    """带验证码的用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # 验证必填字段
        if not all([username, email, password, verification_code]):
            return jsonify({'error': '用户名、邮箱、密码和验证码不能为空'}), 400
        
        # 验证验证码
        code_result = verification_service.verify_code(
            email=email,
            code=verification_code,
            code_type='register'
        )
        
        if not code_result['success']:
            return jsonify(code_result), 400
        
        # 执行注册
        result = auth_service.register_user(username, email, password, full_name)
        
        if result['success']:
            # 发送欢迎邮件
            from services.email_service import EmailService
            email_service = EmailService()
            email_service.send_welcome_email(email, username)
            
            return jsonify({
                'success': True,
                'message': '注册成功！欢迎邮件已发送到您的邮箱',
                'user': result['user']
            }), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'注册失败: {str(e)}'}), 500


# ==================== 密码重置相关路由 ====================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """发送密码重置验证码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        # 验证邮箱格式
        if not auth_service.validate_email(email):
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        # 检查邮箱是否已注册
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': '该邮箱未注册'}), 400
        
        # 发送重置密码验证码
        result = verification_service.send_verification_code(
            email=email,
            code_type='reset_password',
            username=user.username
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'发送验证码失败: {str(e)}'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        verification_code = data.get('verification_code', '').strip()
        new_password = data.get('new_password', '')
        
        if not all([email, verification_code, new_password]):
            return jsonify({'error': '邮箱、验证码和新密码不能为空'}), 400
        
        # 验证邮箱格式
        if not auth_service.validate_email(email):
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        # 验证验证码
        code_result = verification_service.verify_code(
            email=email,
            code=verification_code,
            code_type='reset_password'
        )
        
        if not code_result['success']:
            return jsonify(code_result), 400
        
        # 查找用户
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 400
        
        # 验证新密码强度
        password_validation = auth_service.validate_password(new_password)
        if not password_validation['valid']:
            return jsonify({
                'error': '新密码不符合要求',
                'details': password_validation['errors']
            }), 400
        
        # 检查新密码是否与旧密码相同
        if user.check_password(new_password):
            return jsonify({'error': '新密码不能与当前密码相同'}), 400
        
        # 更新密码
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        # 使所有现有会话失效
        from models.user import UserSession
        UserSession.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
        
        db.session.commit()
        
        # 发送密码重置成功邮件
        from services.email_service import EmailService
        email_service = EmailService()
        email_service.send_password_reset_success_email(email, user.username)
        
        return jsonify({
            'success': True,
            'message': '密码重置成功，请重新登录'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'密码重置失败: {str(e)}'}), 500


