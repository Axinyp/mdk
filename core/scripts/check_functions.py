#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MKControl 函数调用检查工具
用法: python check_functions.py <yourfile.cht>

检查 .cht 文件中所有函数调用是否：
1. 在 docs 中有定义
2. 参数个数正确（如果可以验证）

自动从 docs/系统函数库/*.md 提取函数列表
"""

import sys
import re
import os
import glob

# Windows: 启用 ANSI 颜色 + UTF-8 控制台输出
if sys.platform == "win32":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ANSI 颜色
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

# 函数数据库: {函数名: (参数个数, 文件来源)}
FUNCTION_DB = {}

def extract_functions_from_docs(docs_dir):
    """从 docs/系统函数库/*.md 提取所有函数"""
    md_files = glob.glob(os.path.join(docs_dir, "*.md"))
    
    for md_file in md_files:
        filename = os.path.basename(md_file)
        content = None
        for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
            try:
                with open(md_file, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if content is None:
            with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        
        # 匹配函数签名的模式
        # 格式1: void FUNC_NAME(type param, ...)
        # 格式2: void **FUNC_NAME**(type param, ...) - Markdown 粗体（函数名在 ** 中）
        # 格式3: String FUNC_NAME(...)
        
        patterns = [
            r'(?:void|int|string|char|byte|boolean|double|String)\s+\*+\s*([A-Z_][A-Z0-9_]*)\s*\*+\s*\(',  # void **FUNC**
            r'(?:void|int|string|char|byte|boolean|double|String)\s+\*?\*?\s*([A-Z_][A-Z0-9_]*)\s*\(',  # 标准格式
        ]
        
        # docs 中存在印刷错误：SOMPOSE_COM 实为 COMPOSE_COM
        content = content.replace('SOMPOSE_COM', 'COMPOSE_COM')

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)

                # 跳过非函数名
                if func_name in ['Function', 'String', 'Byte', 'Int']:
                    continue
                
                # 提取参数列表
                start = match.start()
                # 找到对应的括号
                paren_start = content.find('(', start)
                if paren_start == -1:
                    continue
                paren_end = paren_start
                depth = 0
                for i in range(paren_start, len(content)):
                    if content[i] == '(':
                        depth += 1
                    elif content[i] == ')':
                        depth -= 1
                        if depth == 0:
                            paren_end = i
                            break
                
                params_str = content[paren_start+1:paren_end].strip()
                
                # 计算参数个数
                if params_str:
                    param_count = len([p for p in params_str.split(',') if p.strip() and p.strip() != '...'])
                else:
                    param_count = 0
                
                # 如果已有记录，不覆盖
                if func_name not in FUNCTION_DB:
                    FUNCTION_DB[func_name] = (param_count, filename.replace('.md', ''))

def parse_function_calls(content):
    """解析代码中所有函数调用"""
    calls = []
    
    # 匹配函数调用: FUNC_NAME(...)
    # 排除变量名、类型定义等
    pattern = r'\b([A-Z_][A-Z0-9_]*)\s*\('
    
    for match in re.finditer(pattern, content):
        func_name = match.group(1)
        line_num = content[:match.start()].count('\n') + 1
        
        # 跳过常见非函数调用
        if func_name in ['DEFINE_DEVICE', 'DEFINE_COMBINE', 'DEFINE_CONSTANT', 
                        'DEFINE_VARIABLE', 'DEFINE_FUNCTION', 'DEFINE_TIMER',
                        'DEFINE_START', 'DEFINE_EVENT', 'DEFINE_PROGRAME',
                        'BUTTON_EVENT', 'DATA_EVENT', 'LEVEL_EVENT', 'STRING_EVENT',
                        'PUSH', 'RELEASE', 'HOLD', 'REPEAT', 'ONDATA', 'ONLINE', 
                        'OFFLINE', 'ONERROR', 'TIMER', 'WAIT', 'SWITCH', 'CASE',
                        'IF', 'ELSE', 'FOR', 'WHILE', 'DO', 'RETURN', 'BREAK', 'CONTINUE']:
            continue
        
        # 计算参数个数
        start = match.start()
        depth = 0
        paren_start = content.find('(', start)
        paren_end = paren_start
        for i in range(paren_start, len(content)):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    paren_end = i
                    break
        
        params_str = content[paren_start+1:paren_end].strip()
        if params_str:
            param_count = len([p for p in params_str.split(',') if p.strip()])
        else:
            param_count = 0
        
        calls.append({
            'name': func_name,
            'line': line_num,
            'params': param_count
        })
    
    return calls

def check_functions(filepath, docs_dir):
    if not os.path.exists(filepath):
        print(f"{RED}错误: 文件不存在: {filepath}{NC}")
        return False
    
    # 加载函数库
    extract_functions_from_docs(docs_dir)
    
    content = None
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if content is None:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

    # 解析函数调用
    calls = parse_function_calls(content)
    
    print(f"\n{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"{BLUE}  MKControl 函数调用检查工具{NC}")
    print(f"{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"\n校验文件: {GREEN}{filepath}{NC}")
    print(f"函数库: {GREEN}{len(FUNCTION_DB)} 个函数{NC}")
    print(f"检测到: {GREEN}{len(calls)} 次函数调用{NC}")
    print("")
    
    errors = []
    warnings = []
    valid_count = 0

    # 检查每个函数调用
    for call in calls:
        func_name = call['name']

        if func_name not in FUNCTION_DB:
            errors.append(f"行 {call['line']}: 未知函数 '{func_name}' (可能不存在于 docs)")
        else:
            expected_params, source = FUNCTION_DB[func_name]
            actual_params = call['params']

            # 参数个数检查：actual>0 时才比较（actual=0 可能是括号解析不完整）
            # expected>1 避免单参数函数的误报（docs 解析偶有偏差）
            if expected_params > 1 and actual_params > 0 and actual_params != expected_params:
                warnings.append(
                    f"行 {call['line']}: '{func_name}' 参数个数不符"
                    f"（docs 定义 {expected_params} 个，实际传入 {actual_params} 个）"
                )

            valid_count += 1

    # 输出结果
    print(f"{CYAN}[函数定义检查]{NC}")
    if errors:
        for e in errors:
            print(f"  {RED}✗ {e}{NC}")
    else:
        print(f"  {GREEN}✓ 所有函数调用均已定义{NC}")

    if warnings:
        print(f"\n{CYAN}[参数警告]{NC}")
        for w in warnings:
            print(f"  {YELLOW}⚠ {w}{NC}")

    print(f"\n{CYAN}[统计]{NC}")
    print(f"  有效调用: {valid_count}")
    print(f"  未知函数: {len(errors)}")
    print(f"  参数警告: {len(warnings)}")
    
    # 显示使用的函数来自哪些文件
    print(f"\n{CYAN}[使用到的系统函数库]{NC}")
    used_sources = set()
    for call in calls:
        if call['name'] in FUNCTION_DB:
            used_sources.add(FUNCTION_DB[call['name']][1])
    
    for src in sorted(used_sources):
        print(f"  ✓ {src}")
    
    print(f"\n{BLUE}═══════════════════════════════════════════════════{NC}")
    
    if errors:
        return False
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: python check_functions.py <yourfile.cht>")
        print(f"      python check_functions.py /path/to/file.cht")
        sys.exit(1)
    
    # 计算 docs 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(os.path.dirname(script_dir), "docs", "系统函数库")
    
    result = check_functions(sys.argv[1], docs_dir)
    sys.exit(0 if result else 1)