# 分析体验与准确性改进计划

> **Status**: Completed. All 10 items below have been implemented.
> This document is retained as a historical record of the implementation.

## Summary

本计划用于改进当前调查分析流程的三个问题：分析结论对普通用户不够友好、部分问题分析不够准确到位、前端等待和分析过程展示不清晰。

实施方向是保留现有调查流水线，不把系统改成 AutoEDA、BI 仪表盘或纯 LLM 报告工具。确定性分析仍由 `app/services` 完成，LLM 只负责把已经生成的结构化调查报告改写成更容易理解的叙事，不生成或修改结论。

目标结果：

- 等待页能展示当前调查阶段、阶段目的、输入、输出和为什么需要这一步。
- 报告页优先展示“发生了什么、为什么重要、下一步查什么、证据强弱和不确定性”。
- 指标值不再直接暴露内部字段名和原始小数，而是以业务可读方式展示。
- 趋势、证据、验证和报告生成更保守、更可追溯，减少弱信号被过度解释。
- 所有新增字段保持向后兼容，避免破坏现有 API 和前端页面。

## Current State Analysis

项目文档和代码表明，当前系统已经有清晰的调查流水线：

```text
Dataset
→ Profile
→ Signal Detection
→ Question Generation
→ Evidence Generation
→ Hypothesis Validation
→ Investigation Report
→ LLM Narrative
→ Interactive Investigation
```

`README.md` 和 `docs/architecture.md` 中的设计重点是调查而非报表。核心输出包括 Signal Report、Investigation Questions、Hypotheses、Evidence、Investigation Report、AI Narrative 和 Interactive Investigation。`docs/decisions.md` 明确要求证据先于结论、流水线分层、未来 LLM 应消费结构化证据而不是原始信号。

当前后端已经具备一些改进基础：

- `app/models/task.py`、`app/schemas/task.py` 已有 `current_stage` 和 `progress`。
- `app/services/pipeline.py` 已按阶段更新真实进度。
- `app/services/thresholds.py` 和 `app/services/statistics.py` 已开始集中统计口径。
- `app/schemas/signal.py`、`app/services/signal_detector.py` 已开始传递信号上下文和统计值。
- `app/schemas/investigation_report.py` 中 `Finding` 已有 `key_metrics` 和 `trace`。
- `app/schemas/ai_report.py` 中 `Narrative` 已有 `plain_language_summary`、`what_happened`、`why_it_matters`、`what_to_check_next`、`confidence_notes`。
- `frontend/src/lib/metrics.ts` 已提供指标格式化能力。
- `frontend/src/hooks/useTaskPolling.ts` 已优先使用后端真实进度。
- `frontend/src/pages/InvestigationPage.tsx` 已开始接入进度、i18n 和指标格式化。

当前主要缺口：

- 前端等待页仍主要是阶段列表和进度条，用户看不到每一步的目的、输入、输出和意义。
- `ProcessingView` 的阶段列表没有完整覆盖 `secondary_profiling`、`cross_dataset`、`completed`，多数据集任务可能出现阶段索引不匹配。
- `NarrativeTab` 尚未充分展示已有的普通用户友好字段。
- `EvidenceBlock` 仍可能直接展示原始 `metric` 和 `value`，例如 `growth_rate: -0.215`。
- `FindingCard` 尚未充分展示 `affected_columns`、`key_metrics`、`trace` 等可解释字段。
- 页面中仍存在硬编码英文文案，中文体验不一致。
- 趋势检测和验证需要更保守，避免只因 slope 非零或微小波动就生成强结论。
- 数据质量检查结果目前更多停留在日志或中间产物，尚未成为最终报告中的用户可见置信度背景。
- LLM narrative 如果失败，不应导致确定性调查结果不可用。

## Proposed Changes

### 1. 完成前端已有友好字段展示

Files:

- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/i18n/translations.ts`
- `frontend/src/i18n/zh.ts`
- `frontend/src/i18n/en.ts`

What:

- 在 `NarrativeTab` 顶部优先展示 `plain_language_summary`。
- 新增用户友好分区：
  - `what_happened`：发生了什么。
  - `why_it_matters`：为什么重要。
  - `what_to_check_next`：下一步查什么。
  - `confidence_notes`：置信度和限制说明。
- 空数组或空字符串不渲染对应 section。
- 将相关标题和说明全部接入 i18n。

Why:

- 这些字段后端 schema 已经存在，属于低风险、高用户价值改动。
- 普通用户应先看到业务语言，再进入技术证据。

How:

- 在 `NarrativeTab` 中先渲染 `plain_language_summary` 卡片。
- 抽出一个轻量 `NarrativeListSection` 或复用现有列表 section，避免重复 JSX。
- 中文文案放入 `zh.ts`，英文文案放入 `en.ts`，类型定义放入 `translations.ts`。

### 2. 修复指标展示和英文硬编码

Files:

- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/lib/metrics.ts`
- `frontend/src/i18n/translations.ts`
- `frontend/src/i18n/zh.ts`
- `frontend/src/i18n/en.ts`

