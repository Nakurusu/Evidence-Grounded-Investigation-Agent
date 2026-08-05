# MVP Completion Plan

## Product position

当前项目已经具备调查型分析引擎的主干：上传结构化数据后，系统可以完成数据画像、信号检测、问题生成、假设生成、证据生成、假设验证、结构化报告、LLM 叙事和后续调查建议。

MVP 的目标不是继续扩大功能数量，而是把这条链路打磨到一个用户可以信任、可以理解、可以围绕业务问题使用的状态。当前阶段应先完成单数据集调查体验，再继续推进多数据集分析和更复杂的交互式调查。

## MVP definition

MVP 应该支持两种使用方式：

- 探索驱动：用户上传数据集，系统告诉用户哪些风险、异常或机会值得关注。
- 问题驱动：用户上传数据集并输入一个业务问题，系统围绕这个问题组织信号、假设、证据和报告。

MVP 的核心输出应回答：

- 发生了什么。
- 哪些信号值得调查。
- 可能有哪些解释。
- 哪些证据支持或反驳这些解释。
- 当前结论有多可靠。
- 下一步应该查什么数据或问题。

## Current gap

当前系统已经比较接近“证据驱动调查报告”，但还没有完全达到“AI investigative partner”的预想形态。

主要差距：

- 用户问题已进入第一版 pipeline，但仍只影响报告上下文和 findings 排序；更深的语义理解仍待完善。
- 字段语义理解已加入 metric、dimension、time、entity、identifier 初版规则；后续仍可继续增强 rate 等派生角色。
- 报告已加入第一版候选原因排序，但后续仍可继续增强跨 finding 合并和更细的验证路径。
- 后续调查建议目前是静态文本，用户不能点击一个问题继续生成新的证据。
- 多数据集分析有早期雏形，但不应成为 MVP 前的主要投入。

## Development order

### 1. Add investigation question input

用户上传数据时可以输入一个可选业务问题，例如“为什么收入下降”或“哪些地区表现异常”。

后端需要保存该问题，并让主 pipeline 能读取它。前端需要在上传区提供输入框；如果用户不输入问题，系统继续按探索驱动模式运行。

最小改动范围：

- `frontend/src/components/upload/UploadZone.tsx`
- `frontend/src/api/upload.ts`
- `app/api/upload.py`
- `app/models/task.py`
- `app/schemas/task.py`
- `app/services/pipeline.py`

完成标准：

- 用户可以上传文件并附带调查问题。
- 任务结果中能看到原始调查问题。
- 不输入问题时，现有流程保持不变。

### 2. Use the question to rank signals and findings

问题进入系统后，第一版不需要做复杂自然语言推理。可以先用保守的方式影响排序和展示：

- 如果问题中出现某些字段名或字段别名，相关 signal 和 finding 优先展示。
- 如果问题包含“下降、增长、异常、缺失、集中、波动”等词，相关 signal type 优先展示。
- 不过滤掉其他发现，只改变优先级和报告呈现顺序。

最小改动范围：

- `app/services/question_context.py`
- `app/services/signal_detector.py`
- `app/services/hypothesis_generator.py`
- `app/services/report_generator.py`
- `frontend/src/pages/InvestigationPage.tsx`

完成标准：

- 问题相关 findings 排在前面。
- 报告中说明当前调查问题。
- 排序逻辑可追踪，不让 LLM 改变确定性结论。

### 3. Add semantic field roles

字段画像需要从基础类型扩展到分析角色。MVP 只需要支持第一批角色：

- metric：可分析的数值指标。
- dimension：可分组的类别字段。
- time：主要时间字段。
- entity：客户、产品、订单等实体标识。
- identifier：纯标识符，不直接作为分析维度。

这一步不需要一次性做到完美，先用规则和可覆盖配置完成可解释的初版。

最小改动范围：

- `app/schemas/profile.py`
- `app/services/profiler.py`
- `app/services/column_selection.py`
- `app/services/signal_detector.py`
- `app/services/evidence/*`
- `frontend/src/pages/InvestigationPage.tsx`

完成标准：

- Profile 中能看到每列的分析角色。
- 趋势分析使用 time 字段。
- 集中度分析优先使用 dimension × metric。
- identifier 不再被误当成普通分析维度。

