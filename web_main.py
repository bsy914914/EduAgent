#!/usr/bin/env python3
"""
完整系统启动脚本
University AI Lesson Planning System - Complete Launcher

同时启动Flask API和前端界面
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from interface.flask_app import UniversityFlaskAPI


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="University AI Lesson Planning System - Complete System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python web_main.py                    Run with default settings
  python web_main.py --port 8080        Run on custom port
  python web_main.py --host 127.0.0.1   Run on localhost only
  python web_main.py --debug            Enable debug mode
        """
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5029,
        help='Port to run the server on (default: 5026)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default="0.0.0.0",
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    return parser.parse_args()


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = {
        'flask': 'flask',
        'flask_cors': 'flask-cors',
        'langchain': 'langchain',
        'dashscope': 'dashscope',
    }
    
    optional_packages = {
        'docx': 'python-docx (for Word export)',
        'PIL': 'Pillow (for image processing)',
    }
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_required.append(package_name)
    
    # Check optional packages
    for module_name, package_name in optional_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_optional.append(package_name)
    
    # Report missing packages
    if missing_required:
        print("❌ Missing required packages:")
        for pkg in missing_required:
            print(f"   - {pkg}")
        print("\nInstall with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print("⚠️  Optional packages not installed:")
        for pkg in missing_optional:
            print(f"   - {pkg}")
        print("\nInstall with: pip install " + " ".join([p.split()[0] for p in missing_optional]))
        print("Note: System will work without these, but some features may be limited.\n")
    
    return True


def print_system_info(host, port, debug=False):
    """Print system information"""
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          🎓 大学AI教案生成系统 - 完整版                        ║
║          University AI Lesson Planning System - Complete      ║
║                                                               ║
║          基于 LangGraph + 通义千问 + Flask + 前端             ║
║          Powered by LangGraph, Qwen, Flask & Frontend         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

🚀 系统已启动
📍 前端界面: http://{host}:{port}
📚 API接口: http://{host}:{port}/api/health
🔧 调试模式: {'开启' if debug else '关闭'}

💡 使用说明:
   1. 打开浏览器访问前端界面
   2. 配置您的通义千问API Key
   3. 上传教案模板文件
   4. 设置课程基本信息
   5. 开始生成教案

📋 功能特性:
   ✅ 现代化GPT风格界面
   ✅ 模板智能解析
   ✅ 课程大纲生成
   ✅ 批量教案生成
   ✅ 多格式导出
   ✅ 实时进度显示
   ✅ 响应式设计

按 Ctrl+C 停止服务器
    """)


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    
    print("✅ All required dependencies are installed.\n")
    
    # Create and start API
    print("🚀 Starting complete system...")
    try:
        api = UniversityFlaskAPI()
        print_system_info(args.host, args.port, args.debug)
        api.run(host=args.host, port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
