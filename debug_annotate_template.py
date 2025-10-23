#!/usr/bin/env python3
"""
模板标注调试工具
用于后端测试AI自动标注模板功能
"""

import os
import sys
from core.template_annotator import TemplateAnnotator
from core.agent import UniversityCourseAgent
from config.settings import DASHSCOPE_API_KEY


def main():
    """主函数"""
    print("\n" + "=" * 100)
    print("🤖 AI模板自动标注工具")
    print("=" * 100)
    print()
    print("功能说明:")
    print("  该工具会自动识别教案模板中的字段，并添加 {{placeholder}} 标签")
    print("  AI会分析模板结构，识别课程名称、教学目标、教学过程等可填充字段")
    print()
    print("=" * 100)
    print()
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
    else:
        # 列出当前目录的docx文件
        docx_files = [f for f in os.listdir('.') if f.endswith('.docx') and not f.startswith('~')]
        
        if not docx_files:
            print("❌ 当前目录没有找到.docx文件")
            print()
            print("使用方法:")
            print(f"  python {os.path.basename(__file__)} <模板文件路径>")
            print()
            print("示例:")
            print(f"  python {os.path.basename(__file__)} 教案模版.docx")
            return
        
        print("📂 在当前目录找到以下模板文件:\n")
        for idx, file in enumerate(docx_files, 1):
            size = os.path.getsize(file) / 1024  # KB
            print(f"  {idx}. {file} ({size:.1f} KB)")
        
        print()
        
        # 非交互模式，默认选择第一个
        print("🔄 自动选择第1个模板文件")
        template_path = docx_files[0]
    
    # 检查文件是否存在
    if not os.path.exists(template_path):
        print(f"❌ 文件不存在: {template_path}")
        return
    
    print(f"\n📄 选择的模板: {template_path}")
    print(f"📊 文件大小: {os.path.getsize(template_path) / 1024:.1f} KB")
    print()
    
    # 非交互模式，自动开始
    print("🚀 开始标注...")
    print()
    print("-" * 100)
    
    try:
        # 初始化Agent
        print("\n🚀 正在初始化AI Agent...")
        agent = UniversityCourseAgent(api_key=DASHSCOPE_API_KEY)
        print("✅ AI Agent初始化成功")
        
        # 初始化标注器
        print("\n🔧 正在初始化模板标注器...")
        annotator = TemplateAnnotator(agent)
        print("✅ 标注器初始化成功")
        
        # 执行标注
        print()
        output_path = annotator.annotate_template(template_path)
        
        print()
        print("-" * 100)
        print()
        print("🎉 标注完成！")
        print()
        print("📁 输出文件:")
        print(f"  ✓ 标注模板: {output_path}")
        print(f"  ✓ 标注说明: {output_path.replace('.docx', '_标注说明.txt')}")
        print()
        print("📝 下一步:")
        print("  1. 打开标注后的模板，检查红色标记的占位符")
        print("  2. 手动调整不准确的标注")
        print("  3. 将调整后的模板上传到系统的 templates_library/ 目录")
        print("  4. 使用高级生成功能时选择该模板")
        print()
        print("=" * 100)
        
    except Exception as e:
        print()
        print("=" * 100)
        print(f"❌ 标注过程出错: {e}")
        print("=" * 100)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

