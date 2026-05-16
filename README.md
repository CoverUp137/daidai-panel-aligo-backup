# daidai-panel-aligo-backup

呆呆面板 (Daidai Panel) 阿里云盘自动备份脚本，基于原青龙面板备份脚本适配而来。

> 原脚本为青龙面板设计，本项目针对 [linzixuanzz/daidai-panel](https://github.com/linzixuanzz/daidai-panel) 的目录结构进行了适配。

## 功能特性

- ☁️ **阿里云盘自动上传** — 备份完成后自动同步到阿里云盘指定目录
- 🗑️ **自动清理** — 本地 + 云端同步保留最新 N 份备份，超量自动删除旧备份
- 📦 **完整数据备份** — 打包整个 `Dumb-Panel` 数据目录（SQLite 数据库、脚本、依赖、JWT 密钥等）
- 🔕 **日志排除** — 默认排除 `logs/` 和 `backups/` 目录，避免备份体积过大和循环备份
- 📱 **消息推送** — 支持呆呆面板内置通知渠道（Bark、Telegram、Server酱、企业微信等）
- ⚙️ **环境变量配置** — 所有关键参数均可通过环境变量自定义

## 安装使用

### 1. 下载脚本

将 `dd_backup.py` 放入呆呆面板的脚本目录（通常是挂载的 `./Dumb-Panel/scripts/`）：

```bash
# 宿主机操作，假设你的 docker-compose 挂载了 ./Dumb-Panel在root目录
cd /root/Dumb-Panel/scripts
wget https://gh.0507.dpdns.org/https://raw.githubusercontent.com/CoverUp137/daidai-panel-aligo-backup/main/dd_backup.py
```

### 2. 创建定时任务

在呆呆面板 **定时任务** 中新建任务：

- **名称**：阿里云盘自动备份
- **命令**：`task daidai-panel-aligo-backup`
- **定时规则**：`0 2 * * *`（每天凌晨 2 点）

### 3. 安装依赖

在呆呆面板 **定时任务** **创建新任务** 直接执行备份脚本会自动安装依赖

或在呆呆面板 **依赖管理** 中添加 Python 依赖：

```
aligo
```

或进入容器执行：

```bash
docker exec -it daidai-panel pip install aligo
```

### 4. 配置环境变量（可选）

在呆呆面板 **环境变量** 中添加以下变量（均为可选，不填则使用默认值）：

| 变量名 | 说明 | 默认值 |
|---|---|---|
| `DD_EXCLUDE_NAMES` | 排除的目录名（逗号分隔） | `logs,backups` |
| `DD_BACKUPS_PATH` | 本地备份存放子目录 | `backups` |
| `DD_MAX_FILES` | 最大保留备份数量（本地+云端） | `5` |
| `DD_ALI_FOLDER` | 阿里云盘目标目录名 | `daidai-panel-backups` |


### 5. 首次运行

首次执行会触发阿里云盘扫码登录：

```
登录阿里云盘
请手动复制以下链接，打开阿里网盘App扫描登录
https://cli.im/api/qrcode/code?text=xxx
```

复制链接到浏览器，用阿里云盘 App 扫码即可完成授权。授权信息会自动保存，后续无需重复登录。

## 备份内容说明

脚本会打包整个 `/app/Dumb-Panel` 目录，包含：

```
Dumb-Panel/
├── daidai.db          # SQLite 数据库（所有面板数据）
├── .jwt_secret        # JWT 密钥（登录凭证）
├── panel.log          # 面板运行日志
├── deps/              # Python / Node.js 依赖
├── scripts/           # 脚本文件
├── logs/              # 任务执行日志（默认排除）
└── backups/           # 历史备份（默认排除）
```

> 默认排除 `logs/` 和 `backups/`，如需备份日志可修改 `DD_EXCLUDE_NAMES` 变量。

## 自动清理机制

当本地备份数量超过 `DD_MAX_FILES` 时：

1. 按文件**创建时间**排序，从最旧的开始删除
2. **本地文件删除的同时，会同步删除阿里云盘上的同名文件**
3. 最终本地和云端始终保持相同的最新 N 份备份

## 注意事项

1. **数据目录检测**：脚本优先检测 `/app/Dumb-Panel/`，如果未检测到会尝试当前目录下的 `./Dumb-Panel`
2. **阿里云盘 API**：基于 `aligo` 库，登录凭证保存在容器内，重建容器需重新扫码
3. **备份体积**：如果 `scripts/` 目录脚本很多，或 `deps/` 依赖很大，建议适当调高 `DD_MAX_FILES` 或定期手动清理
4. **与面板自带备份的区别**：呆呆面板 v2.2.3+ 已内置定时备份（一键导出/恢复），本脚本的优势是**自动上传到阿里云盘做异地备份**

## 开源协议

本项目基于原青龙备份脚本修改，遵循原项目协议。仅供学习交流使用。

## 相关项目

- [linzixuanzz/daidai-panel](https://github.com/linzixuanzz/daidai-panel) — 呆呆面板官方仓库
- [foyoux/aligo](https://github.com/foyoux/aligo) — 阿里云盘 Python SDK
