#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 2 端到端测试脚本"""
import urllib.request, urllib.error, json, sys, os, re, subprocess

BASE = "http://localhost:8000"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATE = os.path.join(SCRIPT_DIR, "validate.py")
TEMP = os.environ.get("TEMP", "C:/Windows/Temp")
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def api(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"__error": e.code, "__body": e.read().decode("utf-8", errors="replace")}


def sse_generate(sid, token):
    url = f"{BASE}/api/gen/sessions/{sid}/generate"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
        method="POST",
    )
    last = ("?", "")
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            buf = ""
            while True:
                chunk = r.read(256)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buf:
                    msg, buf = buf.split("\n\n", 1)
                    lines = msg.strip().splitlines()
                    ev = next((l[7:] for l in lines if l.startswith("event: ")), "")
                    da = next((l[6:] for l in lines if l.startswith("data: ")), "")
                    last = (ev, da)
                    if ev in ("done", "error"):
                        return last
    except Exception as e:
        return ("exception", str(e))
    return last


def validate_cht(cht_text, label):
    tmp = os.path.join(TEMP, f"gate2_{label}.cht")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(cht_text)
    r = subprocess.run(
        [sys.executable, VALIDATE, tmp],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = ANSI_RE.sub("", r.stdout)
    m = re.search(r"错误:\s*(\d+).*?警告:\s*(\d+)", out)
    ec = int(m.group(1)) if m else -1
    wc = int(m.group(2)) if m else -1
    errors = [l.strip() for l in out.splitlines() if "✗" in l or "✗" in l]
    return ec, wc, errors


def main():
    # Login
    resp = api("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
    if "__error" in resp:
        print(f"登录失败: {resp}")
        sys.exit(1)
    token = resp["access_token"]
    print("✓ 登录成功\n")

    scenarios = [
        (
            "A_relay",
            "会议室灯光控制：使用TS-9101继电器控制器（载体L:1）控制4路灯光开关，触摸屏T:10。"
            "灯光1开JN=1，灯光1关JN=2，灯光2开JN=3，灯光2关JN=4",
        ),
        (
            "B_serial",
            "会议室投影仪控制：爱普生EB系列投影仪通过RS232串口，载体TR-0740S编号L:1，"
            "触摸屏T:10，功能：开机JN=1、关机JN=2、静音JN=3",
        ),
        (
            "C_ir_dual",
            "会议室空调控制：两台格力空调红外控制，载体TR-0740S分别L:2和L:3均为IR，"
            "触摸屏T:10，温度16-30度可调，制冷制热通风自动模式",
        ),
    ]

    results = []

    for label, desc in scenarios:
        print(f"{'='*52}")
        print(f"场景 {label}")
        print(f"{'='*52}")

        # 1. 创建
        s = api("POST", "/api/gen/sessions", {"description": desc}, token)
        if "__error" in s:
            print(f"  创建失败: {s}")
            results.append({"label": label, "ok": False, "ec": -1, "errors": [str(s)]})
            continue
        sid = s["id"]
        print(f"  [1/4] session={sid[:8]}")

        # 2. 解析
        parse_resp = api("POST", f"/api/gen/sessions/{sid}/parse", None, token)
        if "__error" in parse_resp:
            print(f"  解析失败: {parse_resp}")
            results.append({"label": label, "ok": False, "ec": -1, "errors": [str(parse_resp)]})
            continue
        # 从 session GET 读取解析结果（最可靠，直接读 DB 存储的 parsed_data）
        s_after = api("GET", f"/api/gen/sessions/{sid}", token=token)
        raw_pd = s_after.get("parsed_data") or "{}"
        pd = json.loads(raw_pd) if isinstance(raw_pd, str) else (raw_pd or {})
        devs = pd.get("devices", [])
        missing = pd.get("missing_info", [])
        print(f"  [2/4] 解析完成: 设备={len(devs)} 语义告警={len(missing)}")
        for m in missing[:4]:
            print(f"         ⚠ {str(m)[:80]}")

        # 3. 确认
        confirmed = api("POST", f"/api/gen/sessions/{sid}/confirm", {"data": pd}, token)
        print(f"  [3/4] 确认: {confirmed.get('status','?')}")

        # 4. 生成
        print(f"  [4/4] 生成中...", end="", flush=True)
        last_ev = sse_generate(sid, token)
        ok = last_ev[0] == "done"
        print(" 完成" if ok else f" 失败({last_ev[1][:80]})")

        # 取结果
        session = api("GET", f"/api/gen/sessions/{sid}", token=token)
        cht = session.get("cht_content") or ""
        vr = session.get("validation_report") or "{}"
        if isinstance(vr, str):
            try:
                vr = json.loads(vr)
            except Exception:
                vr = {}
        sm = vr.get("summary", vr)
        print(f"       内置校验: Critical={sm.get('critical','?')} Warning={sm.get('warning','?')}")

        ec, wc, errs = (-1, -1, ["无CHT内容"]) if not cht else validate_cht(cht, label)
        print(f"       validate.py: 错误={ec} 警告={wc}")
        for e in errs:
            print(f"         {e}")

        results.append({"label": label, "ok": ok, "ec": ec, "wc": wc, "errors": errs})
        print()

    # 汇总
    print(f"\n{'='*52}")
    print("Gate 2 汇总")
    print(f"{'='*52}")
    gate_pass = True
    for r in results:
        p = r["ok"] and r["ec"] == 0
        icon = "✅" if p else "❌"
        print(f"  {icon} {r['label']}: 流程={'OK' if r['ok'] else 'FAIL'} | "
              f"validate.py 错误={r['ec']}")
        for e in r.get("errors", []):
            print(f"       ✗ {e}")
        if not p:
            gate_pass = False

    print()
    print("Gate 2 结论:", "✅ 通过" if gate_pass else "❌ 未通过，需修复上述错误")
    sys.exit(0 if gate_pass else 1)


if __name__ == "__main__":
    main()