What:

- `EvidenceBlock` 使用 `metricLabel()` 和 `formatMetricValue()` 展示指标。
- 对 `key_metrics` 也使用同一套格式化工具。
- 补齐常见 metric label，例如 `growth_rate`、`outlier_ratio`、`top_1_share`、`top_3_share`、`null_percentage`、`skewness`、`coefficient_of_variation`、`r_squared`。
- 清理页面中硬编码英文，包括但不限于 `Inconclusive`、`Overall confidence`、`Numeric`、`Categorical`、`All`、`Clear`、`Analysis`、`Business Impact`、`Supporting Evidence`、`Evidence Summary`、`Unresolved Areas`、`Affects`、`Cross-Dataset Analysis`。

Why:

- 用户不应直接面对内部字段名和未经格式化的小数。
- 中文界面混杂英文会降低理解和信任。

How:

- 保留未知 metric 的安全回退：未知字段使用原始 key，未知值使用 `String(value)`。
- 百分比字段按百分比显示，计数字段按整数显示，普通数值保留合理小数。
- 所有用户可见静态文本通过 `t.investigation` 读取。

### 3. 增强 Findings 可解释展示

Files:

- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/lib/metrics.ts`
- `frontend/src/i18n/translations.ts`
- `frontend/src/i18n/zh.ts`
- `frontend/src/i18n/en.ts`

What:

- 在 `FindingCard` 展开区展示：
  - `affected_columns`
  - `key_metrics`
  - `trace`
  - 支持证据和反驳证据中的方法、阈值、样本量、限制说明，前提是后端字段存在。
- 为 `trace` 同时支持 `string` 和 `string[]`。

Why:

- 用户需要理解结论从哪里来，而不仅是看到一个判断。
- 这符合 Explainability 和 Evidence Before Conclusions 原则。

How:

- 新增轻量展示组件，例如 `MetricGrid`、`TraceBlock`、`TagList`，可以先放在 `InvestigationPage.tsx` 内，后续再拆分。
- 没有数据时不显示空块。
- 保持现有筛选、展开和 tab 行为不变。

### 4. 扩展进度协议和等待页解释

Files:

- `app/schemas/task.py`
- `app/services/pipeline.py`
- `frontend/src/api/types.ts`
- `frontend/src/hooks/useTaskPolling.ts`
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/i18n/translations.ts`
- `frontend/src/i18n/zh.ts`
- `frontend/src/i18n/en.ts`

What:

- 向后兼容扩展 `TaskProgress`：
  - `stage_title`
  - `stage_goal`
  - `stage_input`
  - `stage_output`
  - `stage_reason`
- 在 `pipeline.py` 中新增阶段解释字典，覆盖主流程、多数据集扩展阶段和完成阶段。
- 前端等待页展示当前阶段说明、阶段输入、阶段输出和为什么需要这一步。
- 在 `useTaskPolling.ts` 中导出统一阶段列表，避免 hook 和 UI 各维护一份。

Why:

- 用户觉得等待漫长，核心原因不是只有耗时，而是无法感知系统正在做什么。
- 展示确定性流水线阶段可以提供透明度，但不会暴露或伪造 LLM 隐式推理链。

How:

- `pipeline.py` 的 `_update_progress` 或等价逻辑在写入 progress 时同时填充阶段解释字段。
- `ProcessingView` 使用后端解释字段；缺失时使用前端 i18n fallback。
- 阶段列表包含 `secondary_profiling`、`cross_dataset`、`completed`，并处理未知阶段 fallback。

### 5. 增强 Evidence 结构化字段

Files:

- `app/schemas/evidence.py`
- `app/services/evidence/trend.py`
- `app/services/evidence/distribution.py`
- `app/services/evidence/outlier.py`
- `app/services/evidence/concentration.py`
- `app/services/evidence/missing_rate.py`
- `app/services/evidence/cardinality.py`
- `app/services/evidence/variance.py`
- `frontend/src/api/types.ts`

What:

