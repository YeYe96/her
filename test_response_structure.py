#!/usr/bin/env python3
"""
测试 Ollama API 响应结构，查看是否包含 thinking/reasoning 信息
"""
import asyncio
import sys
import json
sys.path.insert(0, 'server')

import httpx
from config.settings import settings

async def test_response_structure():
    """测试 Ollama API 响应结构"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": settings.MODEL_NAME,
                "messages": [
                    {"role": "user", "content": "2+2等于几？"}
                ],
                "stream": False
            },
            timeout=60
        )
        
        result = response.json()
        
        print("="*70)
        print("Ollama API Response Structure:")
        print("="*70)
        try:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        print("="*70)
        print("\n响应字段列表:")
        for key in result.keys():
            print(f"  - {key}: {type(result[key]).__name__}")
        
        # 检查是否有 thinking/reasoning 相关字段
        print("\n检查 thinking/reasoning 相关字段:")
        thinking_fields = []
        for key in result.keys():
            if any(word in key.lower() for word in ['think', 'reason', 'reasoning', 'thought', 'chain']):
                thinking_fields.append(key)
        
        if thinking_fields:
            print(f"  找到 thinking 相关字段: {thinking_fields}")
            for field in thinking_fields:
                print(f"\n  {field}:")
                print(f"    {result[field]}")
        else:
            print("  未找到 thinking/reasoning 相关字段")
        
        # 检查 message 结构
        if "message" in result:
            print("\nMessage 字段结构:")
            msg = result["message"]
            for key in msg.keys():
                print(f"  - {key}: {type(msg[key]).__name__}")

if __name__ == "__main__":
    asyncio.run(test_response_structure())
