# 🧪 OptoAgent 功能测试方案

> 按顺序执行，每步标注了**预期结果**，方便对照判断是否通过。

---

## 〇、前置检查

```bash
# 确认包已安装
optoagent --help
```
✅ 预期：显示 7 个命令列表 (`add_experiment`, `run_cycle`, `list_papers` 等)

---

## 一、Storage 存储层

### 1.1 添加实验记录

```bash
optoagent add_experiment --title "量子点薄膜沉积测试" --desc "CdSe量子点旋涂在Si基底上" --results "膜厚50nm，均匀"
```
✅ 预期：日志输出 `Added experiment: 量子点薄膜沉积测试`

### 1.2 验证数据持久化

```bash
# 检查 experiments.json 是否生成
type data\experiments.json
```
✅ 预期：看到包含 `量子点薄膜沉积测试` 的 JSON 数据

### 1.3 列出论文 / 灵感

```bash
optoagent list_papers
optoagent list_ideas
```
✅ 预期：正常输出已有数据（如果之前有的话），无报错

---

## 二、论文搜索（模拟模式）

> 不需要 API Key，验证流程逻辑正确

### 2.1 临时清除 EXA Key 后搜索

```bash
# Windows PowerShell
$env:EXA_API_KEY=""; optoagent active_search --query "test query" --limit 2
```
✅ 预期：输出 `[Simulated] Searching for: test query`，返回 2 条模拟结果

---

## 三、论文搜索（Exa.ai 真实搜索）

> 需要 `.env` 中配置 `EXA_API_KEY`

### 3.1 主动搜索

```bash
optoagent active_search --query "miniaturized spectrometer" --limit 3
```
✅ 预期：
- 日志输出 `[Exa] Searching for: miniaturized spectrometer`
- 日志输出 `[Exa] Enriching metadata for 3 papers...`
- 看到 `✓ Authors enriched [semantic_scholar_doi]: ...` 或类似的元数据补全信息
- 找到 ≤3 篇论文，每篇有标题、URL 和真实作者列表
- 如果配了 OPENAI_API_KEY，还会看到 `Summarizing new paper: ...`

### 3.2 验证元数据补全质量

```bash
type data\papers.json | findstr "authors"
```
✅ 预期：authors 字段包含真实作者姓名（如 `"Kefan Song"`, `"Gang Wu"` 等），而非空列表 `[]`

### 3.3 监控追踪源

```bash
optoagent monitor_sources
```
✅ 预期：
- 日志输出 `Checking 9 Research Groups via Exa...`
- 逐个 Tracking Group 搜索
- 每组搜索后触发元数据补全

---

## 四、LLM 摘要 + Idea 生成

> 需要 `.env` 中配置 `OPENAI_API_KEY`（+ 可选 `OPENAI_BASE_URL`）

### 4.1 完整搜索循环

```bash
optoagent run_cycle --query "perovskite solar cell" --limit 2
```
✅ 预期：
1. 搜索论文
2. 元数据补全 → `✓ Authors enriched ...` / `✓ Abstract enriched ...`
3. 对新论文调用 LLM 做摘要 → `Summarizing new paper: ...`
4. RAG 检索知识库上下文 → `Retrieving context for: ...`
5. CoT 推理生成 Idea → `Generated new idea: ...`
6. 飞书通知发送（如果配了 webhook）

### 4.2 验证数据已存储

```bash
optoagent list_papers
optoagent list_ideas
```
✅ 预期：新搜到的论文和 Idea 出现在列表中

---

## 五、知识库 RAG

### 5.1 准备测试文档

手动在 `data/knowledge/` 下创建一个测试 Markdown：

```bash
echo "# 量子点光谱仪研究笔记`n`n我们课题组主要研究 CdSe/ZnS 量子点在微型光谱仪的应用。" > data\knowledge\test_rag.md
```

### 5.2 建立索引

```bash
optoagent index_knowledge
```
✅ 预期：`Indexed X chunks from local knowledge base.`
⚠ 如果 `data/knowledge/` 中有非 UTF-8 编码文件（如 UTF-16 BOM 文件），应正常处理而不崩溃

### 5.3 验证 RAG 增强

```bash
optoagent run_cycle --query "quantum dot spectrometer" --limit 1
```
✅ 预期：日志中出现 `Retrieving context for: ...`，且生成的 Idea 应与量子点相关

---

## 六、飞书通知

### 6.1 Webhook 通知（简单）

> 需要 `.env` 中配置 `FEISHU_WEBHOOK`

运行 `run_cycle` 后检查飞书群聊是否收到：
- 📄 论文通知（标题 + 作者 + 摘要）
- 💡 Idea 通知（标题 + 推理过程）

⚠ 如果看到日志 `Webhook returned error: status=200 body={"code":19007,...}`，说明飞书机器人未启用，请在飞书开放平台启用机器人能力。

### 6.2 交互式机器人

> 需要 `APP_ID` + `APP_SECRET` + 公网 Webhook 地址

```bash
python -m optoagent.server
```
然后在飞书群中发送：
```
search 钙钛矿量子点
```
✅ 预期：
1. 群内立即回复 `🔍收到指令：'钙钛矿量子点'`
2. 一段时间后收到论文和 Idea 推送

---

## 七、定时调度器

### 7.1 Dry Run（立即执行一次）

```bash
python -m optoagent.scheduler --dry-run
```
✅ 预期：立即执行 `monitor_sources` + `run_cycle`，然后退出

### 7.2 限次运行

```bash
python -m optoagent.scheduler --interval 1 --unit minutes --max-runs 2
```
✅ 预期：每分钟执行一次，2 次后打印 `Max runs reached. Exiting.` 并退出

---

## 八、日志系统

所有上述命令执行后检查：

```bash
type logs\optoagent.log
```
✅ 预期：看到格式化的日志，包含时间戳和模块名，例如：
```
[2026-02-18 21:30:00] INFO    optoagent.modules.searcher: [Exa] Searching for: ...
[2026-02-18 21:30:01] INFO    optoagent.modules.searcher:   ✓ Authors enriched [semantic_scholar_doi]: ...
```

---

## 九、自动化测试

```bash
python -m pytest tests/ -v
```
✅ 预期：9/9 PASSED

---

## 快速通过/失败判断表

| # | 测试项 | 需要的 Key | Pass 标志 |
|---|--------|-----------|-----------|
| 1 | `optoagent --help` | 无 | 显示命令列表 |
| 2 | `add_experiment` | 无 | experiments.json 有数据 |
| 3 | 模拟搜索 | 无 | `[Simulated]` 输出 |
| 4 | Exa 搜索 | EXA | `[Exa]` 输出 + 论文 |
| 5 | 元数据补全 | EXA | `✓ Authors enriched` |
| 6 | LLM 摘要 | OPENAI | `Summarizing new paper` |
| 7 | Idea 生成 | OPENAI | `Generated new idea` |
| 8 | 知识库索引 | 无 | `Indexed X chunks` |
| 9 | RAG 增强 | OPENAI | `Retrieving context` |
| 10 | 飞书通知 | FEISHU | 群内收到消息 |
| 11 | 调度器 | 视配置 | dry-run 正常退出 |
| 12 | 日志文件 | 无 | `logs/optoagent.log` 有内容 |
| 13 | pytest | 无 | 9/9 PASSED |
