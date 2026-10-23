# Changelog

## 2026-10-23

### Changed

- Project renamed: **Investigative Data Analyst** → **Evidence-Grounded Investigation Agent**.
- Repository renamed to `Nakurusu/Evidence-Grounded-Investigation-Agent`. GitHub keeps a permanent redirect from the old URL, so existing links still resolve.
- Updated the name in `README.md`, `CLAUDE.md`, `docs/decisions.md`, `frontend/README.md`, the frontend `<title>` and i18n `appName` / `home.heading` strings, and the CLI example header.
- Frontend header short label `IDA` → `EGIA`; the mobile abbreviation now tracks the new name.

### Notes

- Prose keeps the adjective "investigative" where it describes behaviour rather than the product (`docs/vision.md`, `CLAUDE.md`): an *investigative* question, an *investigative* partner. Only the product name changed.
- The home-page subtitle punchline moved from "Not a dashboard. An analyst." to "Not a dashboard. An investigator." so it no longer positions the project as an analyst role.
- No code, pipeline, schema or test behaviour changed.

## 2026-08-05

### Fixed

- 优化 `profiler` 中字符串日期字段的类型推断逻辑。
- 将 `pd.to_datetime(..., errors="raise")` 调整为显式使用 `format="mixed"`，避免 pandas 在无法推断统一日期格式时输出 `UserWarning`。
- 保持原有字段识别行为不变：可解析日期字符串仍识别为 `datetime`，普通文本仍继续按唯一值比例识别为 `categorical` 或 `text`。

### Tests

- 为 datetime 字符串推断新增无 warning 回归测试。
- 已验证：
  - `python -m pytest tests/test_profiler.py -q` → `36 passed`
  - `python -m pytest tests/ -q` → `206 passed, 1 skipped`

### Notes

- 当前工作分支已经是 `main`，因此 profiler 修复已同步到主分支工作区。
- 本次变更不改变调查流水线顺序，也不改变 signal detection、evidence generation 或 drill-down 分析结果。
