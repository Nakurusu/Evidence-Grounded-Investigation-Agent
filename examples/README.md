# 示例数据集与运行方式

仓库提供三种运行方式，以及多组演示数据集。

---

## 1. CLI Demo（最快，无需服务器和数据库）

在终端运行完整 pipeline，输出格式化文本和 JSON 报告。

```bash
pip install -r requirements.txt

# 使用内置数据集：
python examples/run_investigation.py --demo sales       # 收入集中度 + 异常值
python examples/run_investigation.py --demo churn       # 缺失数据 + 消费下降
python examples/run_investigation.py --demo operations  # 低方差 + 传感器异常

# 使用自定义 CSV：
python examples/run_investigation.py path/to/data.csv
```

**环境要求**：Python 3.11，`pip install -r requirements.txt`。`LLM_MODE=mock` 时不需要 API key。

如需使用真实 LLM 生成叙事：

```bash
cp .env.example .env
# 编辑 .env：LLM_MODE=openai, LLM_API_KEY=你的key
python examples/run_investigation.py --demo sales
```

---

## 2. API 服务器（本地开发）

启动 FastAPI 服务器，支持文件上传和后台任务处理。

```bash
# 1. 启动 PostgreSQL（通过 Docker）：
docker compose up -d postgres

# 2. 配置环境：
cp .env.example .env
# 编辑 .env：设置 DATABASE_URL

# 3. 运行数据库迁移并启动：
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

打开 [http://localhost:8000/docs](http://localhost:8000/docs) 查看交互式 API 文档。

**接口列表**：

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/upload/` | 上传单个 CSV/Excel 文件，返回 `task_id` |
| `POST` | `/upload/investigate/` | 上传主数据集 + 辅助数据集，触发跨数据集分析 |
| `GET` | `/task/{task_id}` | 查询任务状态和结果 |
| `POST` | `/task/{task_id}/follow-ups/{question_index}/drilldown` | 运行后续 drill-down 分析 |

**环境要求**：Python 3.11，PostgreSQL。

---

## 3. Docker Compose（一条命令启动全部）

```bash
cp .env.example .env
# 编辑 .env：如使用真实 LLM，设置 LLM_MODE 和 LLM_API_KEY

docker compose up -d
```

启动后包含：
- **FastAPI** 运行在 `http://localhost:8000`
- **PostgreSQL** 运行在 `localhost:5432`

数据库迁移在启动时自动执行。上传文件和调查结果持久化在 Docker volumes 中。

**环境要求**：Docker。

---

## 4. 前端界面

前端基于 React + TypeScript + Vite。

```bash
cd frontend
npm install
npm run dev
```

默认运行在 `http://localhost:5173`，通过 Vite proxy 将 `/api` 请求转发到后端 `http://localhost:8000`。

---

## 演示数据集

### 展示用数据集（推荐）

| 文件 | 行数 | 场景 | 触发信号 |
|---|---|---|---|
| `demo_retail_revenue.csv` | 60 | 5 区域 × 12 个月零售收入 | revenue 下降趋势（-74%）、East 集中度（50.5%）、satisfaction_score 缺失 |
| `demo_customer_complaints.csv` | 60 | 5 区域 × 12 个月客户投诉 | complaint_count 上升（+487%）、avg_resolution_hours 上升 |

这两个数据集共享 `date` 和 `region` 维度，配合使用可展示完整的跨数据集分析流程：

- 单独上传主数据集 → 展示候选原因和 drill-down
- 添加辅助数据集 → 展示反向趋势和互补信号

### CLI Demo 数据集

| 文件 | 行数 | 场景 | 触发信号 |
|---|---|---|---|
| `demo_sales.csv` | 21 | 多区域销售 | 异常值（Premium 产品）、右偏、集中度、下降趋势 |
| `demo_churn.csv` | 22 | 订阅流失 | 缺失值（支持工单、最后活跃日期）、套餐集中度、消费下降 |
| `demo_operations.csv` | 20 | 传感器监控 | 低方差（压力）、温度异常值、状态集中度 |

---

## 数据集生成脚本

`demo_gen.py` 用于生成展示用数据集，可按需修改参数重新生成：

```bash
python examples/demo_gen.py
```

输出文件：
- `examples/demo_retail_revenue.csv`
- `examples/demo_customer_complaints.csv`
