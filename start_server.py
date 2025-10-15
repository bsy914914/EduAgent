#!/usr/bin/env python3
"""
启动服务器脚本
Start Server Script
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动服务器"""
    try:
        from interface.flask_app import UniversityFlaskAPI
        
        print("🚀 启动EduAgent智教创想...")
        print("=" * 60)
        
        # 创建API实例
        api = UniversityFlaskAPI()
        
        # 启动服务器
        api.run(host='0.0.0.0', port=5025, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()