- 向后兼容扩展 `Evidence`：
  - `method`
  - `threshold`
  - `sample_size`
  - `direction`
  - `strength`
  - `limitation`
- 各 evidence builder 在关键证据中填充方法、阈值、样本量和限制说明。

Why:

- 当前 evidence 对普通用户仍偏抽象，只看到一个 metric/value 很难理解判断依据。
- 方法、阈值、样本量和限制说明能减少过度解读。

How:

- schema 字段全部设为可选，避免破坏旧输出。
- 阈值来自 `app/services/thresholds.py`，不在 builder 中硬编码。
- 前端类型同步新增字段，展示时按字段存在与否渲染。

### 6. 增加 Finding 证据强度和不确定性

Files:

- `app/schemas/investigation_report.py`
- `app/services/report_generator.py`
- `app/services/hypothesis_validator.py`
- `frontend/src/api/types.ts`
- `frontend/src/pages/InvestigationPage.tsx`

What:

- 向后兼容扩展 `Finding`：
  - `evidence_strength`
  - `uncertainty_notes`
- 在 `report_generator.py` 中根据 validated hypothesis 的状态、证据数量、证据方向和置信度填充证据强度。
- 对 inconclusive、样本不足、质量风险、仅相关非因果等情况生成不确定性说明。

Why:

- 当前报告容易被用户理解成“系统已经给出确定原因”。
- 证据强度和不确定性可以让结论更准确、更克制。

How:

- 使用确定性规则，不让 LLM 参与判断强弱。
- 规则放在 report generator 的私有 helper 中，保持 schema 纯数据。
- 前端在 Finding 展开区显示“证据强度”和“需要谨慎解读”。

### 7. 收紧趋势检测和验证

Files:

- `app/services/statistics.py`
- `app/services/thresholds.py`
- `app/services/signal_detector.py`
- `app/services/evidence/trend.py`
- `app/services/hypothesis_validator.py`
- `tests/test_signal_detector.py`
- `tests/test_evidence_builders.py`
- `tests/test_hypothesis_validator.py`

What:

- 在趋势统计中增加可靠性指标，例如 `r_squared` 和 `points`。
- 在 `thresholds.py` 中增加趋势可靠性阈值，例如最小增长幅度、最少数据点、最小拟合质量。
- 趋势信号检测不再因为 slope 非零就判定为有意义趋势。
- 假设验证不再让 `trend_slope > 0` 或 `< 0` 单独支持趋势结论，必须结合增长幅度和可靠性。

Why:

- 用户反馈“分析不够准确到位”时，弱趋势误报是高风险来源。
- 趋势应体现有意义变化，而不是任何微小波动。

How:

- `statistics.py` 计算趋势方向、绝对变化、增长率、点数和拟合质量。
- `signal_detector.py` 使用集中阈值判断是否生成趋势信号。
- `evidence/trend.py` 输出增长率、拟合质量、样本点数和限制说明。
- `hypothesis_validator.py` 使用同一阈值口径分类 supporting/contradicting/neutral evidence。

### 8. 将数据质量摘要接入报告

Files:

- `app/schemas/investigation_report.py`
- `app/services/pipeline.py`
- `app/services/report_generator.py`
- `app/services/quality.py`
- `app/schemas/quality.py`
- `frontend/src/api/types.ts`
- `frontend/src/pages/InvestigationPage.tsx`

What:

- 将已有 `assess_data_quality(df)` 的结果作为报告的一部分进入最终输出。
- 可以先在 `InvestigationReport` 中增加轻量 `quality_summary`，包含风险等级、问题数量、主要警告。
- 前端 Overview 显示数据质量提示，并在 Narrative 置信度说明中体现质量限制。

Why:

- 数据质量会直接影响结论可信度，用户需要看到这个背景。
- 这不改变流水线顺序，只是把已有质量检查结果变成用户可见证据。

How:

- 保持 quality schema 为纯数据结构。
- `pipeline.py` 调用质量检查后传入 `generate_report` 或在 report 生成后附加结构化质量摘要。
- 无明显质量问题时前端不制造噪音。

### 9. 增加 LLM narrative fallback

Files:

- `app/services/pipeline.py`
- `app/services/narrative_generator.py`
- `app/services/llm_narrative_generator.py`
- `app/prompts/investigation_narrative.py`
- `tests/test_pipeline_integration.py`
- `tests/test_llm_narrative_generator.py`

What:

