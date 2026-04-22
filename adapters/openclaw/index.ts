/**
 * MDK (MKControl Development Kit) — OpenClaw 插件
 * 注册 15 个工具，引用 core/ 知识库提供中控开发辅助
 */

import { definePluginEntry, type PluginContext } from "@openclaw/sdk";
import * as path from "path";
import * as fs from "fs";

const MDK_CORE = path.resolve(__dirname, "../../core");
const PROTOCOLS_DIR = path.join(MDK_CORE, "protocols");
const REFERENCES_DIR = path.join(MDK_CORE, "references");
const DOCS_DIR = path.join(MDK_CORE, "docs");

function readFile(filePath: string): string {
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    try {
      return fs.readFileSync(filePath, "gbk" as BufferEncoding);
    } catch {
      return `[文件不存在: ${filePath}]`;
    }
  }
}

function findProtocolFile(name: string): string | null {
  const nameLower = name.toLowerCase().replace(/[\s_]/g, "-");
  const dirs = fs.readdirSync(PROTOCOLS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  for (const dir of dirs) {
    const dirPath = path.join(PROTOCOLS_DIR, dir);
    const files = fs.readdirSync(dirPath).filter((f) => f.endsWith(".md") && !f.startsWith("_"));
    for (const file of files) {
      if (file.toLowerCase().includes(nameLower) || nameLower.includes(file.replace(".md", "").toLowerCase())) {
        return path.join(dirPath, file);
      }
    }
  }
  return null;
}

export default definePluginEntry({
  name: "mdk-mkcontrol",
  version: "1.0.0",

  setup(ctx: PluginContext) {
    // 注册 Skill 文件
    ctx.registerSkill(path.join(MDK_CORE, "skills", "mkcontrol", "SKILL.md"));
    ctx.registerSkill(path.join(MDK_CORE, "skills", "protocol", "SKILL.md"));
    ctx.registerSkill(path.join(MDK_CORE, "skills", "cht-ref", "SKILL.md"));
    ctx.registerSkill(path.join(MDK_CORE, "skills", "xml-ref", "SKILL.md"));

    // 协议列表
    ctx.registerTool({
      name: "protocol_list",
      description: "列出协议库中的所有协议，支持按关键词过滤",
      parameters: {
        filter: { type: "string", description: "过滤关键词", default: "" },
      },
      handler: async ({ filter }) => {
        const indexPath = path.join(PROTOCOLS_DIR, "_index.md");
        let content = readFile(indexPath);
        if (filter) {
          const lines = content.split("\n").filter((l) => l.toLowerCase().includes(filter.toLowerCase()));
          content = lines.join("\n") || `未找到包含 '${filter}' 的协议`;
        }
        return { content };
      },
    });

    // 协议详情
    ctx.registerTool({
      name: "protocol_show",
      description: "查看某个协议的完整详情",
      parameters: {
        name: { type: "string", description: "协议名称或关键词" },
      },
      handler: async ({ name }) => {
        const filePath = findProtocolFile(name);
        if (filePath) {
          return { content: readFile(filePath) };
        }
        return { content: `未找到协议：${name}。请用 protocol_add 添加。` };
      },
    });

    // CHT 代码模式
    ctx.registerTool({
      name: "cht_patterns",
      description: "查询 .cht 常见代码模式",
      parameters: {
        pattern: { type: "string", description: "模式关键词", default: "" },
      },
      handler: async ({ pattern }) => {
        const filePath = path.join(REFERENCES_DIR, "core", "code-patterns.md");
        const content = readFile(filePath);
        if (!pattern) return { content };
        const sections = content.split(/(?=^## 模式)/m);
        const matched = sections.find((s) => s.toLowerCase().includes(pattern.toLowerCase()));
        return { content: matched || content.substring(0, 1000) };
      },
    });

    // XML 控件规范
    ctx.registerTool({
      name: "xml_controls",
      description: "查询 Project.xml 控件类型和属性规范",
      parameters: {
        control_type: { type: "string", description: "控件类型（如 DFCButton）", default: "" },
      },
      handler: async ({ control_type }) => {
        const filePath = path.join(REFERENCES_DIR, "controls", "controls-spec.md");
        const content = readFile(filePath);
        if (!control_type) return { content: content.substring(0, 2000) };
        const sections = content.split(/(?=^## \d+\.)/m);
        const matched = sections.find((s) => s.toUpperCase().includes(control_type.toUpperCase()));
        return { content: matched || `未找到控件：${control_type}` };
      },
    });

    // CHT 语法规则
    ctx.registerTool({
      name: "cht_syntax",
      description: "查询 .cht 语言语法约束规则",
      parameters: {},
      handler: async () => {
        const filePath = path.join(REFERENCES_DIR, "core", "syntax-rules.md");
        return { content: readFile(filePath) };
      },
    });
  },
});
