#!/usr/bin/env python3
"""
邮件密码设置脚本
Email Password Setup Script
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_password():
    """设置邮件密码"""
    print("📧 设置163邮箱密码")
    print("=" * 40)
    print("邮箱地址: Edu_Agent@163.com")
    print("SMTP服务器: smtp.163.com")
    print("端口: 587")
    print("加密方式: TLS")
    print("=" * 40)
    
    print("\n🔐 获取163邮箱应用密码的步骤:")
    print("1. 登录 https://mail.163.com")
    print("2. 使用 Edu_Agent@163.com 登录")
    print("3. 进入设置 → POP3/SMTP/IMAP")
    print("4. 开启SMTP服务")
    print("5. 设置客户端授权密码（16位字符）")
    print("6. 记录授权密码")
    
    print("\n💡 设置密码的方法:")
    print("方法1: 设置环境变量")
    print("  export MAIL_PASSWORD=your-16-digit-password")
    print()
    print("方法2: 直接修改配置文件")
    print("  编辑 config/settings.py")
    print("  将 MAIL_PASSWORD 设置为您的授权密码")
    
    # 检查当前密码状态
    try:
        from config.settings import MAIL_CONFIG
        current_password = MAIL_CONFIG.get('MAIL_PASSWORD', '')
        
        if current_password:
            print(f"\n✅ 当前已设置密码: {'*' * len(current_password)}")
        else:
            print("\n⚠️  当前未设置密码")
            
    except Exception as e:
        print(f"\n❌ 读取配置失败: {e}")
    
    print("\n🧪 测试邮件发送:")
    print("设置密码后，运行以下命令测试:")
    print("  python test_email_config.py")

def test_with_password():
    """使用密码测试邮件发送"""
    print("\n🔍 测试邮件发送功能...")
    
    try:
        from interface.flask_app import create_app
        app = create_app()
        
        with app.app_context():
            from services.email_service import EmailService
            
            email_service = EmailService()
            
            # 测试发送验证码邮件
            result = email_service.send_verification_email(
                email='test@example.com',
                code='123456',
                username='测试用户'
            )
            
            if result['success']:
                print("✅ 邮件发送测试成功！")
                print("🎉 163邮箱配置完成，可以正常发送验证码邮件")
            else:
                print(f"❌ 邮件发送失败: {result.get('error', '未知错误')}")
                print("💡 请检查:")
                print("  1. 邮箱地址是否正确")
                print("  2. 授权密码是否正确")
                print("  3. SMTP服务是否已开启")
            
            return result['success']
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 163邮箱密码设置助手")
    print("=" * 50)
    
    setup_password()
    
    # 检查是否已设置密码
    try:
        from config.settings import MAIL_CONFIG
        if MAIL_CONFIG.get('MAIL_PASSWORD'):
            print("\n" + "=" * 50)
            choice = input("是否要测试邮件发送？(y/n): ").lower().strip()
            if choice == 'y':
                test_with_password()
        else:
            print("\n💡 请先设置密码，然后重新运行此脚本进行测试")
            
    except Exception as e:
        print(f"\n❌ 检查配置失败: {e}")

if __name__ == "__main__":
    main()
