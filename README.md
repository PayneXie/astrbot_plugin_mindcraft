# AstrBot Mindcraft Plugin

<div align="center">
  <img src="https://github.com/Soulter/AstrBot/raw/main/assets/logo_text.png" width="300" alt="AstrBot Logo">
  <h3>🧠 Mindcraft for AstrBot</h3>
  <p>将强大的 Minecraft AI Agent 接入您的 QQ/微信/Telegram 聊天机器人</p>
</div>

---

> [!NOTE]
> 本项目是 [Mindcraft](https://github.com/mindcraft-bots/mindcraft) 的 AstrBot 插件移植版。
> 它允许您通过聊天窗口直接控制和交互 Minecraft 中的 AI 代理。

## ✨ 功能特性

- **多模态交互**：通过聊天窗口与 Minecraft 里的 AI 对话，支持文字指令。
- **智能 Agent**：基于 LLM (GPT-4/Doubao/DeepSeek 等) 驱动的 AI，能理解复杂的自然语言指令。
- **自主行为**：支持生存模式下的自动采集、战斗、建造、合成等复杂任务。
- **实时反馈**：机器人的状态（生命、位置、背包）和行为日志会实时反馈到聊天窗口。
- **多模型支持**：支持 OpenAI, Anthropic, Google Gemini, DeepSeek, Doubao, Ollama 等 20+ 种模型后端。
- **权限管理**：内置白名单系统，防止未授权用户操控机器人。

## 📦 安装

1. 确保您已安装 [AstrBot](https://github.com/Soulter/AstrBot)。
2. 将本项目克隆或下载到 AstrBot 的 `data/plugins/` 目录下：
   ```bash
   cd data/plugins
   git clone https://github.com/your-repo/astrbot_plugin_mindcraft.git
   ```
3. 安装依赖：
   - 本插件依赖 Node.js 环境运行 Mindcraft 核心。请确保服务器已安装 [Node.js](https://nodejs.org/) (推荐 v18+)。
   - 在插件目录下运行：
     ```bash
     npm install
     ```
     或者在 AstrBot 中发送 `/mcinstall` 指令自动安装。

## ⚙️ 配置

建议使用 AstrBot 的 WebUI 进行配置（推荐）：
1. 打开 AstrBot 管理面板。
2. 进入 **插件管理** -> **Mindcraft Controller**。
3. 填写以下配置：
   - **Minecraft 服务器**：目标服务器地址 (`mc_host`) 和端口 (`mc_port`)。
   - **MindServer 配置**：本地 Node 服务端口，默认 `8076`。
   - **LLM 模型配置**：
     - `llm_api`: 选择模型服务商 (如 `openai`, `doubao`, `deepseek`)。
     - `llm_model`: 模型名称 (如 `gpt-4o`, `doubao-pro-32k`)。
     - `llm_api_key`: 对应的 API Key。
     - `llm_url`: (可选) 自定义 API 接口地址，例如 Ollama 的 `http://localhost:11434/v1`。
   - **Agent 设置**：机器人名称。
   - **权限白名单**：允许使用指令的 QQ 号列表。

## 🎮 指令列表

所有指令均需在聊天窗口发送。

| 指令 | 说明 | 示例 |
|------|------|------|
| `/mcstart` | 启动 Mindcraft 服务并连接机器人 | `/mcstart` |
| `/mcstop` | 停止 Mindcraft 服务并下线机器人 | `/mcstop` |
| `/mc [消息]` | 与机器人对话或下达指令 | `/mc 去帮我砍点木头` |
| `/mcinventory` | 查看机器人当前的背包、装备和状态 | `/mcinventory` |
| `/mcserver [地址]` | 临时修改目标 MC 服务器地址 | `/mcserver 192.168.1.10:25565` |
| `/mcinstall` | 自动安装 Node.js 依赖 (仅首次需要) | `/mcinstall` |

### 指令示例

- **启动机器人**：
  ```
  /mcstart
  ```
  > 机器人会启动 Node.js 进程，连接到配置的 MC 服务器，并生成 AI 代理。

- **让机器人干活**：
  ```
  /mc 请帮我收集 64 个橡木原木，并制作一个工作台。
  ```
  ```
  /mc 跟我来，保护我。
  ```

- **查询状态**：
  ```
  /mcinventory
  ```
  > 返回示例：
  > 📊 状态: MindBot
  > ❤️ 生命: 20.0 | 🍖 饥饿: 20.0
  > 📍 位置: (100, 64, -200) | 🎮 模式: survival
  > 🛡️ 装备:
  >   ✋ 主手: diamond_sword
  > 🎒 背包 (5/36):
  >   - oak_log: 32
  >   - bread: 10

## 🛠️ 常见问题

**Q: 启动时提示 `npm` 命令未找到？**
A: 请确保您的系统环境变量中已配置 Node.js。

**Q: 机器人进不去服务器？**
A: 
1. 检查服务器地址是否正确。
2. 如果是正版服务器，需配置微软账号认证（目前插件版默认为离线模式/盗版模式，正版登录需修改源码 `auth` 配置）。
3. 检查服务器是否有白名单或反作弊插件。

**Q: 机器人没有反应？**
A: 
1. 检查 `/mcstart` 是否成功。
2. 检查后台日志是否有报错。
3. 确认您是否在白名单内。

## 📄 开源协议

本项目基于 [Mindcraft](https://github.com/mindcraft-bots/mindcraft) 开发，遵循 MIT 协议。
Mindcraft 核心代码版权归原作者所有。
