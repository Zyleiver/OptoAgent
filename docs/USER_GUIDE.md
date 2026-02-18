# 📘 OptoAgent 用户使用指南

> 本文档将引导你从零开始配置并使用 OptoAgent，让 AI 成为你的科研助手。

---

## 一、环境准备

### 1.1 系统要求

- **Python** 3.9 或更高版本
- **pip** 包管理器
- 稳定的网络连接（访问 Exa.ai、OpenAI API、飞书 API）

### 1.2 安装

```bash
# 克隆项目
git clone https://github.com/Zyleiver/OptoAgent.git
cd OptoAgent

# 创建虚拟环境（推荐）
python -m venv .venv

# Windows 激活
.venv\Scripts\activate
# macOS/Linux 激活
# source .venv/bin/activate

# 安装（含开发依赖）
pip install -e ".[dev]"
```

安装完成后，`optoagent` 命令将全局注册到虚拟环境中。

### 1.3 配置 API 密钥

1. 复制环境变量模板:

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API 密钥:

```env
# LLM 服务（必需 — 用于摘要与灵感生成）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1    # 可替换为兼容 API
OPENAI_MODEL=gpt-4o                           # 可选，默认 gpt-4o

# Exa.ai 搜索（必需 — 用于论文搜索）
EXA_API_KEY=exa-xxxxxxxxxxxxxxxx

# 飞书通知（可选 — 用于消息推送）
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx

# 飞书 App API（可选 — 用于交互式机器人）
APP_ID=cli_xxxxxxxx
APP_SECRET=xxxxxxxxxxxxxxxx
```

> **💡 提示**：没有 API Key 的模块会自动降级为模拟模式，你可以先不配置全部 Key 来体验基本功能。

### 1.4 业务配置

编辑 `config.yaml` 来自定义搜索、调度、追踪源等所有业务参数（API 密钥除外，始终在 `.env` 中管理）。

主要可配置项：

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `search.default_query` | config.yaml | 默认搜索关键词 |
| `search.default_limit` | config.yaml | 每次搜索返回论文数 |
| `search.days_back` | config.yaml | 只搜索最近 N 天的论文（默认 30） |
| `search.academic_domains` | config.yaml | 限定搜索的 15 个学术域名 |
| `scheduler.interval` | config.yaml | 定时任务间隔 |
| `tracking.research_groups` | config.yaml | 9 大出版商追踪查询配置 |
| `journals.target_journals` | config.yaml | 60+ 目标期刊列表 |

---

## 二、快速上手

### 2.1 主动搜索论文

```bash
optoagent active_search --query "miniaturized spectrometer" --limit 5
```

OptoAgent 会自动：
1. ✅ 在 15 个高影响力学术域名中搜索最近 30 天的论文
2. ✅ 通过 Exa highlights + summary 提取干净的论文内容
3. ✅ 通过 Semantic Scholar / CrossRef 补全准确的作者和摘要
4. ✅ 用 LLM 生成每篇论文的结构化摘要
5. ✅ 存入本地论文库 (`data/papers.json`)
6. ✅ 通过飞书推送通知（如已配置）

### 2.2 完整搜索+灵感生成循环

```bash
optoagent run_cycle --query "2D material optoelectronics" --limit 3
```

在 `active_search` 的基础上，额外：
- 💡 基于搜到的论文 + 已有实验记录 + 知识库上下文
- 💡 使用 Chain-of-Thought 推理生成一个科研灵感
- 💡 灵感存入 `data/ideas.json` 并推送飞书

### 2.3 监控期刊更新

```bash
optoagent monitor_sources
```

自动检查 `config.yaml` 中配置的 9 大出版商的最新论文。

---

## 三、全部 CLI 命令速查

| 命令 | 说明 | 示例 |
|------|------|------|
| `active_search` | 主动搜索论文 | `optoagent active_search --query "量子点" --limit 5` |
| `run_cycle` | 搜索 + 摘要 + Idea 生成 | `optoagent run_cycle --query "光谱成像"` |
| `monitor_sources` | 监控追踪源更新 | `optoagent monitor_sources` |
| `list_papers` | 列出已收录论文 | `optoagent list_papers` |
| `list_ideas` | 列出已生成灵感 | `optoagent list_ideas` |
| `add_experiment` | 添加实验记录 | `optoagent add_experiment --title "实验1" --desc "描述"` |
| `index_knowledge` | 索引本地知识库 | `optoagent index_knowledge` |

### 命令参数说明

| 参数 | 适用命令 | 说明 |
|------|---------|------|
| `--query` | `active_search`, `run_cycle` | 搜索关键词，支持 OR 布尔语法 |
| `--limit` | `active_search`, `run_cycle` | 返回论文数量，默认 5 |
| `--title` | `add_experiment` | 实验标题（必需） |
| `--desc` | `add_experiment` | 实验描述（必需） |
| `--results` | `add_experiment` | 实验结果，默认 "Pending" |
| `--chat_id` | 所有搜索命令 | 指定飞书群聊 ID |

---

## 四、定时自动运行

### 4.1 使用内置调度器

```bash
# 每 6 小时自动搜索一次（默认，可在 config.yaml 中修改）
python -m optoagent.scheduler

# 自定义频率
python -m optoagent.scheduler --interval 30 --unit minutes --query "perovskite solar cell"

# 先试运行一次
python -m optoagent.scheduler --dry-run
```

| 参数 | 说明 | 默认值 |
|------|------|-------|
| `--interval` | 运行间隔 | 6（从 config.yaml 读取） |
| `--unit` | 时间单位 (`minutes` / `hours`) | hours |
| `--query` | 搜索关键词 | 从 config.yaml 读取 |
| `--dry-run` | 立即执行一次后退出 | - |
| `--max-runs` | 最大运行次数 (0=无限) | 0 |

