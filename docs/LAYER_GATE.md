# 层次升级门控协议

## 背景

本系统经历了四个层次的演进：

```
Stage 1: 单 Skill（prompt 内嵌知识）
  ↓
Stage 2: MDK Skills（分离知识库）
  ↓
Stage 3: Plugin（结构化生成 + 静态校验）
  ↓
Stage 4: Agent Web（完整 Web 应用 + LLM 流水线）
```

每次跨层时都携带了上一层未修复的问题，导致错误累积。本协议规定：**在现有层次稳定之前，不得引入新的复杂度**。

---

## 升级门控清单

在开始任何新功能/层次之前，当前层必须通过以下全部检查：

### Gate 1：CI 绿灯

```bash
python core/scripts/run_ci.py
# 要求: 全部通过，0 失败
```

新增任何规则知识点时，必须同时在 `core/tests/ci/` 中新增对应测试用例。

### Gate 2：端到端生成验证（≥3 次）

手动运行不少于 3 次完整生成流程，覆盖不同场景（继电器灯控、IR 空调、串口投影仪），确认：
- `validate.py` 输出：错误: 0
- 生成的 `.cht` 文件结构完整（无未替换占位符）
- 无 LLM 输出 schema 验证错误（Pydantic 不抛 ValidationError）

### Gate 3：知识库审查通过

对于本次开发修改的所有知识文件，在 `core/KNOWLEDGE_REVIEW.md` 的变更登记表中填写一条记录，格式：

```
| 日期 | 文件 | 变更摘要 | CI |
```

CI 列必须为 ✅（绿灯）。

### Gate 4：已知问题清零

不允许带着已知的 Critical 错误升级层次。当前已知问题状态：

| 问题 | 状态 | 修复版本 |
|------|------|---------|
| GET_LEVEL 不存在 | ✅ 已修复 | v4（Agent Web）|
| IRCODE<> 拼接报错 | ✅ 已修复 | v4（Agent Web）|
| DEFINE_COMBINE 单 TP 报错 | ✅ 已修复 | v4（Agent Web）|
| DSP 非法设备类型 | ✅ 已修复 | v4（Agent Web）|
| 设备命名用板卡号作后缀 | ✅ 已修复 | v4（Agent Web）|
| 校验器假阳性误报 | ✅ 已修复 | v4（Agent Web）|
| JSON 控制字符解析失败 | ✅ 已修复 | v4（Agent Web）|
| Pydantic null 字段校验失败 | ✅ 已修复 | v4（Agent Web）|

---

## 下一层（Stage 5）候选功能

以下功能处于评估阶段，**在 Stage 4 通过全部 Gate 之前不启动**：

- [ ] 多页面 XML 生成（多 page 结构）
- [ ] 协议库扩展（自动导入用户协议文件）
- [ ] 实时 WebSocket 推送取代 SSE
- [ ] 多用户协作（会话共享）

---

## 根本原因回顾（不要重蹈覆辙）

| 根因 | 表现 | 当前防护 |
|------|------|---------|
| **无编译器反馈回路** | 知识错误沉默传递，直到真实编译才暴露 | `run_ci.py` + `validate.py` 新增 3 项规则 |
| **知识质量滞后于系统复杂度** | 每次 ad-hoc 修复，没有测试固化 | 知识审查协议（KNOWLEDGE_REVIEW.md）|
| **用有 bug 的工具做正确性验证** | validate.py 有假阳性，401.cht 本身有问题 | CI 套件中有反向测试验证 validate.py 自身行为 |
