# 知识库变更审查协议

每次修改 `core/references/`、`core/templates/`、`core/protocols/` 内任意文件前，必须回答以下三个问题。全部通过后方可合入。

---

## 三问核查清单

### Q1：这个知识点有没有对应的 CI 测试用例？

**操作**：在 `core/tests/ci/` 中找到或创建覆盖该知识点的 `.test.cht` 文件。

- 正向测试（`xxx.test.cht`）：修改前后均应零错误通过
- 反向测试（`neg-xxx.test.cht`）：首行 `# EXPECT: <关键词>`，用于验证 validate.py 能检测该规则

**没有测试 = 不允许修改**。先补测试，再改知识。

---

### Q2：这个修改是否与现有测试用例冲突？

**操作**：修改后立即运行：

```bash
python core/scripts/run_ci.py
```

- 全部通过 → 通过
- 有失败 → 查明原因：是知识改错了，还是测试需要同步更新

**注意**：若是正向测试变红，说明改出了新 bug；若是反向测试变红，说明 validate.py 检测规则被删除了。

---

### Q3：这个修改是否需要同步更新其他文件？

知识库各文件之间存在依赖链，改一处往往需要联动：

| 修改文件 | 必须同步检查 |
|---------|------------|
| `core/references/core/patterns/*.md` | `core/tests/ci/*.test.cht`（对应测试） |
| `core/templates/cht/devices.md` | `web/backend/app/prompts/parse_system.md`（设备声明规则） |
| `web/backend/app/prompts/parse_system.md` | `web/backend/app/prompts/cht_system.md`（生成规则） |
| `web/backend/app/prompts/cht_system.md` | `core/scripts/validate.py`（静态检查覆盖） |
| `core/scripts/validate.py`（新增规则）| `core/tests/ci/`（新增对应反向测试） |

---

## 变更登记（最近 10 条）

> 格式：日期 | 文件 | 变更摘要 | CI 结果

| 日期 | 文件 | 变更摘要 | CI |
|------|------|---------|-----|
| 2026-04-26 | `ir-ac.md` | 新增多 IR 设备同步控制章节，明确每台设备需完整 if-else 链 | ✅ 9/9 |
| 2026-04-26 | `devices.md` | 完整重写：明确 9 种合法类型、顺序后缀命名规则、DSP 非法 | ✅ 9/9 |
| 2026-04-26 | `cht_system.md` | DEFINE_COMBINE 单 TP 必须留空规则 | ✅ 9/9 |
| 2026-04-26 | `parse_system.md` | 增加规则 9-13：DSP限制、禁重复、TCP/UDP无需声明、命名规则 | ✅ 9/9 |
| 2026-04-26 | `validate.py` | 新增检查 11-13：GET_LEVEL、IRCODE拼接、COMBINE单TP | ✅ 9/9 |
| 2026-04-26 | `validate.py` | 修复 DEFINE_COMBINE 检查未覆盖 `[ tp ];` 括号格式，新增 neg-combine-bracket-single-tp 反向测试 | ✅ 10/10 |
| 2026-04-26 | `parse_system.md` | 新增规则 14：触摸屏（T:N）必须在 devices 中声明 TP 类型设备 | ✅ 10/10 |

---

## 快速检查命令

```bash
# 运行 CI 套件（在项目根目录执行）
python core/scripts/run_ci.py

# 单文件快速校验
python core/scripts/validate.py path/to/file.cht
```
