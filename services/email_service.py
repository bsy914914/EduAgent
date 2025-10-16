"""
邮件发送服务
Email Service
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app
from flask_mail import Mail, Message
from config.settings import MAIL_CONFIG


class EmailService:
    """邮件发送服务类"""
    
    def __init__(self):
        self.mail = None
        self._init_mail()
    
    def _init_mail(self):
        """初始化邮件服务"""
        try:
            # 延迟初始化，在需要时再创建
            self.mail = None
        except Exception as e:
            print(f"邮件服务初始化失败: {e}")
    
    def _get_mail(self):
        """获取邮件服务实例"""
        if self.mail is None:
            try:
                self.mail = Mail(current_app)
            except Exception as e:
                print(f"邮件服务创建失败: {e}")
                return None
        return self.mail
    
    def generate_verification_code(self, length: int = 6) -> str:
        """生成验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, email: str, code: str, username: str = None, code_type: str = 'register') -> Dict[str, Any]:
        """发送验证码邮件"""
        try:
            mail = self._get_mail()
            if not mail:
                return {'success': False, 'error': '邮件服务未初始化'}
            
            # 设置邮件主题和内容
            if code_type == 'register':
                subject = "【EduAgent智教创想】邮箱验证码"
                action_text = "注册"
                action_description = "您正在注册EduAgent智教创想账户，请使用以下验证码完成注册："
            elif code_type == 'reset_password':
                subject = "【EduAgent智教创想】密码重置验证码"
                action_text = "密码重置"
                action_description = "您正在重置EduAgent智教创想账户密码，请使用以下验证码完成密码重置："
            else:
                subject = "【EduAgent智教创想】邮箱验证码"
                action_text = "验证"
                action_description = "您正在进行账户验证，请使用以下验证码完成验证："
            
            # HTML邮件模板
            html_body = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>邮箱验证码</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        border-radius: 10px;
                        padding: 30px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #007bff;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{
                        color: #007bff;
                        margin: 0;
                        font-size: 24px;
                    }}
                    .content {{
                        margin-bottom: 30px;
                    }}
                    .verification-code {{
                        background: #f8f9fa;
                        border: 2px dashed #007bff;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .code {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #007bff;
                        letter-spacing: 5px;
                        font-family: 'Courier New', monospace;
                    }}
                    .warning {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #856404;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                        border-top: 1px solid #eee;
                        padding-top: 20px;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎓 EduAgent智教创想</h1>
                    </div>
                    
                    <div class="content">
                        <p>您好{f'，{username}' if username else ''}！</p>
                        
                        <p>{action_description}</p>
                        
                        <div class="verification-code">
                            <div class="code">{code}</div>
                        </div>
                        
                        <div class="warning">
                            <strong>⚠️ 重要提醒：</strong>
                            <ul>
                                <li>验证码有效期为 <strong>10分钟</strong></li>
                                <li>请勿将验证码泄露给他人</li>
                                <li>如非本人操作，请忽略此邮件</li>
                            </ul>
                        </div>
                        
                        <p>如果验证码无法使用，请重新获取验证码。</p>
                    </div>
                    
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿回复。</p>
                        <p>&copy; 2025 EduAgent智教创想. 保留所有权利.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本版本
            text_body = f"""
EduAgent智教创想 - {action_text}验证码

您好{username if username else ''}！

{action_description}

验证码：{code}

重要提醒：
- 验证码有效期为 10分钟
- 请勿将验证码泄露给他人
- 如非本人操作，请忽略此邮件

如果验证码无法使用，请重新获取验证码。

此邮件由系统自动发送，请勿回复。
© 2025 EduAgent智教创想. 保留所有权利.
            """
            
            # 创建邮件消息
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body,
                body=text_body
            )
            
            # 发送邮件
            mail.send(msg)
            
            return {
                'success': True,
                'message': '验证码邮件发送成功',
                'code': code  # 开发环境返回验证码，生产环境应移除
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'邮件发送失败: {str(e)}'
            }
    
    def send_welcome_email(self, email: str, username: str) -> Dict[str, Any]:
        """发送欢迎邮件"""
        try:
            mail = self._get_mail()
            if not mail:
                return {'success': False, 'error': '邮件服务未初始化'}
            
            subject = "欢迎加入EduAgent智教创想！"
            
            html_body = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>欢迎加入</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        border-radius: 10px;
                        padding: 30px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #28a745;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{
                        color: #28a745;
                        margin: 0;
                        font-size: 24px;
                    }}
                    .content {{
                        margin-bottom: 30px;
                    }}
                    .success {{
                        background: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #155724;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                        border-top: 1px solid #eee;
                        padding-top: 20px;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 欢迎加入EduAgent智教创想！</h1>
                    </div>
                    
                    <div class="content">
                        <p>亲爱的 {username}，</p>
                        
                        <div class="success">
                            <strong>🎊 恭喜您！</strong> 您的账户已成功创建并激活。
                        </div>
                        
                        <p>现在您可以开始使用我们的AI教案生成系统了！</p>
                        
                        <h3>🚀 开始使用：</h3>
                        <ul>
                            <li>上传您的教学模板</li>
                            <li>使用AI生成个性化教案</li>
                            <li>导出专业的教学文档</li>
                            <li>管理您的教学资源</li>
                        </ul>
                        
                        <p>如有任何问题，请随时联系我们的技术支持团队。</p>
                    </div>
                    
                    <div class="footer">
                        <p>感谢您选择EduAgent智教创想！</p>
                        <p>&copy; 2025 EduAgent智教创想. 保留所有权利.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body
            )
            
            mail.send(msg)
            
            return {
                'success': True,
                'message': '欢迎邮件发送成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'欢迎邮件发送失败: {str(e)}'
            }
    
    def send_password_reset_success_email(self, email: str, username: str) -> Dict[str, Any]:
        """发送密码重置成功通知邮件"""
        try:
            mail = self._get_mail()
            if not mail:
                return {'success': False, 'error': '邮件服务未初始化'}
            
            subject = "【EduAgent智教创想】密码重置成功"
            
            html_body = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>密码重置成功</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        border-radius: 10px;
                        padding: 30px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #28a745;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{
                        color: #28a745;
                        margin: 0;
                        font-size: 24px;
                    }}
                    .content {{
                        margin-bottom: 30px;
                    }}
                    .success {{
                        background: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #155724;
                    }}
                    .warning {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #856404;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                        border-top: 1px solid #eee;
                        padding-top: 20px;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔒 密码重置成功</h1>
                    </div>
                    
                    <div class="content">
                        <p>亲爱的 {username}，</p>
                        
                        <div class="success">
                            <strong>✅ 您的密码已成功重置！</strong>
                        </div>
                        
                        <p>您的EduAgent智教创想账户密码已于 {datetime.now().strftime('%Y年%m月%d日 %H:%M')} 成功重置。</p>
                        
                        <div class="warning">
                            <strong>🔐 安全提醒：</strong>
                            <ul>
                                <li>为了您的账户安全，所有现有登录会话已自动失效</li>
                                <li>请使用新密码重新登录</li>
                                <li>如非本人操作，请立即联系客服</li>
                                <li>建议定期更换密码以保护账户安全</li>
                            </ul>
                        </div>
                        
                        <p>如有任何疑问，请随时联系我们的技术支持团队。</p>
                    </div>
                    
                    <div class="footer">
                        <p>感谢您使用EduAgent智教创想！</p>
                        <p>&copy; 2025 EduAgent智教创想. 保留所有权利.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本版本
            text_body = f"""
EduAgent智教创想 - 密码重置成功

亲爱的 {username}，

您的密码已成功重置！

您的EduAgent智教创想账户密码已于 {datetime.now().strftime('%Y年%m月%d日 %H:%M')} 成功重置。

安全提醒：
- 为了您的账户安全，所有现有登录会话已自动失效
- 请使用新密码重新登录
- 如非本人操作，请立即联系客服
- 建议定期更换密码以保护账户安全

如有任何疑问，请随时联系我们的技术支持团队。

感谢您使用EduAgent智教创想！
© 2025 EduAgent智教创想. 保留所有权利.
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body,
                body=text_body
            )
            
            mail.send(msg)
            
            return {
                'success': True,
                'message': '密码重置成功通知邮件发送成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'密码重置成功通知邮件发送失败: {str(e)}'
            }