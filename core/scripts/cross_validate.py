#!/usr/bin/env python3
"""
cross_validate.py — MKControl XML ↔ .cht 交叉校验器
用法：python3 cross_validate.py Project.xml output.cht
"""

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_xml_joins(xml_path):
    """从 Project.xml 提取所有非零 JoinNumber 及其控件信息"""
    joins = {}  # {join_num: {type, name, page}}
    pages = set()

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[ERROR] XML 解析失败: {e}")
        sys.exit(1)

    # 提取所有页面名称
    for obj in root.findall('Object'):
        obj_name = obj.get('Name', '')
        obj_type = obj.get('Type', '')
        if obj_type in ('DFCForm', 'DFCMessegeToast'):
            pages.add(obj_name)

        # 提取控件 JoinNumber
        for ctrl in obj.findall('Control'):
            event = ctrl.find('Event')
            if event is None:
                continue
            join_str = event.get('JoinNumber', '0')
            try:
                join = int(join_str)
            except ValueError:
                join = 0
            if join == 0:
                continue

            ctrl_name = ctrl.get('Name', '')
            ctrl_type = ctrl.get('Type', '')
            page_name = obj.get('Name', '')

            if join not in joins:
                joins[join] = []
            joins[join].append({
                'ctrl_type': ctrl_type,
                'ctrl_name': ctrl_name,
                'page': page_name,
                'jump_page': event.get('JumpPage', ''),
                'dialog_page': event.get('DialogPage', ''),
                'autolock': event.get('Autolock', ''),
                'mutual_group': event.get('MutualLockGroup', ''),
            })

        # TextSendJoinNumber（可编辑文本框双通道）
        for ctrl in obj.findall('Control'):
            style = ctrl.find('Style')
            if style is None:
                continue
            tsj = style.get('TextSendJoinNumber', '0')
            try:
                tsj_num = int(tsj)
            except ValueError:
                tsj_num = 0
            if tsj_num == 0:
                continue
            if tsj_num not in joins:
                joins[tsj_num] = []
            joins[tsj_num].append({
                'ctrl_type': ctrl.get('Type', '') + '[TextSend]',
                'ctrl_name': ctrl.get('Name', ''),
                'page': obj.get('Name', ''),
                'jump_page': '',
                'dialog_page': '',
            })

    return joins, pages


