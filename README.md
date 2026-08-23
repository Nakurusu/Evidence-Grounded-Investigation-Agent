# Investigative Data Analyst

Investigative Data Analyst 是一个面向结构化数据的 AI 调查分析引擎。它可以把 CSV 或 Excel 数据逐步转化为数据画像、异常信号、调查问题、假设、证据、候选原因、自然语言总结和可继续运行的后续分析。

项目重点是“调查”而不是单纯“报表”。系统不会只给出描述性统计或图表，而是帮助用户从原始数据出发，逐步缩小业务问题的可能解释范围，并说明每个结论背后的证据、置信度和限制。

## 当前状态

MVP 主线已经完成。系统同时支持探索驱动分析和问题驱动调查。

| 模块 | 状态 |
|---|---|
| 核心 pipeline、数据画像、信号检测、假设、证据、验证 | 已完成 |
| 问题驱动调查 | 已完成 |
| 字段语义角色识别 | 已完成 |
| 候选原因排序 | 已完成 |
| 可运行 follow-up 分析 | 已完成 |
| LLM 叙事层与 mock fallback | 已完成 |
| 多数据集调查图谱 | 已完成 |

## 系统能做什么

用户上传结构化数据集后，可以选择输入一个业务问题，例如“为什么收入下降？”或“哪些地区表现异常？”。系统会返回一个结构化的 `AIInvestigationReport`，其中包含：

| 输出 | 作用 |
|---|---|
| 数据画像 | 字段类型、语义角色、缺失率、标识符识别 |
| 信号报告 | 异常值、趋势、偏态、集中度、高基数、低方差等信号 |
| 调查问题 | 基于检测信号生成的后续调查问题 |
| 假设 | 对观察到的模式生成简单假设和组合假设 |
| 证据 | 支持、反驳或削弱假设的统计证据 |
| 发现 | 面向业务阅读的发现，包含证据强度和不确定性说明 |
| 候选原因 | 基于确定性证据排序的 3 到 5 个可能解释 |
| AI 叙事 | 基于结构化报告生成的自然语言总结 |
| 交互式调查 | 后续问题、数据缺口、调查路径和可运行的 drill-down 结果 |

## 调查流程

```text
CSV / Excel
    ↓
Parser + Normalizer
    ↓
Dataset Profile
    ↓
Signal Detection
    ↓
Question Generation
    ↓
Hypothesis Generation
    ↓
Evidence Generation
    ↓
Hypothesis Validation
    ↓
Investigation Report
    ↓
LLM Narrative
    ↓
Interactive Investigation
```

每一层都消费上一层的输出。确定性服务负责生成信号、证据、置信度和验证状态；LLM 只负责把这些结构化结果解释成自然语言，不负责创造或修改分析结论。

## MVP 亮点

### 问题驱动调查

用户可以在上传数据时输入一个可选调查问题。该问题会影响信号、发现和候选原因的排序与展示，但不会过滤掉无关证据，也不会让 LLM 改写确定性结论。

### 字段语义角色

Profiler 会识别 `metric`、`dimension`、`time`、`entity`、`identifier` 等分析角色。系统因此可以避免把 ID 当作普通维度，并更可靠地选择趋势分析、集中度分析和 drill-down 分析所需字段。

### 候选原因排序

报告会根据证据数量、置信度、问题相关性、数据质量限制，以及多个信号是否指向同一解释来排序候选原因。候选原因被表述为需要继续验证的假设，而不是确定的根因。

### 可运行 follow-up

部分后续调查问题可以基于原始上传数据继续运行确定性分析。新结果会追加到交互式调查层，不会覆盖原始报告。

当前支持的 drill-down 分析：

| 信号类型 | 分析类型 | 检查内容 |
|---|---|---|
| 异常值与偏态 | `tail_records` | 尾部记录、异常记录及其贡献 |
| 上升或下降趋势 | `trend_by_dimension` | 哪些维度分组推动了趋势 |
| 高集中度 | `top_category_vs_rest` | 头部类别与其他类别的贡献对比 |
| 高缺失率 | `missingness_by_dimension` | 缺失是否集中在特定分组 |
| 高基数 | `cardinality_distribution` | 值频率分布与覆盖阈值 |
| 低方差 | `low_variance_distribution` | 变异系数与主导值分布 |

## 示例

仓库 `examples/` 目录下包含多组演示数据集，覆盖单数据集调查和多数据集跨分析两种场景。

### 场景一：单数据集调查 + drill-down

使用 `examples/demo_retail_revenue.csv`（60 行，5 个区域 × 12 个月的零售收入数据）。

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@examples/demo_retail_revenue.csv" \
  -F "investigation_question=为什么收入下降"
```

该数据集会触发以下信号：

| 信号 | 触发原因 |
|---|---|
| `DECREASING_TREND` | revenue 从 620 降至 160（-74%） |
| `HIGH_CONCENTRATION` | East 区域占 revenue 的 50.5% |
| `HIGH_MISSING_RATE` | satisfaction_score 在 North 区域 9/12 个月缺失 |

报告中会生成 2-3 个候选原因，每个都带证据和限制说明。点击 follow-up 的"运行分析"按钮可以执行 drill-down，例如按 `region` 拆解趋势，确认 East 是下降的主要驱动因素。

### 场景二：多数据集跨分析

在主数据集基础上添加 `examples/demo_customer_complaints.csv`（60 行，共享 `date` 和 `region` 维度）。

```bash
curl -X POST "http://localhost:8000/upload/investigate/" \
  -F "primary_file=@examples/demo_retail_revenue.csv" \
  -F "secondary_files=@examples/demo_customer_complaints.csv" \
  -F "investigation_question=为什么收入下降"
