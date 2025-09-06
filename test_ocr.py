#!/usr/bin/env python3
"""
OCR测试脚本 - 识别指定的PDF文件
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdfreadermcp.tools.pdf_ocr import PDFOCR


async def test_ocr():
    """测试OCR功能识别PDF文件"""
    pdf_path = "/Users/lihongwen/Desktop/第三章　工程项目管理.pdf"
    
    print("🚀 开始OCR识别...")
    print(f"📄 文件路径: {pdf_path}")
    print(f"📊 文件大小: {Path(pdf_path).stat().st_size / 1024 / 1024:.2f} MB")
    
    # 创建PDFOCR实例
    ocr = PDFOCR()
    
    try:
        # 执行OCR识别 - 只处理前3页以节省时间
        print("\n⏳ 正在进行OCR识别（处理前3页）...")
        result = await ocr.extract_text_ocr(
            file_path=pdf_path,
            pages="1-3",  # 只处理前3页
            language="ch",  # 中文识别
            chunk_size=1000
        )
        
        # 解析结果
        result_data = json.loads(result)
        
        print("\n✅ OCR识别完成!")
        print("=" * 60)
        
        if result_data.get('success', False):
            print(f"📋 处理状态: 成功")
            print(f"📄 总页数: {result_data.get('total_pages', 'N/A')}")
            print(f"🔍 处理页数: {result_data.get('processed_pages', [])}")
            print(f"🌐 识别语言: {result_data.get('ocr_language', 'N/A')}")
            print(f"📦 文本块数量: {len(result_data.get('chunks', []))}")
            
            # 显示OCR摘要信息
            ocr_summary = result_data.get('ocr_summary', {})
            if ocr_summary:
                print(f"📊 平均置信度: {ocr_summary.get('average_confidence', 0):.3f}")
                print(f"📝 文本块总数: {ocr_summary.get('total_text_blocks', 0)}")
            
            # 显示前几个文本块的内容预览
            chunks = result_data.get('chunks', [])
            if chunks:
                print(f"\n📖 文本内容预览 (前2个块):")
                print("-" * 60)
                for i, chunk in enumerate(chunks[:2]):
                    content = chunk.get('content', '').strip()
                    page_num = chunk.get('page_number', 'N/A')
                    print(f"\n块 {i+1} (第{page_num}页):")
                    # 限制预览长度
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(preview)
                    
                print(f"\n💾 完整结果已保存到: ocr_result.json")
                
                # 保存完整结果
                with open('ocr_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                    
        else:
            print(f"❌ OCR识别失败: {result_data.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ocr())