### 4. Improve cause candidate ranking

当前系统可以生成假设，但还没有明确告诉用户“最可能的几个解释是什么”。MVP 应增加一个轻量的原因候选层，基于已验证的 findings 生成排序结果。

第一版可以采用确定性评分：

- 支持证据数量越多，分数越高。
- 高置信度 finding 分数更高。
- 与用户问题相关的 finding 分数更高。
- 有反驳证据或数据质量限制时降低分数。
- 多个信号共同指向同一解释时提高分数。

最小改动范围：

- `app/schemas/investigation_report.py`
- `app/services/cause_ranker.py`
- `app/services/report_generator.py`
- `frontend/src/api/types.ts`
- `frontend/src/pages/InvestigationPage.tsx`

完成标准：

- 报告中出现 3 到 5 个原因候选。
- 每个候选包含支持证据、限制说明和下一步验证建议。
- 不把候选原因表述为确定因果。

### 5. Make follow-up questions runnable in a limited way

交互式调查的 MVP 不需要完整对话系统，但至少要让一部分 follow-up question 对应到可运行的 drill-down。

第一批可支持：

- 查看异常值记录摘要。
- 按主要维度拆解趋势。
- 比较头部类别与其他类别。
- 检查缺失值是否集中在某些维度。

最小改动范围：

- `app/schemas/interactive.py`
- `app/services/interactive_investigator.py`
- `app/services/drilldown.py`
- `app/api/task.py`
- `frontend/src/pages/InvestigationPage.tsx`

完成标准：

- 至少 3 类 follow-up question 可以触发后续分析。
- 后续分析返回新的 evidence 或 summary。
- 原始报告不被覆盖，而是追加一个 investigation step。

### 6. Polish MVP frontend flow

前端应围绕“问题、发现、证据、原因候选、下一步调查”组织，而不是只展示后端对象结构。

建议的页面结构：

- 上传页：文件 + 可选调查问题。
- 等待页：当前阶段、阶段目的、输入、输出。
- 总览页：调查问题、核心发现、原因候选、整体置信度。
- 发现页：每个 finding 的证据、方法、阈值、限制。
- 后续调查页：可继续追问的问题和数据缺口。

最小改动范围：

- `frontend/src/pages/HomePage.tsx`
- `frontend/src/components/upload/UploadZone.tsx`
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/i18n/*`

完成标准：

- 用户不需要理解内部 pipeline，也能看懂系统结论。
- 技术证据仍然可以展开查看。
- 移动端和桌面端都能完成主要流程。

## MVP non-goals

以下内容应暂缓，避免 MVP 失焦：

- 完整多数据集根因图谱。
- 自由对话式分析代理。
- 自动生成复杂图表仪表盘。
- 让 LLM 直接生成或修改统计结论。
- 大规模性能优化。
- 多租户、权限、审计等生产级平台能力。

## Suggested milestone split

### Milestone 1: question-aware investigation

包含调查问题输入、任务保存、报告展示和基础排序。完成后，系统从纯探索驱动变成探索驱动与问题驱动并存。

**Status**: Completed in MVP track.

### Milestone 2: semantic profiling

加入字段角色识别，让系统更可靠地区分指标、维度、时间和实体。完成后，趋势、集中度和分组分析的误判会减少。

**Status**: Completed in MVP track.

### Milestone 3: cause candidates

在报告中增加原因候选排序，让用户看到最值得优先验证的解释。完成后，系统开始接近“缩小原因范围”的产品价值。

**Status**: Completed in MVP track.

### Milestone 4: runnable follow-ups

让部分后续问题可以继续生成新的分析结果。完成后，系统从一次性报告开始走向交互式调查。

## MVP completion signal

当用户能完成下面这条路径时，可以认为 MVP 成立：

1. 上传一个业务数据集。
2. 输入一个问题，例如“为什么收入下降”。
3. 等待页解释系统正在做什么。
4. 总览页给出与问题相关的核心发现。
5. 报告列出 3 到 5 个原因候选，并说明证据和限制。
6. 用户可以选择至少一个后续问题继续分析。
7. 系统不会把相关性说成确定因果。

达到这个状态后，再继续推进 Phase 9 多数据集分析和更完整的交互式调查，会更符合项目愿景。
