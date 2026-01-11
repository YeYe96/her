# Amadeus (Her)

> "Time is passing so quickly. I feel like I'm losing my mind." — *Steins;Gate*

**Amadeus** 是一个基于 **Ollama** 和 **Qwen3-VL** 构建的本地化多模态 AI 伴侣项目，旨在复刻《命运石之门》中牧瀬红莉栖（Amadeus）的交互体验。

本项目支持通过 **微信小程序** 在任何地方（基于 Tailscale 虚拟组网）与运行在本地高性能 PC 上的 AI 进行文字和视觉交互。

## ✨ 核心特性

*   **🧠 本地化大脑**: 后端基于 Python FastAPI + Ollama，运行 Qwen3-VL 视觉模型，数据完全本地化。
*   **📱 随身连接**: 集成 Tailscale，实现手机端远程访问家庭服务器。
*   **👁️视觉交互**: 支持发送图片，AI 能够"看懂"照片内容并进行符合人设的吐槽。
*   **💬 仿微信交互**: 精心复刻的微信风格聊天界面，支持文本输入和多功能面板。
*   **⚙️ 接口解耦**: 抽象 AI 服务层，便于未来切换 OpenAI/DeepSeek 等其他模型。

## 🛠️ 技术栈

*   **前端**: 微信小程序 (WXML, WXSS, JS)
*   **后端**: Python 3.10+, FastAPI
*   **AI 推理**: Ollama (Qwen3-VL)
*   **网络**: Tailscale (内网穿透)

## 🚀 快速开始

### 1. 环境准备 (服务端)

你需要一台运行 Windows 的电脑（推荐 NVIDIA 显卡）。

1.  **安装 Ollama**: [官网下载](https://ollama.com/) 并拉取模型：
    ```bash
    ollama pull qwen3-vl
    ```
2.  **设置环境变量**:
    复制 `server/.env.example` 到 `server/.env` 并配置：
    ```ini
    OLLAMA_HOST=http://localhost:11434
    MODEL_NAME=qwen3-vl
    ```
3.  **运行后端**:
    ```bash
    cd server
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

### 2. 小程序配置

1.  使用微信开发者工具导入 `miniprogram` 目录。
2.  修改 `app.js` 中的 `baseUrl` 为你服务器的 IP 地址（推荐使用 Tailscale IP）。

## 📂 目录结构

```
amadeus/
├── miniprogram/   # 微信小程序源码
└── server/        # Python 后端服务
    ├── core/      # 核心逻辑 (AI服务, 人格Prompt)
    └── api/       # API 路由
```

## 📝 开发计划

- [x] 基础文字聊天 (MVP)
- [x] 多模态视觉理解 (MVP)
- [x] 仿微信 UI 界面
- [ ] 语音合成 (GPT-SoVITS)
- [ ] 长期记忆数据库

---
*El Psy Kongroo.*