def extract_cht_joins(cht_path):
    """从 .cht 提取所有事件相关的 JoinNumber"""
    button_events = set()     # BUTTON_EVENT(tp, N) 的 N
    level_events = set()      # LEVEL_EVENT(tp, N) 的 N
    set_button_joins = set()  # SET_BUTTON(tp, N, ...) 的 N
    send_text_joins = set()   # SEND_TEXT(tp, N, ...) 的 N
    set_level_joins = set()   # SET_LEVEL(tp, N, ...) 的 N
    send_picture_joins = set()# SEND_PICTURE(tp, N, ...) 的 N
    send_paging_refs = set()  # SEND_PAGING(tp, N, "页面名") 中的页面名

    defined_devices = set()   # DEFINE_DEVICE 中声明的设备名
    set_com_devices = set()   # SET_COM 初始化的设备

    try:
        content = Path(cht_path).read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = Path(cht_path).read_text(encoding='gbk')

    # 剥离单行注释（// 至行尾），避免匹配注释掉的事件
    content = re.sub(r'//[^\n]*', '', content)

    # 提取 BUTTON_EVENT
    for m in re.finditer(r'BUTTON_EVENT\s*\(\s*\w+\s*,\s*(\d+)\s*\)', content):
        button_events.add(int(m.group(1)))

    # 提取 LEVEL_EVENT
    for m in re.finditer(r'LEVEL_EVENT\s*\(\s*\w+\s*,\s*(\d+)\s*\)', content):
        level_events.add(int(m.group(1)))

    # 提取 SET_BUTTON
    for m in re.finditer(r'SET_BUTTON\s*\(\s*\w+\s*,\s*(\d+)\s*,', content):
        set_button_joins.add(int(m.group(1)))

    # 提取 SEND_TEXT
    for m in re.finditer(r'SEND_TEXT\s*\(\s*\w+\s*,\s*(\d+)\s*,', content):
        send_text_joins.add(int(m.group(1)))

    # 提取 SET_LEVEL
    for m in re.finditer(r'SET_LEVEL\s*\(\s*\w+\s*,\s*(\d+)\s*,', content):
        set_level_joins.add(int(m.group(1)))

    # 提取 SEND_PICTURE
    for m in re.finditer(r'SEND_PICTURE\s*\(\s*\w+\s*,\s*(\d+)\s*,', content):
        send_picture_joins.add(int(m.group(1)))

    # 提取 SEND_PAGING 中的页面名
    for m in re.finditer(r'SEND_PAGING\s*\(\s*\w+\s*,\s*\d+\s*,\s*"([^"]+)"', content):
        send_paging_refs.add(m.group(1))

    # 提取 DEFINE_DEVICE 中的设备声明
    device_block = re.search(r'DEFINE_DEVICE(.*?)(?=DEFINE_|$)', content, re.DOTALL)
    if device_block:
        for m in re.finditer(r'(\w+)\s*=\s*[LMTND]:\d+:\w+', device_block.group(1)):
            defined_devices.add(m.group(1))

    # 提取 SET_COM 调用的设备名
    for m in re.finditer(r'SET_COM\s*\(\s*(\w+)\s*,', content):
        set_com_devices.add(m.group(1))

    # 所有 .cht 中使用的 JoinNumber（合集）
    all_cht_joins = button_events | level_events | set_button_joins | send_text_joins | set_level_joins | send_picture_joins

    return {
        'button_events': button_events,
        'level_events': level_events,
        'set_button': set_button_joins,
        'send_text': send_text_joins,
        'set_level': set_level_joins,
        'send_picture': send_picture_joins,
        'send_paging_pages': send_paging_refs,
        'all_joins': all_cht_joins,
        'defined_devices': defined_devices,
        'set_com_devices': set_com_devices,
    }


