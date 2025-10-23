#!/usr/bin/env python3
"""
@高级生成 - 命令行工具
Advanced Generation CLI Tool

使用方法:
    python advanced_gen.py "Python列表推导式"
    python advanced_gen.py "市场营销中的SWOT分析"
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.advanced_generator import AdvancedLessonGenerator
from core.agent import UniversityCourseAgent
from config.settings import DASHSCOPE_API_KEY


async def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 2:
        print("=" * 80)
        print("🚀 @高级生成 - Advanced Generation")
        print("=" * 80)
        print()
        print("用法:")
        print("    python advanced_gen.py \"教案主题\"")
        print()
        print("示例:")
        print("    python advanced_gen.py \"Python列表推导式\"")
        print("    python advanced_gen.py \"市场营销中的SWOT分析\"")
        print("    python advanced_gen.py \"数据库的事务管理\"")
        print()
        print("=" * 80)
        sys.exit(1)
    
    # 获取主题
    topic = " ".join(sys.argv[1:])
    
    try:
        # 初始化AI代理
        print("🔧 初始化AI代理...")
        agent = UniversityCourseAgent(api_key=DASHSCOPE_API_KEY)
        
        # 创建生成器
        generator = AdvancedLessonGenerator(agent=agent)
        
        # 执行生成
        success, result = await generator.generate(topic)
        
        if success:
            print()
            print("✨ 您可以打开以下文件查看生成的教案:")
            print(f"   {result}")
            print()
            return 0
        else:
            print()
            print(f"❌ 生成失败: {result}")
            print()
            return 1
            
    except Exception as e:
        print()
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

