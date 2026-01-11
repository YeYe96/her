#!/usr/bin/env python3
"""
测试脚本：查看 AI 推理的详细过程
"""
import asyncio
import sys
sys.path.insert(0, 'server')

from core.ai_service import get_ai_service

async def test_chat():
    """测试聊天功能"""
    ai_service = get_ai_service()
    
    print("="*70)
    print("测试开始：发送消息给 Amadeus")
    print("="*70)
    print()
    
    # 测试消息
    test_message = "你好，红莉栖！给我讲讲时间机器的原理吧。"
    
    # 调用 AI 服务（这里会输出详细的推理过程）
    reply, latency = await ai_service.chat(test_message)
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
    print(f"\n最终回复: {reply}\n")

if __name__ == "__main__":
    asyncio.run(test_chat())