```

跨数据集分析会检测到：

| 关系类型 | 说明 |
|---|---|
| `shared_dimension` | 两个数据集共享 `date`、`region` 两个维度 |
| `opposite_trend` | revenue 下降 vs complaint_count 上升（+487%） |
| `complementary_signal` | East 的集中度风险 + 投诉趋势上升，可能相互关联 |

辅助数据集为"收入下降"提供了新的证据维度：投诉激增可能是收入下降的关联因素。

### 其他数据集

| 文件 | 场景 | 说明 |
|---|---|---|
| `demo_sales.csv` | 多区域销售 | 异常值、右偏、集中度、下降趋势 |
| `demo_churn.csv` | 订阅流失 | 缺失值、套餐集中度、消费下降 |
| `demo_operations.csv` | 传感器监控 | 低方差、温度异常值、状态集中度 |

更多说明见 [examples/README.md](examples/README.md)。

## 快速开始

### 使用 Docker Compose

```bash
cp .env.example .env
docker compose up -d
```

API 文档地址：

```text
http://localhost:8000/docs
```

### 本地运行

本地运行需要 Python 3.11+ 和 PostgreSQL。应用会从 `.env` 读取配置。

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

如果使用本项目的 conda 开发环境：

```bash
conda activate ai
alembic upgrade head
uvicorn app.main:app --reload
```

### 前端启动

前端基于 React + TypeScript + Vite，默认运行在 `http://localhost:5173`，通过 Vite proxy 将 `/api` 请求转发到后端 `http://localhost:8000`。

```bash
cd frontend
npm install
npm run dev
```

生产构建：

```bash
cd frontend
npm run build
```

构建产物输出到 `frontend/dist/`，可直接用静态服务器托管。

### CLI Demo

```bash
python examples/run_investigation.py --demo sales
python examples/run_investigation.py --demo operations
python examples/run_investigation.py --demo churn
```

更多示例说明见 [examples/README.md](examples/README.md)。

## API 使用

上传单个数据集：

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@examples/demo_retail_revenue.csv" \
  -F "investigation_question=为什么收入下降"
```

上传主数据集 + 辅助数据集（跨数据集分析）：

```bash
curl -X POST "http://localhost:8000/upload/investigate/" \
  -F "primary_file=@examples/demo_retail_revenue.csv" \
  -F "secondary_files=@examples/demo_customer_complaints.csv" \
  -F "investigation_question=为什么收入下降"
```

获取任务结果：

```bash
curl "http://localhost:8000/task/{task_id}"
```

运行后续 drill-down 分析：

```bash
curl -X POST \
  "http://localhost:8000/task/{task_id}/follow-ups/{question_index}/drilldown"
```

drill-down 结果会追加到：

```text
result.interactive_investigation.drilldown_steps
```

跨数据集分析结果在：

```text
result.investigation_graph
```

## 项目结构

```text
app/
├── api/                 FastAPI 接口
├── core/                配置与日志
├── db/                  SQLAlchemy 数据库配置
├── models/              ORM 模型与枚举
├── prompts/             版本化 LLM prompt 契约
├── schemas/             Pydantic 数据契约
└── services/            调查分析业务逻辑
    ├── evidence/        证据构建器
    ├── profiler.py
    ├── signal_detector.py
    ├── question_generator.py
    ├── hypothesis_generator.py
    ├── hypothesis_validator.py
    ├── cause_ranker.py
    ├── drilldown.py
    ├── report_generator.py
    ├── narrative_generator.py
    └── pipeline.py

frontend/
├── src/api/             API client 与共享类型
├── src/components/      UI 组件
├── src/i18n/            中文与英文翻译
├── src/pages/           上传页与调查结果页
└── src/hooks/           轮询、主题、上传 hooks

docs/                    愿景、架构、决策、路线图
examples/                Demo 数据集与 CLI 示例
tests/                   后端测试套件
```

## 架构原则

- 证据先于结论：每个发现都必须能追溯到结构化证据。
- 可解释性：结论需要引用信号、方法、阈值、样本量和限制。
- 确定性分析先于 LLM 表达：LLM 解释发现，不生成发现。
- 优先扩展而非修改：新增 detector 或 builder 时优先采用 registry 风格。
- Schema 保持纯数据结构：业务逻辑放在 `app/services`。
- 调查质量优先于功能数量。

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python 3.11+, FastAPI, Pandas, Pydantic |
| 数据库 | PostgreSQL, SQLAlchemy, Alembic |
| LLM 集成 | Provider-agnostic protocol, mock fallback, OpenAI-compatible mode |
| 前端 | React, TypeScript, Vite, i18n |
| 测试 | pytest |
| 部署 | Docker Compose |

## 测试

```bash
python -m pytest tests/ -q
```

当前后端测试结果：

```text
210 passed
```

测试覆盖数据画像、信号检测、证据构建器、假设验证、报告生成、叙事 fallback、交互式调查、全部 6 类可运行 drill-down 分析，以及跨数据集分析。

## 文档

- [项目愿景](docs/vision.md)
- [系统架构](docs/architecture.md)
- [产品原则](docs/principles.md)
- [开发路线图](docs/roadmap.md)
- [架构决策](docs/decisions.md)
- [MVP 计划](docs/mvp-plan.md)

## License

MIT
