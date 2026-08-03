# AstrBot 随机二次元图片插件

从 yppp.net 获取随机二次元图片，支持多张图片一次性发送。

## ✨ 功能特点

- 🖼️ 获取随机二次元图片（横图/竖图随机）
- 🔢 支持数量参数，一次性发送多张图片
- 📨 多张图片合并为一条消息发送（消息链方式）
- ⚡ 并发请求，快速获取多张图片
- 🛡️ 自动限流保护，最多 15 张

## 📥 安装

### 方式一：通过 AstrBot WebUI 安装（推荐）

1. 在 AstrBot 管理面板中进入「插件管理」
2. 点击「插件市场」
3. 搜索 `random_image` 或 `二次元图片`
4. 点击安装

### 方式二：手动安装

1. 克隆本仓库到 `AstrBot/data/plugins/` 目录：
   ```bash
   cd AstrBot/data/plugins/
   git clone https://github.com/你的用户名/astrbot_plugin_random_image.git
