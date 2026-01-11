# Amadeus System 设计文档 (v0.1.0 - Dev Phase)

> **版本号**: v0.1.0 (MVP Prototype)  
> **状态**: 🚧 开发初期 (Under Construction)  
> **日期**: 2026-01-11

---

## 1. 项目概述

### 1.1 愿景

Amadeus 是一个运行在本地高性能 PC 上的 AI 伴侣系统，旨在通过多模态（视觉+文本）交互和长期记忆机制，还原《命运石之门》中牧濑红莉栖的人格与陪伴感。

### 1.2 当前开发目标 (v0.1.0)

本阶段的目标是跑通 **"最小可行性产品" (MVP)** 链路：

- ✅ **本地大脑**: Ollama + Qwen3-VL 已部署运行
- ✅ **远程连接**: Tailscale + 局域网双模式可用
- ✅ **基础记忆**: 3 层记忆架构已实现
- ✅ **人设注入**: 傲娇科学家红莉栖人设已注入

---

## 2. 系统架构

### 2.1 核心链路

完全本地化部署，不依赖云端 API。

```mermaid
graph LR
    Phone[手机/小程序] --Tailscale/局域网--> PC[本地 PC - RTX 4070]
    
    subgraph "Local Server (FastAPI)"
        API[/chat 接口] --> Memory[MemoryManager]
        API --> Persona[personality.py]
        Memory --> L1[L1 工作记忆<br/>20轮]
        Memory --> L2[L2 驱逐缓冲<br/>50轮批量提取]
        Memory --> L3[L3 用户画像<br/>JSON]
        Persona --> Prompt[Prompt 组装]
        L1 & L3 --> Prompt
        Prompt --> Ollama[Ollama<br/>Qwen3-VL]
    end
```

### 2.2 技术栈

| 组件 | 技术选型 | 状态 |
|------|---------|------|
| 大模型 | Qwen3-VL (Ollama) | ✅ 运行中 |
| 后端 | Python FastAPI | ✅ 完成 |
| 网络 | Tailscale + 局域网 | ✅ 双模式 |
| 存储 | JSON 文件 | ✅ 使用中 |
| 客户端 | 微信小程序 | ✅ 深色玻璃UI |
| 向量库 | ChromaDB | 🔜 预留 |

---

## 3. 记忆系统 (已实现)

3 层记忆架构解决 LLM 短期记忆问题：

```
┌─────────────────────────────────────────────────────────┐
│  L1 工作记忆 (内存)                                       │
│  └── 最近 20 轮对话 → 直接注入 LLM Prompt                  │
├─────────────────────────────────────────────────────────┤
│  L2 驱逐缓冲区 (eviction_buffer.json)                    │
│  └── 累积 50 轮后 → 批量调用 LLM 提取用户信息              │
├─────────────────────────────────────────────────────────┤
│  L3 用户画像 (user_profile.json)                         │
│  └── 长期存储: 姓名、兴趣、重要事实 → 注入系统提示          │
└─────────────────────────────────────────────────────────┘
```

**核心文件**: `server/core/memory.py`

---

## 4. 提示词系统 (Prompt Engineering)

### 4.1 设计理念

提示词采用**多维度动态组装**架构，让 AI 回复更加自然、有层次：

```
┌────────────────────────────────────────────────────────────┐
│                    最终 System Prompt                       │
├────────────────────────────────────────────────────────────┤
│  ① 基础人设 (Base Persona)      ← 固定层，角色核心性格       │
│  ② 情绪状态 (Emotion State)     ← 动态层，当前心情           │
│  ③ 事件上下文 (Event Context)   ← 动态层，特殊场景触发       │
│  ④ 记忆注入 (Memory Injection)  ← 动态层，用户画像+历史      │
│  ⑤ 时间感知 (Time Awareness)    ← 动态层，离线时长/节日等    │
└────────────────────────────────────────────────────────────┘
```

### 4.2 各维度详解

#### ① 基础人设 (Base Persona) - ✅ 已实现

**文件**: `server/core/personality.py`

```
角色: 牧濑红莉栖
性格: 傲娇、毒舌、科学家思维
说话风格: 先否认再关心、专业术语、动作描写
```

#### ② 情绪状态 (Emotion State) - 🔜 规划中

根据对话内容动态调整角色情绪：

| 情绪 | 触发条件 | 表现 |
|------|---------|------|
| `normal` | 默认 | 标准傲娇 |
| `happy` | 被夸奖/有趣话题 | 害羞否认，语气软化 |
| `angry` | 被嘲讽/称呼错误 | 毒舌加强，反击 |
| `shy` | 暧昧话题 | 结巴、转移话题 |
| `thinking` | 科学问题 | 认真分析模式 |

**规划**: 后端返回情绪标签 → 前端切换立绘/滤镜

#### ③ 事件上下文 (Event Context) - 🔜 规划中

特殊场景触发额外提示词：