def cross_validate(xml_path, cht_path):
    """执行交叉校验"""
    print(f"\n📋 MKControl 交叉校验")
    print(f"   XML:  {xml_path}")
    print(f"   CHT:  {cht_path}")
    print("=" * 60)

    xml_joins, xml_pages = extract_xml_joins(xml_path)
    cht_data = extract_cht_joins(cht_path)

    criticals = []
    warnings = []

    # === 校验1：XML 非零 JN 在 .cht 中有事件处理 ===
    for join, ctrls in xml_joins.items():
        ctrl_types = [c['ctrl_type'] for c in ctrls]

        has_handler = False
        # DFCButton → BUTTON_EVENT 或 SET_BUTTON
        if any('DFCButton' in t for t in ctrl_types):
            if join in cht_data['button_events'] or join in cht_data['set_button']:
                has_handler = True
        # DFCSlider → LEVEL_EVENT 或 SET_LEVEL
        if any('DFCSlider' in t for t in ctrl_types):
            if join in cht_data['level_events'] or join in cht_data['set_level']:
                has_handler = True
        # DFCTaskBar → SET_LEVEL
        if any('DFCTaskBar' in t for t in ctrl_types):
            if join in cht_data['set_level']:
                has_handler = True
        # DFCTextbox → SEND_TEXT
        if any('DFCTextbox' in t for t in ctrl_types):
            if join in cht_data['send_text']:
                has_handler = True
        # DFCPicture → SEND_PICTURE
        if any('DFCPicture' in t for t in ctrl_types):
            if join in cht_data['send_picture']:
                has_handler = True
        # 通用匹配（任何 .cht 中出现此 JN）
        if join in cht_data['all_joins']:
            has_handler = True

        if not has_handler:
            pages_str = ', '.join(set(c['page'] for c in ctrls))
            # 纯导航按钮（只有 JumpPage，无需 .cht 处理）→ Warning
            all_nav_only = all(
                c.get('jump_page', '') not in ('', '无') and
                c.get('dialog_page', '') == ''
                for c in ctrls
            )
            if all_nav_only:
                warnings.append(
                    f"JN={join}: XML 中有纯导航按钮（{', '.join(ctrl_types)} @ {pages_str}），"
                    f".cht 中无事件处理（纯页面跳转无需处理）"
                )
            else:
                criticals.append(
                    f"JN={join}: XML 中有控件（{', '.join(ctrl_types)} @ {pages_str}），"
                    f"但 .cht 中无对应事件处理"
                )

    # === 校验2：.cht 事件的 JN 在 XML 中有控件（降级为 Warning）===
    # 注意：CHT 事件可能由外部设备/虚拟通道触发，不一定有对应 XML 控件
    for join in cht_data['button_events']:
        if join not in xml_joins:
            warnings.append(
                f"JN={join}: .cht 中有 BUTTON_EVENT，但 XML 中无对应 DFCButton 控件（可能是虚拟通道）"
            )

    for join in cht_data['level_events']:
        if join not in xml_joins:
            warnings.append(
                f"JN={join}: .cht 中有 LEVEL_EVENT，但 XML 中无对应 DFCSlider 控件（可能是虚拟通道）"
            )

    # === 校验3：JoinNumber 唯一性（同号不同语义）===
    for join, ctrls in xml_joins.items():
        if len(ctrls) > 1:
            # 同号多个控件（可能是故意复用 SET_BUTTON 反馈，也可能是错误）
            ctrl_types = [c['ctrl_type'] for c in ctrls]
            unique_types = set(ctrl_types)
            if len(unique_types) > 1:
                warnings.append(
                    f"JN={join}: 被多种控件类型使用 {ctrl_types}，请确认是否为有意复用"
                )

    # === 校验4：JumpPage 目标存在 ===
    for join, ctrls in xml_joins.items():
        for ctrl in ctrls:
            jp = ctrl.get('jump_page', '')
            if jp and jp not in ('', '无') and jp not in xml_pages:
                warnings.append(
                    f"JN={join} 控件 [{ctrl['ctrl_name']}]：JumpPage=\"{jp}\" 目标页面不存在"
                )

    # SEND_PAGING 中的页面名
    for page_name in cht_data['send_paging_pages']:
        if page_name not in xml_pages:
            warnings.append(
                f".cht 中 SEND_PAGING 目标页面 \"{page_name}\" 在 XML 中不存在"
            )

    # === 输出结果 ===
    print(f"\n📊 统计")
    print(f"   XML JoinNumber 数量: {len(xml_joins)}")
    print(f"   CHT BUTTON_EVENT 数量: {len(cht_data['button_events'])}")
    print(f"   CHT LEVEL_EVENT 数量: {len(cht_data['level_events'])}")
    print(f"   XML 页面数量: {len(xml_pages)}")

    if criticals:
        print(f"\n🔴 Critical ({len(criticals)} 项) — 必须修复")
        for i, msg in enumerate(criticals, 1):
            print(f"  [{i}] {msg}")
    else:
        print(f"\n✅ Critical: 0 项")

    if warnings:
        print(f"\n🟡 Warning ({len(warnings)} 项) — 建议检查")
        for i, msg in enumerate(warnings, 1):
            print(f"  [{i}] {msg}")
    else:
        print(f"\n✅ Warning: 0 项")

    print("\n" + "=" * 60)
    if criticals:
        print(f"❌ 校验未通过：{len(criticals)} 个 Critical 问题需修复")
        return False
    else:
        print("✅ 校验通过")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python3 cross_validate.py Project.xml output.cht")
        sys.exit(1)

    xml_file = sys.argv[1]
    cht_file = sys.argv[2]

    if not Path(xml_file).exists():
        print(f"[ERROR] XML 文件不存在: {xml_file}")
        sys.exit(1)
    if not Path(cht_file).exists():
        print(f"[ERROR] CHT 文件不存在: {cht_file}")
        sys.exit(1)

    ok = cross_validate(xml_file, cht_file)
    sys.exit(0 if ok else 1)
