#!/usr/bin/env python3
"""
Flask API启动脚本
University AI Lesson Planning System - Flask API Launcher

Usage:
    python flask_main.py [--port PORT] [--host HOST] [--debug]

Examples:
    python flask_main.py                  # Run on default port 5000
    python flask_main.py --port 8080      # Run on custom port
    python flask_main.py --debug           # Enable debug mode
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
        description="University AI Lesson Planning System - Flask API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flask_main.py                    Run with default settings
  python flask_main.py --port 8080        Run on custom port
  python flask_main.py --host 127.0.0.1   Run on localhost only
  python flask_main.py --debug            Enable debug mode
        """
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the server on (default: 5000)'
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


def print_api_info(host, port):
    """Print API information"""
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          🎓 大学AI教案生成系统 - Flask API                     ║
║          University AI Lesson Planning System - Flask API     ║
║                                                               ║
║          基于 LangGraph + 通义千问                             ║
║          Powered by LangGraph & Qwen                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

🚀 Flask API服务器已启动
📍 访问地址: http://{host}:{port}
📚 API文档: http://{host}:{port}/api/health

📋 可用接口:
   POST /api/initialize              - 初始化代理
   POST /api/upload-template         - 上传模板文件
   POST /api/generate-outline        - 生成课程大纲
   POST /api/generate-lesson         - 生成单个教案
   POST /api/generate-all-lessons    - 批量生成教案
   POST /api/export-lessons          - 导出教案文件
   GET  /api/status                  - 获取当前状态
   POST /api/reset                   - 重置状态
   GET  /api/health                  - 健康检查

💡 使用示例:
   curl -X POST http://{host}:{port}/api/health
   curl -X POST http://{host}:{port}/api/initialize -H "Content-Type: application/json" -d '{{"api_key":"your-api-key"}}'

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
    print("🚀 Starting Flask API server...")
    try:
        api = UniversityFlaskAPI()
        print_api_info(args.host, args.port)
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
