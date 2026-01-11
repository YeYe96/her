# Amadeus System 设计文档 (v2.0 - Local & Cloud Ready)

> **版本号**: v2.0  
> **核心变更**: 采用本地高性能算力 + 虚拟组网方案，确立多模态视觉交互核心。

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构-architecture)
3. [目录结构](#3-目录结构-project-structure)
4. [开发规划](#4-开发规划-roadmap)
5. [移植性设计规范](#5-移植性设计规范-portability-strategy)
6. [API 设计](#6-api-设计)
7. [人格系统设计](#7-人格系统设计-personality-system)
8. [前端设计](#8-前端设计)
9. [部署指南](#9-部署指南-deployment)
10. [依赖清单](#10-依赖清单)
11. [快速启动清单](#11-快速启动清单-action-items)

---

## 1. 项目概述

### 1.1 项目简介

Amadeus 是一个模拟《命运石之门》中人工智能系统的多模态聊天应用。

**当前阶段**利用开发者的高性能本地 PC 作为算力服务器，通过 **Tailscale** 构建虚拟局域网，实现移动端在任何网络环境下对"红莉栖"的远程访问。核心模型采用 **Qwen3-VL**，使其具备"看懂世界"的能力。

### 1.2 核心特性

| 特性 | 描述 |
| --- | --- |
| **🧠 本地化大脑** | 基于 `Qwen3-VL` 运行于 RTX 4070，阿里最新一代视觉语言模型。 |
| **🌏 随身连接** | 集成 `Tailscale`，无论在 4G/5G 还是公共 Wi-Fi 下，手机都能连接家中的 Amadeus。 |
| **👁️ 视觉交互** | 支持发送照片/截图，AI 能够识别环境细节并进行"红莉栖式"的吐槽。 |
| **🚀 云端就绪** | 架构设计遵循 Cloud-Native 标准，未来可无缝迁移至云端 GPU 服务器。 |

### 1.3 与 v1.0 的区别

| 方面 | v1.0 (旧方案) | v2.0 (新方案) |
| --- | --- | --- |
| **AI 算力** | OpenAI API (GPT-4o-mini) | 本地 Ollama (Qwen3-VL) |
| **网络方式** | 公网直连 | Tailscale 虚拟组网 |
| **成本** | 按 Token 计费 | 仅电费，长期免费 |
| **隐私** | 数据上传云端 | 数据完全本地化 |
| **多模态** | 依赖 OpenAI Vision | 本地视觉模型 |

---

## 2. 系统架构 (Architecture)

### 2.1 混合网络架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Mobile Device (Anywhere)                          │
│  ┌────────────────┐                                                      │
│  │  微信小程序     │ ──── HTTP Request ────┐                             │
│  │  / Web 客户端   │                        │                             │
│  └────────────────┘                        │                             │
└──────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     Tailscale Mesh Network (Encrypted)                   │
│                                                                          │
│     Client IP ◀══════════ WireGuard Tunnel ══════════▶ Server IP        │
│    (100.x.x.x)                                        (100.68.x.x)       │
└──────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    Home Server (RTX 4070 Laptop)                         │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      FastAPI Server (:8000)                      │    │
│  │  ┌───────────┐    ┌───────────┐    ┌───────────────────────┐   │    │
│  │  │  Routes   │───▶│ Controller│───▶│     AIService         │   │    │
│  │  │  /chat    │    │ (业务逻辑) │    │ (Ollama 接口封装)      │   │    │
│  │  └───────────┘    └───────────┘    └───────────┬───────────┘   │    │
│  └─────────────────────────────────────────────────│───────────────┘    │
│                                                    │                     │
│  ┌─────────────────────────────────────────────────▼───────────────┐    │
│  │                     Ollama Service (:11434)                      │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │                      Qwen3-VL Model                      │    │    │
│  │  │              (Local Inference via Ollama)                │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Future: Memory Layer                          │   │
│  │  ┌───────────────┐    ┌───────────────┐    ┌────────────────┐   │   │
│  │  │   SQLite      │    │   ChromaDB    │    │  GPT-SoVITS    │   │   │
│  │  │  (对话历史)    │    │  (向量记忆)    │    │   (TTS 语音)   │   │   │
│  │  └───────────────┘    └───────────────┘    └────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选型

| 模块 | 技术组件 | 选型理由 |
| --- | --- | --- |
| **前端** | 微信小程序 / Web | 轻量级，便于手机端快速验证。 |
| **网络层** | **Tailscale** | 零配置实现内网穿透，安全、稳定、免费。 |
| **后端框架** | **FastAPI** | 高性能异步 Python 框架，自动生成 API 文档。 |
| **AI 推理** | **Ollama** | 极简部署，提供标准 REST API，支持并发。 |
| **核心模型** | **Qwen3-VL** | 阿里最新一代开源视觉语言模型，支持多种尺寸，RTX 4070 可运行。 |
| **配置管理** | **python-dotenv** | 环境变量管理，支持开发/生产环境切换。 |

---

## 3. 目录结构 (Project Structure)

```
amadeus/
├── DESIGN.md                    # 本设计文档
│
├── miniprogram/                 # 微信小程序前端
│   ├── app.js                   # 小程序入口
│   ├── app.json                 # 全局配置
│   ├── app.wxss                 # 全局样式
│   ├── project.config.json      # 项目配置
│   ├── assets/                  # 静态资源
│   │   └── amadeus_logo.png     # Amadeus Logo
│   └── pages/
│       └── index/               # 主页面
│           ├── index.js         # 页面逻辑
│           ├── index.json       # 页面配置
│           ├── index.wxml       # 页面结构
│           └── index.wxss       # 页面样式
│
└── server/                      # Python 后端服务
    ├── .env                     # 环境变量 (不提交 Git)
    ├── .env.example             # 环境变量示例
    ├── main.py                  # FastAPI 应用入口
    ├── requirements.txt         # Python 依赖
    │
    ├── config/                  # 配置模块
    │   ├── __init__.py
    │   └── settings.py          # 环境变量加载
    │
    ├── api/                     # API 路由层
    │   ├── __init__.py
    │   └── routes.py            # 路由定义
    │
    ├── core/                    # 核心业务层
    │   ├── __init__.py
    │   ├── personality.py       # 人格 Prompt 定义
    │   └── ai_service.py        # AI 服务封装 (Ollama)
    │
    └── models/                  # 数据模型 (Future)
        ├── __init__.py
        └── schemas.py           # Pydantic 模型
```

---

## 4. 开发规划 (Roadmap)

### 4.1 阶段一：MVP (最小可行性产品) 🎯 当前

**目标**：跑通全流程，手机能远程让电脑里的红莉栖"看图说话"。

#### 基础设施搭建
- [ ] PC 端安装 Ollama 并拉取 `qwen3-vl`
- [ ] PC 端与手机端安装 Tailscale 并互通测试（Ping 通）
- [ ] 配置 Ollama 监听 `0.0.0.0` 允许外部访问

#### 后端开发 (Python)
- [ ] 重构 FastAPI 框架，添加 `config/settings.py`
- [ ] 实现 `AIService` 类封装 Ollama 调用
- [ ] 支持多模态输入（文本 + Image Base64）
- [ ] 注入牧濑红莉栖人格 System Prompt

#### 前端开发
- [ ] 更新 `app.js` 中的 `baseUrl` 为 Tailscale IP
- [ ] 优化聊天界面交互体验
- [ ] 测试拍照/相册发送图片功能

### 4.2 阶段二：体验升级 (Enhancement)

**目标**：增加沉浸感，让她"活"过来。

| 功能 | 技术方案 | 优先级 |
| --- | --- | --- |
| **对话历史** | SQLite 存储聊天记录 | 🔴 高 |
| **长期记忆** | ChromaDB 向量数据库 + RAG | 🟡 中 |
| **流式输出** | SSE 实现打字机效果 | 🟡 中 |
| **语音输出** | GPT-SoVITS 克隆牧濑红莉栖声音 | 🟢 低 (暂缓) |
| **情感表情** | 根据情绪返回不同表情图 | 🟢 低 |

### 4.3 阶段三：商业化与移植 (Future)

**目标**：脱离本地 PC，部署至云端，服务更多用户。

- [ ] 编写 `Dockerfile`，容器化 FastAPI 服务
- [ ] 编写 `docker-compose.yml`，编排多服务
- [ ] 租用 GPU 云主机（AutoDL / AWS / 阿里云）
- [ ] 实现多用户鉴权系统
- [ ] 添加用户数据隔离

---

## 8. 前端设计

### 8.1 UI 设计规范

**主题**：赛博朋克 / 科幻终端 + 仿微信交互

| 元素 | 颜色 | 说明 |
| --- | --- | --- |
| 背景 | `#000000` | 纯黑 |
| 主色调 | `#00ff00` | 霓虹绿 (Amadeus 标志色) |
| Amadeus 消息 | `#002200` 背景 + `#00ff00` 文字 | 终端风格 |
| 用户消息 | `#95ec69` 背景 + `#000000` 文字 | 仿微信绿气泡 |
| 底部交互 | `白色/极简` | 默认文本输入，去语音，保留拓展面板 (+) |


### 8.2 配置更新

```javascript
// miniprogram/app.js
App({
    globalData: {
        userInfo: null,
        // 更新为 Tailscale IP
        baseUrl: 'http://100.68.x.x:8000'  // 替换为实际 Tailscale IP
    }
})
```

---

## 9. 部署指南 (Deployment)

### 9.1 本地开发环境

#### Step 1: 安装 Ollama

```powershell
# Windows - 下载安装包
# https://ollama.com/download

# 拉取 Qwen3-VL 模型
ollama pull qwen3-vl

# 验证安装
ollama list
```

#### Step 2: 配置 Ollama 外部访问

```powershell
# Windows - 设置环境变量
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")

# 重启 Ollama 服务
```

#### Step 3: 安装 Tailscale

1. 下载安装 [Tailscale](https://tailscale.com/download)
2. 登录账号，获取分配的 IP (如 `100.68.x.x`)
3. 手机端也安装并登录同一账号
4. 测试连通性：`ping 100.68.x.x`

#### Step 4: 启动后端服务

```powershell
# 进入后端目录
cd amadeus/server

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
copy .env.example .env
# 编辑 .env 配置

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 5: 验证服务

```powershell
# 本地测试
curl http://localhost:8000/health

# 手机端测试（通过 Tailscale IP）
# 浏览器访问 http://100.68.x.x:8000/docs
```

### 9.2 生产环境部署 (Future)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 10. 依赖清单

### 10.1 Python 依赖

```txt
# server/requirements.txt

# Web 框架
fastapi>=0.109.0
uvicorn[standard]>=0.27.0

# HTTP 客户端
httpx>=0.26.0

# 数据验证
pydantic>=2.5.0

# 配置管理
python-dotenv>=1.0.0

# 文件处理
python-multipart>=0.0.6

# Future: 数据库
# sqlalchemy>=2.0.0
# chromadb>=0.4.0
```

### 10.2 系统依赖

| 组件 | 版本要求 | 用途 |
| --- | --- | --- |
| Python | >= 3.10 | 后端运行环境 |
| Ollama | >= 0.1.0 | 本地 LLM 推理 |
| Tailscale | Latest | 虚拟组网 |
| RTX 4070 | 8GB+ VRAM | GPU 推理加速 |

---

## 11. 快速启动清单 (Action Items)

### ✅ 今日任务

1. **Tailscale 配置**
   - [ ] 电脑安装并登录 → 获得 IP (如 `100.68.x.x`)
   - [ ] 手机安装并登录 → 确保显示 "Active"
   - [ ] 测试互通：手机 Ping 电脑 IP

2. **Ollama 验证**
   - [ ] 安装 Ollama
   - [ ] 拉取模型：`ollama pull qwen3-vl`
   - [ ] 设置 `OLLAMA_HOST=0.0.0.0`
   - [ ] 重启 Ollama 服务

3. **后端原型**
   - [ ] 创建 `config/settings.py`
   - [ ] 重构 `api/routes.py` 使用 Ollama
   - [ ] 手机浏览器访问 `http://100.68.x.x:8000/docs` 验证

4. **端到端测试**
   - [ ] 小程序修改 `baseUrl` 为 Tailscale IP
   - [ ] 发送文字消息测试
   - [ ] 发送图片测试多模态

---

## 附录

### A. 常见问题

**Q: Ollama 显存不够怎么办？**
A: 使用量化版本：`ollama pull qwen3-vl:latest` 或查看 Ollama 支持的具体量化标签。

**Q: 手机连不上服务器？**
A: 检查 Tailscale 是否都在线，确认防火墙允许 8000 端口。

**Q: 响应很慢？**
A: 首次加载模型需要时间，后续请求会快很多。可以在 Ollama 启动后先发一条预热消息。

### B. 参考资料

- [Ollama 官方文档](https://ollama.com/docs)
- [Tailscale 快速入门](https://tailscale.com/kb/start)
- [Qwen3-VL 模型介绍](https://huggingface.co/Qwen/Qwen3-VL)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)

---

*El Psy Kongroo.*