### 4.2 使用 Docker 部署

```bash
# 构建镜像
docker build -t optoagent .

# 运行容器（挂载 data 和 logs 目录实现持久化）
docker run -d \
  --name optoagent \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  optoagent
```

---

## 五、飞书机器人交互

### 5.1 启动 Webhook 服务

```bash
python -m optoagent.server
```

服务将在 `http://0.0.0.0:5000` 启动，Webhook 端点为 `/feishu_webhook`。

### 5.2 配置飞书机器人

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用 → 获取 `APP_ID` 和 `APP_SECRET`
3. 启用 **机器人** 能力
4. 添加事件订阅 → 订阅 `im.message.receive_v1`
5. 填写请求地址: `https://你的服务器域名/feishu_webhook`
6. 将 `APP_ID` 和 `APP_SECRET` 填入 `.env` 文件

### 5.3 在飞书中使用

在机器人所在的群聊中发送消息即可触发搜索：

```
search 钙钛矿太阳能电池
```

```
research miniaturized spectrometer
```

> 以 `search` 或 `research` 开头的消息会触发论文搜索 + Idea 生成，结果将自动回复到群聊中。

---

## 六、知识库 (RAG) 使用

### 6.1 添加研究资料

将你的研究笔记、文献综述、实验记录放入 `data/knowledge/` 目录：

```
data/knowledge/
├── 光谱仪综述笔记.md
├── 实验方案_量子点制备.txt
├── group_papers/
│   └── 重要论文全文.pdf
└── reviews/
    └── 文献综述.md
```

支持的文件格式：`.md`、`.txt`、`.pdf`（自动递归扫描子目录）

> **💡 编码支持**：文件可以是 UTF-8、UTF-16、GBK 等编码，OptoAgent 会自动检测并正确读取。

### 6.2 建立索引

```bash
optoagent index_knowledge
```

OptoAgent 会将所有文档按 1000 字符分块，使用 `all-MiniLM-L6-v2` 嵌入模型生成向量，存入 ChromaDB。

### 6.3 RAG 自动增强

索引建立后，每次运行 `run_cycle` 时：
1. OptoAgent 会根据新发现的论文标题和摘要，自动从知识库中检索最相关的 3 个片段
2. 这些上下文会被注入 IdeaGenerator 的 Prompt 中
3. 使得生成的科研 Idea 更贴合你的研究方向和已有工作

---

## 七、元数据补全

OptoAgent 在搜索论文后，会自动通过学术 API 补全准确的 **作者列表** 和 **论文摘要**：

### 补全流程

1. **从 URL 提取 DOI** — 支持 nature.com、science.org、wiley.com、acs.org 等主流出版商
2. **查询 Semantic Scholar** — 通过 DOI 获取准确的作者和摘要
3. **查询 CrossRef** — 如 Semantic Scholar 未收录，通过 CrossRef DOI 查询
4. **标题搜索** — 如无法提取 DOI，通过标题模糊搜索 Semantic Scholar
5. **保留 Exa 数据** — 以上均未命中时，使用 Exa AI 生成的摘要

### 补全效果

| 数据来源 | Authors | Abstract |
|----------|---------|----------|
| Semantic Scholar (DOI) | ✅ 准确完整 | ✅ 论文原始摘要 |
| CrossRef (DOI) | ✅ 准确完整 | ⚠️ 部分期刊无摘要 |
| Semantic Scholar (标题搜索) | ✅ 大概率命中 | ✅ 论文原始摘要 |
| Exa 原始数据 (fallback) | ❌ 通常为空 | ⚠️ AI 生成摘要 |

> **⚠ 注意**：极新论文（发表 < 7 天）可能尚未被 Semantic Scholar 收录，此时使用 Exa AI summary 作为 fallback。

---

## 八、自定义追踪源

编辑 `config.yaml` 的 `tracking` 部分来添加你关注的出版商或课题组：

```yaml
tracking:
  rss_feeds:
    - "https://www.nature.com/nphoton.rss"

  research_groups:
    - name: "你关注的课题组"
      query: "site:目标网站.com 相关关键词"
```

---

## 九、常见问题

### Q: 没有 API Key 能用吗？

可以。所有模块都有模拟模式，搜索会返回占位数据，摘要会生成简单文本。适合先了解工作流。

### Q: 支持其他 LLM 吗？

支持。只要兼容 OpenAI Chat API 格式，设置 `OPENAI_BASE_URL` 即可接入（如 Azure OpenAI、本地 Ollama、DeepSeek 等）。

### Q: 论文会重复添加吗？

不会。Storage 模块会通过论文标题进行不区分大小写的去重。

### Q: 数据存在哪里？

- 论文和灵感存储在 `data/papers.json` 和 `data/ideas.json`
- 实验记录存储在 `data/experiments.json`
- 向量索引存储在 `data/chroma_db/` 目录
- 研究笔记原文在 `data/knowledge/` 目录
- 日志输出在 `logs/optoagent.log`

### Q: 配置文件在哪里？

- **API 密钥** → `.env` 文件
- **所有业务配置** → `config.yaml`（搜索参数、调度频率、追踪源、目标期刊等）

### Q: 论文的作者信息为什么有时为空？

Exa.ai 搜索 API 不直接返回作者信息。OptoAgent 通过 Semantic Scholar 和 CrossRef 自动补全，但极新论文（< 7 天）或非标准出版页面可能无法补全。如需 100% 覆盖，建议配合 Google Scholar 手动确认。

### Q: 搜索结果不够新怎么办？

调整 `config.yaml` 中的 `search.days_back` 参数（默认 30 天）。减小数值只搜索更近期的论文，增大数值扩大搜索范围。