- deterministic `InvestigationReport` 成功后，即使 LLM narrative 失败，任务仍应完成。
- 捕获 LLM JSON 解析失败、provider 异常等 presentation 层错误。
- fallback 到 `MockNarrativeGenerator`。
- metadata 或置信度说明中标记 narrative 使用了 fallback。
- 更新 prompt 合约，让 LLM 消费 `evidence_strength` 和 `uncertainty_notes`，但不能改变 supported/refuted/inconclusive。

Why:

- LLM 只是表达层，不应破坏确定性调查结果。
- 用户至少应获得结构化报告和 mock narrative。

How:

- 在 `pipeline.py` narrative 阶段添加 try/except。
- 日志记录原始异常。
- 保持最终 `AIInvestigationReport` schema 可序列化。

### 10. 适度拆分 InvestigationPage

Files:

- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/components/investigation/ProcessingView.tsx`
- `frontend/src/components/investigation/OverviewTab.tsx`
- `frontend/src/components/investigation/FindingsTab.tsx`
- `frontend/src/components/investigation/NarrativeTab.tsx`
- `frontend/src/components/investigation/InteractiveTab.tsx`
- `frontend/src/components/investigation/CrossDatasetTab.tsx`
- `frontend/src/components/investigation/shared.tsx`

What:

- 在前端 UI 改动变大后，将大型页面文件拆成多个调查组件。

Why:

- `InvestigationPage.tsx` 已经承担页面、进度、概览、发现、叙事、交互、多数据集和共享组件职责。
- 拆分是 UI 层维护性改进，不改变业务逻辑。

How:

- 先完成用户可见修复，再拆分。
- 拆分时保持 props 明确，避免把 API 请求逻辑下沉到子组件。
- 路由、tab query param、轮询 hook 行为保持不变。

## Assumptions & Decisions

- 使用 `conda` 环境 `ai` 执行 Python 依赖安装和测试。
- 不展示或伪造 LLM chain-of-thought。所谓“思考过程”只展示确定性调查流水线的阶段、输入、输出和解释。
- 不改变核心流水线顺序，不绕过 profile、signals、questions、evidence、validation。
- LLM 只解释 deterministic report，不生成或修改分析结论。
- schema 保持纯数据模型，业务逻辑继续放在 `app/services`。
- 新字段全部可选或有默认值，保持向后兼容。
- 前端优先消费后端真实进度；老任务或缺字段时使用前端 fallback。
- 准确性提升优先发生在 `statistics.py`、`thresholds.py`、`signal_detector.py`、`evidence/`、`hypothesis_validator.py`、`report_generator.py`。
- 用户友好提升优先发生在前端展示、i18n、metric formatting 和 narrative 字段呈现。
- 数据质量摘要进入报告是对现有质量检查结果的暴露，不是新增独立分析分支。
- 不把项目改成通用 dashboard 或 AutoEDA，所有展示都服务于调查问题。

## Verification Steps

后端验证使用 `conda ai` 环境：

```bash
conda run -n ai python -m pytest tests/test_signal_detector.py tests/test_evidence_builders.py tests/test_hypothesis_validator.py tests/test_report_generator.py tests/test_pipeline_integration.py -q
```

LLM 和 narrative 相关验证：

```bash
conda run -n ai python -m pytest tests/test_narrative_generator.py tests/test_llm_narrative_generator.py -q
```

交互式调查验证：

```bash
conda run -n ai python -m pytest tests/test_interactive_investigator.py -q
```

完整后端回归：

```bash
conda run -n ai python -m pytest tests/ -q
```

如果 `pytest` 缺失，应在 `conda ai` 环境中安装项目开发依赖，而不是在系统 Python 中安装：

```bash
conda run -n ai python -m pip install -r requirements-dev.txt
```

前端验证在 `frontend` 目录执行：

```bash
npm run build
npm run lint
```

重点验收：

- 上传后等待页能展示当前阶段、阶段目的、输入、输出和原因。
- 单数据集和多数据集阶段都能正确高亮，不出现未知阶段导致的 UI 错乱。
- Narrative 页优先展示普通语言摘要、发生了什么、为什么重要、下一步查什么和置信度说明。
- Findings 页能展示格式化指标、影响字段、关键指标、trace、证据强度和不确定性。
- 中文界面不再混杂明显硬编码英文。
- 弱趋势或噪声数据不会生成强 supported finding。
- 明显趋势、异常值、集中度、缺失率等原有核心能力仍能被检测。
- LLM narrative 失败时任务仍完成，并返回 deterministic investigation report 和 fallback narrative。
- 新增字段在 API JSON 中可序列化，前端 TypeScript build 通过。
