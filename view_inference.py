#!/usr/bin/env python3
"""
查看 AI 推理过程的测试脚本
运行: python view_inference.py
"""
import asyncio
import sys
from pathlib import Path

# 添加 server 目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'server'))

from core.ai_service import get_ai_service

async def main():
    """测试并展示完整的推理过程"""
    print("\n" + "="*70)
    print("Amadeus AI 推理过程展示")
    print("="*70)
    print("\n提示: 推理过程会在下方实时显示，请耐心等待 20-40 秒...\n")
    
    ai_service = get_ai_service()
    
    # 获取用户输入
    test_message = input("请输入你想问红莉栖的问题（直接回车使用默认问题）：").strip()
    if not test_message:
        test_message = "你好，红莉栖！给我讲讲时间机器的原理吧。"
    
    print(f"\n正在发送: {test_message}\n")
    print("="*70)
    
    # 调用 AI 服务（会自动显示详细的推理过程）
    try:
        reply, latency = await ai_service.chat(test_message)
        
        print("\n" + "="*70)
        print("推理完成！")
        print("="*70)
        print(f"\n最终回复:\n{reply}\n")
        print(f"总耗时: {latency}ms ({latency/1000:.2f}秒)")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n错误: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
