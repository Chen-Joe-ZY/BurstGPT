import argparse
import asyncio
import json
import random
import time
from aiohttp import web

async def generate_response(request):
    # 记录连接信息
    remote_addr = request.remote
    print(f"[CONNECTION] New connection from {remote_addr}")
    
    # 记录接收到的请求内容
    data = await request.json()
    prompt = data.get("prompt", "")
    stream = data.get("stream", False)
    ignore_eos = data.get("ignore_eos", False)
    max_tokens = data.get("max_tokens", 128)
    temperature = data.get("temperature", 0)
    request_tokens = data.get("request_tokens", len(prompt.split()))
    response_tokens = data.get("response_tokens", max_tokens)
    
    print(f"[REQUEST] Received request: prompt_length={len(prompt)}, stream={stream}, max_tokens={max_tokens}, temperature={temperature}, request_tokens={request_tokens}, response_tokens={response_tokens}")
    
    # 生成模拟响应文本
    def generate_text(length):
        if length <= 0:
            return ""
        
        words = ["Hello", "world", "this", "is", "a", "mock", "response", "from", "vllm", "server", "testing", "streaming", "functionality", "with", "multiple", "chunks"]
        result = []
        current_length = 0
        
        while current_length < length:
            word = random.choice(words)
            # 如果是第一个单词，直接添加；否则需要考虑前面的空格
            if result:
                # 检查添加当前单词和空格后是否超过长度
                if current_length + 1 + len(word) <= length:
                    result.append(word)
                    current_length += 1 + len(word)  # 1代表空格
                else:
                    # 如果添加当前单词会超过长度，检查是否还能添加部分单词
                    remaining = length - current_length
                    if remaining > 0:
                        # 如果只剩一个字符，添加空格
                        if remaining == 1:
                            result.append(" ")
                            current_length += 1
                        else:
                            # 否则添加部分单词
                            result.append(word[:remaining - 1])
                            current_length += remaining
                    break
            else:
                # 第一个单词，考虑是否需要截断
                if len(word) <= length:
                    result.append(word)
                    current_length += len(word)
                else:
                    result.append(word[:length])
                    current_length = length
                    break
        
        return " ".join(result)
    
    response_text = generate_text(response_tokens)
    
    if stream:
        # 流式响应
        print(f"[RESPONSE] Sending streaming response with {len(response_text.split())} words")
        async def stream_response():
            # 模拟多个chunk的响应
            chunks = response_text.split()
            total_words = len(chunks)
            
            # 根据响应长度动态调整chunk大小，确保chunk数量合理（10-20个）
            if total_words <= 20:
                # 短响应：1-2个单词/块
                chunk_size = random.randint(1, 2)
            elif total_words <= 100:
                # 中等响应：3-6个单词/块
                chunk_size = random.randint(3, 6)
            else:
                # 长响应：5-10个单词/块
                chunk_size = random.randint(5, 10)
                
            chunk_count = 0
            
            for i in range(0, len(chunks), chunk_size):
                chunk = chunks[i:i+chunk_size]
                response_data = {
                    "text": [" ".join(chunk)],
                    "index": 0,
                    "finish_reason": None
                }
                chunk_count += 1
                print(f"[RESPONSE-CHUNK] Sending chunk {chunk_count}: {len(chunk)} words")
                yield json.dumps(response_data).encode("utf-8") + b"\0"
                # 模拟真实延迟，根据chunk大小调整延迟时间
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # 最后一个chunk
            final_data = {
                "text": [""],
                "index": 0,
                "finish_reason": "length"
            }
            print(f"[RESPONSE-CHUNK] Sending final chunk with finish_reason=length")
            yield json.dumps(final_data).encode("utf-8") + b"\0"
        
        return web.Response(body=stream_response(), content_type="application/json")
    else:
        # 非流式响应
        # 模拟真实延迟
        await asyncio.sleep(random.uniform(0.1, 1.0))
        
        response_data = {
            "text": [response_text],
            "index": 0,
            "finish_reason": "length"
        }
        
        print(f"[RESPONSE] Sending non-streaming response with {len(response_text.split())} words")
        return web.json_response(response_data)

async def health_check(request):
    return web.json_response({"status": "healthy"})

def main():
    parser = argparse.ArgumentParser(description="Mock VLLM Server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=17717, help="Server port")
    args = parser.parse_args()
    
    app = web.Application()
    app.add_routes([
        web.post("/generate", generate_response),
        web.get("/health", health_check)
    ])
    
    print(f"Mock VLLM Server starting on http://{args.host}:{args.port}")
    web.run_app(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
