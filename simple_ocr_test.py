#!/usr/bin/env python3
"""
简化OCR测试 - 测试单页识别
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdfreadermcp.tools.pdf_ocr import PDFOCR


async def simple_ocr_test():
    """简化的OCR测试 - 只测试第一页"""
    pdf_path = "/Users/lihongwen/Desktop/第三章　工程项目管理.pdf"
    
    print("🚀 开始简化OCR测试...")
    print(f"📄 文件: {Path(pdf_path).name}")
    
    # 创建PDFOCR实例
    ocr = PDFOCR()
    
    try:
        print("⏳ 正在识别第1页...")
        result = await ocr.extract_text_ocr(
            file_path=pdf_path,
            pages="1",  # 只处理第1页
            language="ch",
            chunk_size=500
        )
        
        # 解析并显示结果
        result_data = json.loads(result)
        
        if result_data.get('success', False):
            print("✅ OCR识别成功!")
            
            chunks = result_data.get('chunks', [])
            if chunks:
                print(f"📝 识别到 {len(chunks)} 个文本块")
                
                # 显示第一个块的内容
                first_chunk = chunks[0]
                content = first_chunk.get('content', '').strip()
                print(f"\n📖 第一页内容预览:")
                print("-" * 40)
                preview = content[:300] + "..." if len(content) > 300 else content
                print(preview)
                
                # 显示统计信息
                ocr_summary = result_data.get('ocr_summary', {})
                if ocr_summary:
                    print(f"\n📊 识别统计:")
                    print(f"置信度: {ocr_summary.get('average_confidence', 0):.3f}")
                    print(f"文本块: {ocr_summary.get('total_text_blocks', 0)}")
                    
                print("\n✅ OCR功能验证成功!")
                return True
            else:
                print("❌ 未识别到文本内容")
                return False
        else:
            print(f"❌ OCR失败: {result_data.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(simple_ocr_test())
    sys.exit(0 if success else 1)