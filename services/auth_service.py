"""
认证服务
Authentication Service
"""

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import request
from flask_login import login_user, logout_user, current_user
from models.user import User, UserSession, db
from config.settings import SECRET_KEY


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.session_timeout = 24 * 60 * 60  # 24小时
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """验证密码强度"""
        errors = []
        
        if len(password) < 8:
            errors.append("密码长度至少8位")
        
        if not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        
        if not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        
        if not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def register_user(self, username: str, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        """用户注册"""
        try:
            # 验证输入
            if not username or not email or not password:
                return {'success': False, 'error': '用户名、邮箱和密码不能为空'}
            
            # 验证邮箱格式
            if not self.validate_email(email):
                return {'success': False, 'error': '邮箱格式不正确'}
            
            # 验证密码强度
            password_validation = self.validate_password(password)
            if not password_validation['valid']:
                return {'success': False, 'error': '密码不符合要求', 'details': password_validation['errors']}
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                return {'success': False, 'error': '用户名已存在'}
            
            # 检查邮箱是否已存在
            if User.query.filter_by(email=email).first():
                return {'success': False, 'error': '邮箱已被注册'}
            
            # 创建用户
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'message': '注册成功',
                'user': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'注册失败: {str(e)}'}
    
    def login_user(self, username_or_email: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """用户登录"""
        try:
            # 查找用户（支持用户名或邮箱登录）
            user = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
            
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            if not user.is_active:
                return {'success': False, 'error': '账户已被禁用'}
            
            if not user.check_password(password):
                return {'success': False, 'error': '密码错误'}
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # 创建会话
            session_token = self.create_session(user)
            
            # Flask-Login登录
            login_user(user, remember=remember_me)
            
            return {
                'success': True,
                'message': '登录成功',
                'user': user.to_dict(),
                'token': session_token
            }
            
        except Exception as e:
            return {'success': False, 'error': f'登录失败: {str(e)}'}
    
    def logout_user(self, token: str = None) -> Dict[str, Any]:
        """用户登出"""
        try:
            # 如果提供了token，删除对应的会话
            if token:
                session = UserSession.query.filter_by(session_token=token).first()
                if session:
                    session.is_active = False
                    db.session.commit()
            
            # Flask-Login登出
            logout_user()
            
            return {'success': True, 'message': '登出成功'}
            
        except Exception as e:
            return {'success': False, 'error': f'登出失败: {str(e)}'}
    
    def create_session(self, user: User) -> str:
        """创建用户会话"""
        try:
            # 生成会话令牌
            session_token = str(uuid.uuid4())
            
            # 获取客户端信息
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None
            
            # 计算过期时间
            expires_at = datetime.utcnow() + timedelta(seconds=self.session_timeout)
            
            # 创建会话记录
            session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            
            db.session.add(session)
            db.session.commit()
            
            return session_token
            
        except Exception as e:
            raise Exception(f'创建会话失败: {str(e)}')
    
    def verify_session(self, token: str) -> Optional[User]:
        """验证会话令牌"""
        try:
            session = UserSession.query.filter_by(
                session_token=token,
                is_active=True
            ).first()
            
            if not session:
                return None
            
            if session.is_expired():
                session.is_active = False
                db.session.commit()
                return None
            
            return User.query.get(session.user_id)
            
        except Exception as e:
            return None
    
    def get_current_user(self) -> Optional[User]:
        """获取当前用户"""
        return current_user if current_user.is_authenticated else None
    
    def change_password(self, user: User, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改密码"""
        try:
            # 验证旧密码
            if not user.check_password(old_password):
                return {'success': False, 'error': '原密码错误'}
            
            # 验证新密码强度
            password_validation = self.validate_password(new_password)
            if not password_validation['valid']:
                return {'success': False, 'error': '新密码不符合要求', 'details': password_validation['errors']}
            
            # 更新密码
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {'success': True, 'message': '密码修改成功'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'密码修改失败: {str(e)}'}
    
    def update_profile(self, user: User, full_name: str = None, avatar_url: str = None) -> Dict[str, Any]:
        """更新用户资料"""
        try:
            if full_name is not None:
                user.full_name = full_name
            
            if avatar_url is not None:
                user.avatar_url = avatar_url
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'message': '资料更新成功',
                'user': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'资料更新失败: {str(e)}'}
    
    def get_user_sessions(self, user: User) -> list:
        """获取用户会话列表"""
        try:
            sessions = UserSession.query.filter_by(
                user_id=user.id,
                is_active=True
            ).order_by(UserSession.created_at.desc()).all()
            
            return [session.to_dict() for session in sessions]
            
        except Exception as e:
            return []
    
    def revoke_session(self, user: User, session_id: int) -> Dict[str, Any]:
        """撤销指定会话"""
        try:
            session = UserSession.query.filter_by(
                id=session_id,
                user_id=user.id
            ).first()
            
            if not session:
                return {'success': False, 'error': '会话不存在'}
            
            session.is_active = False
            db.session.commit()
            
            return {'success': True, 'message': '会话已撤销'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'撤销会话失败: {str(e)}'}
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            expired_sessions = UserSession.query.filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            for session in expired_sessions:
                session.is_active = False
            
            db.session.commit()
            return len(expired_sessions)
            
        except Exception as e:
            db.session.rollback()
            return 0
