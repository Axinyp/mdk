#!/usr/bin/env bash
# MDK (MKControl Development Kit) — Claude Code 安装脚本
# 用法: bash install.sh [--uninstall]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MDK_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CORE_DIR="$MDK_ROOT/core"
COMMANDS_DIR="$MDK_ROOT/commands"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
CLAUDE_COMMANDS_DIR="$HOME/.claude/commands"
TARGET_SKILLS="$CLAUDE_SKILLS_DIR/mdk"
TARGET_COMMANDS="$CLAUDE_COMMANDS_DIR/mk"

echo "=============================="
echo " MKControl Development Kit"
echo " MDK 安装程序"
echo "=============================="

# 卸载模式
if [[ "$1" == "--uninstall" ]]; then
    echo ""
    echo "正在卸载 MDK..."
    if [[ -L "$TARGET_SKILLS" ]]; then
        rm "$TARGET_SKILLS"
        echo "✅ 已删除符号链接: $TARGET_SKILLS"
    elif [[ -d "$TARGET_SKILLS" ]]; then
        rm -rf "$TARGET_SKILLS"
        echo "✅ 已删除目录: $TARGET_SKILLS"
    fi
    if [[ -d "$TARGET_COMMANDS" ]]; then
        rm -rf "$TARGET_COMMANDS"
        echo "✅ 已删除命令目录: $TARGET_COMMANDS"
    fi
    # 移除 MCP Server 注册
    CLAUDE_JSON="$HOME/.claude/claude.json"
    if [[ -f "$CLAUDE_JSON" ]]; then
        python3 - "$CLAUDE_JSON" <<'PYEOF'
import sys, json
config_path = sys.argv[1]
with open(config_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg.get('mcpServers', {}).pop('mdk', None)
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
PYEOF
        echo "✅ 已从 claude.json 移除 MCP Server 注册"
    fi
    echo "MDK 卸载完成。"
    exit 0
fi

# 检查 Claude 目录
if [[ ! -d "$CLAUDE_SKILLS_DIR" ]]; then
    echo "错误: Claude skills 目录不存在: $CLAUDE_SKILLS_DIR"
    echo "请先安装 Claude Code CLI。"
    exit 1
fi

if [[ ! -d "$CORE_DIR" ]]; then
    echo "错误: MDK core 目录不存在: $CORE_DIR"
    exit 1
fi

echo ""
echo "安装路径:"
echo "  core  → $TARGET_SKILLS"
echo "  commands → $TARGET_COMMANDS"
echo ""

# 安装 core/
if [[ -e "$TARGET_SKILLS" ]]; then
    echo "⚠️  已存在安装，将覆盖 core/..."
    [[ -L "$TARGET_SKILLS" ]] && rm "$TARGET_SKILLS" || rm -rf "$TARGET_SKILLS"
fi

if ln -s "$CORE_DIR" "$TARGET_SKILLS" 2>/dev/null; then
    echo "✅ core 符号链接创建成功"
    echo "   $TARGET_SKILLS → $CORE_DIR"
else
    echo "符号链接创建失败，改用复制..."
    cp -r "$CORE_DIR" "$TARGET_SKILLS"
    echo "✅ core 文件复制成功"
fi

# 安装 commands/（替换路径为当前用户的实际安装路径）
mkdir -p "$TARGET_COMMANDS"
SKILLS_PATH="$HOME/.claude/skills/mdk"

for src_file in "$COMMANDS_DIR"/*.md; do
    filename="$(basename "$src_file")"
    # 将文件中的占位路径替换为当前用户的实际路径
    sed "s|~/.claude/skills/mdk|$SKILLS_PATH|g; s|C:/Users/[^/]*/\.claude/skills/mdk|$SKILLS_PATH|g" \
        "$src_file" > "$TARGET_COMMANDS/$filename"
done

echo "✅ commands 安装成功（12 个命令）"

# 注册 MCP Server 到 ~/.claude/claude.json
CLAUDE_JSON="$HOME/.claude/claude.json"
MCP_SERVER_PATH="$MDK_ROOT/adapters/mcp-server/server.py"

if [[ ! -f "$CLAUDE_JSON" ]]; then
    echo '{"mcpServers":{}}' > "$CLAUDE_JSON"
fi

# 注入 mdk MCP server 条目（用 Python 安全合并 JSON）
python3 - "$CLAUDE_JSON" "$MCP_SERVER_PATH" <<'PYEOF'
import sys, json
config_path, server_path = sys.argv[1], sys.argv[2]
with open(config_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg.setdefault('mcpServers', {})['mdk'] = {
    'command': 'python',
    'args': [server_path],
    'env': {}
}
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
PYEOF

echo "✅ MCP Server 已注册到 $CLAUDE_JSON"
echo "   重启 Claude Code 后可使用 MDK MCP tools"

echo ""
echo "=============================="
echo "✅ MDK 安装完成！"
echo ""
echo "可用命令（在 Claude Code 中输入）:"
echo "  /mk:control          — 生成 Project.xml + .cht"
echo "  /mk:protocol-list    — 查看协议库"
echo "  /mk:protocol-add     — 添加新协议"
echo "  /mk:protocol-show    — 查看协议详情"
echo "  /mk:protocol-update  — 修正协议"
echo "  /mk:protocol-delete  — 删除协议"
echo "  /mk:protocol-import  — 从 .cht 提取协议"
echo "  /mk:cht-devices      — CHT 设备类型查询"
echo "  /mk:cht-functions    — CHT 函数查询"
echo "  /mk:cht-patterns     — CHT 代码模式"
echo "  /mk:xml-controls     — XML 控件查询"
echo "  /mk:xml-structure    — XML 结构规范"
echo "=============================="