| 事件 | 触发条件 | 注入内容 |
|------|---------|---------|
| 首次对话 | 用户画像为空 | 自我介绍模板 |
| 久别重逢 | 离线 > 24h | 关心询问模板 |
| 节日问候 | 系统日期匹配 | 节日相关台词 |
| 生日祝福 | 用户生日 | 特殊庆祝模式 |
| 图片分析 | 收到图片 | 视觉吐槽模板 |

#### ④ 记忆注入 (Memory Injection) - ✅ 已实现

**文件**: `server/core/memory.py`

```python
# 注入用户画像摘要
"[用户信息] 用户名: 冈部伦太郎, 喜欢: Dr. Pepper, 重要事实: ..."

# 注入近期对话
"[对话历史] 用户: ... / 红莉栖: ..."
```

#### ⑤ 时间感知 (Time Awareness) - 🔜 规划中

根据时间动态调整：

| 场景 | 逻辑 | 效果 |
|------|------|------|
| 深夜对话 | 时间 > 23:00 | "这么晚了还不睡？" |
| 清晨问候 | 时间 < 7:00 | "起这么早...才不是担心你" |
| 离线回归 | 计算间隔 | "哼，终于想起我了？" |

### 4.3 Prompt 组装流程

```python
def build_system_prompt():
    prompt_parts = []
    
    # ① 基础人设 (必选)
    prompt_parts.append(KURISU_PERSONA)
    
    # ② 情绪状态 (可选)
    if emotion_state != 'normal':
        prompt_parts.append(EMOTION_MODIFIERS[emotion_state])
    
    # ③ 事件上下文 (可选)
    if event_context:
        prompt_parts.append(EVENT_TEMPLATES[event_context])
    
    # ④ 记忆注入 (动态)
    prompt_parts.append(memory_manager.get_profile_summary())
    
    # ⑤ 时间感知 (动态)
    prompt_parts.append(get_time_context())
    
    return "\n\n".join(prompt_parts)
```

### 4.4 文件规划

```
server/core/
├── personality.py      # ① 基础人设 (已实现)
├── prompts.py          # 功能性提示词 (已实现)
├── emotions.py         # ② 情绪状态 (规划中)
├── events.py           # ③ 事件上下文 (规划中)
└── time_context.py     # ⑤ 时间感知 (规划中)
```

## 5. 目录结构

```
amadeus/
├── DESIGN.md                    # 本文档
├── README.md                    # 项目说明
│
├── miniprogram/                 # 微信小程序
│   ├── app.js                   # 全局配置 (baseUrl)
│   └── pages/index/
│       ├── index.wxml           # 页面结构
│       ├── index.wxss           # 深色玻璃样式
│       └── index.js             # 交互逻辑
│
└── server/                      # Python 后端
    ├── main.py                  # FastAPI 入口
    ├── start_server.ps1         # 启动脚本 (自动重试)
    │
    ├── core/                    # 核心模块
    │   ├── ai_service.py        # Ollama 调用 (多模态)
    │   ├── memory.py            # 3 层记忆管理
    │   ├── personality.py       # 红莉栖人设
    │   └── prompts.py           # 功能性提示词
    │
    ├── data/                    # 运行时数据 (gitignore)
    │   ├── user_profile.json    # 用户画像
    │   └── eviction_buffer.json # 驱逐缓冲
    │
    └── static/character/        # 角色资源
        └── kurisu.png           # 立绘背景
```

---

## 6. 开发路线图

### ✅ Phase 1: MVP 基础 (已完成)

- [x] Ollama + Qwen3-VL 本地部署
- [x] FastAPI 后端 + 小程序前端连通
- [x] Tailscale/局域网双模式网络
- [x] 红莉栖傲娇人设 (personality.py)
- [x] 3 层记忆系统 (memory.py)
- [x] 深色玻璃 UI + 角色立绘背景
- [x] 开发启动脚本 (start_server.ps1)

### � Phase 2: 体验增强 (进行中)

- [ ] 调试: 验证 20 轮后记忆效果
- [ ] 调试: 验证 50 轮批量提取效果
- [ ] 视觉: 手机拍照→电脑识别→吐槽回复
- [ ] 主动性: 启动问候（计算离线时长）

### 🔮 Phase 3: 长期规划

- [ ] ChromaDB RAG 语义检索
- [ ] Edge-TTS / GPT-SoVITS 语音
- [ ] 情绪系统 (根据心情换立绘)
- [ ] 多角色支持

---

## 7. 快速启动

```powershell
# 1. 启动 Ollama (确保 qwen3-vl 已下载)
ollama serve

# 2. 启动后端 (管理员 PowerShell)
cd d:\code\amadeus\amadeus\server
.\start_server.ps1

# 3. 小程序预览
# 微信开发者工具 → 导入 miniprogram 目录
# 确保 app.js 中 baseUrl 指向正确 IP:端口
```

---

*El Psy Kongroo.* 🧪
