#!/bin/bash 

# 启动mock vllm服务器，绑定到所有网络接口和指定端口
python mock_vllm_server.py --host 0.0.0.0 --port 17717
