#!/usr/bin/env python3
"""
EasyOCR测试脚本 - 测试新的轻量级OCR实现
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdfreadermcp.tools.pdf_ocr import PDFOCR


async def test_easyocr():
    """测试EasyOCR功能识别PDF文件"""
    pdf_path = "/Users/lihongwen/Desktop/第三章　工程项目管理.pdf"
    
    print("🚀 开始EasyOCR测试...")
    print(f"📄 文件路径: {pdf_path}")
    print(f"📊 文件大小: {Path(pdf_path).stat().st_size / 1024 / 1024:.2f} MB")
    
    # 创建PDFOCR实例
    ocr = PDFOCR()
    
    try:
        # 执行OCR识别 - 只处理第1页进行快速测试
        print("\n⏳ 正在进行EasyOCR识别（处理第1页）...")
        print("💡 提示: 首次运行会自动下载EasyOCR模型，请稍等...")
        
        result = await ocr.extract_text_ocr(
            file_path=pdf_path,
            pages="1",  # 只处理第1页
            language="ch_sim,en",  # 中英文识别
            chunk_size=800,
            use_gpu=False  # 使用CPU模式
        )
        
        # 解析结果
        result_data = json.loads(result)
        
        print("\n" + "="*60)
        print("🎉 EasyOCR识别完成!")
        print("="*60)
        
        if result_data.get('success', False):
            print(f"✅ 处理状态: 成功")
            print(f"📄 总页数: {result_data.get('total_pages', 'N/A')}")
            print(f"🔍 处理页数: {result_data.get('processed_pages', [])}")
            print(f"🌐 识别语言: {result_data.get('ocr_language', 'N/A')}")
            print(f"📦 文本块数量: {len(result_data.get('chunks', []))}")
            print(f"⚡ 识别引擎: {result_data.get('extraction_method', 'N/A')}")
            
            # 显示OCR摘要信息
            ocr_summary = result_data.get('ocr_summary', {})
            if ocr_summary:
                print(f"📊 平均置信度: {ocr_summary.get('average_confidence', 0):.3f}")
                print(f"📝 文本块总数: {ocr_summary.get('total_text_blocks', 0)}")
            
            # 显示文本内容预览
            chunks = result_data.get('chunks', [])
            if chunks:
                print(f"\n📖 识别内容预览:")
                print("-" * 60)
                for i, chunk in enumerate(chunks[:2]):  # 显示前2个块
                    content = chunk.get('content', '').strip()
                    page_num = chunk.get('page_number', 'N/A')
                    print(f"\n块 {i+1} (第{page_num}页):")
                    # 限制预览长度
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(preview)
                
                if len(chunks) > 2:
                    print(f"\n... 还有 {len(chunks) - 2} 个文本块")
                    
                print(f"\n💾 完整结果已保存到: easyocr_result.json")
                
                # 保存完整结果
                with open('easyocr_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                print("\n🎊 EasyOCR功能测试成功!")
                print("✨ 相比PaddleOCR的优势:")
                print("   - 🚀 启动速度更快")
                print("   - 💾 模型更轻量")
                print("   - 🛠️ 安装更简单")
                print("   - ⚡ CPU模式友好")
                
                return True
            else:
                print("❌ 未识别到文本内容")
                return False
                
        else:
            print(f"❌ OCR识别失败: {result_data.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_easyocr())
    print(f"\n{'='*60}")
    if success:
        print("🎉 测试结果: 成功 - EasyOCR OCR功能正常工作!")
    else:
        print("💥 测试结果: 失败 - 请检查错误信息")
    print(f"{'='*60}")
    sys.exit(0 if success else 1)