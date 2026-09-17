#!/usr/bin/env python3
"""
FoDi AI — Bug Hunt Explorer (Blue Whale Edition)
Mission: Crash-safe static analysis lab for postMessage audit.
Scope: LOCAL files only — scans downloaded source / HTML for missing origin checks.
Does NOT exploit, does NOT send messages.
Rule: Scan only code you own or have permission per bounty program.
Checkpoint: Alpha — fodi_boat_room.py style crash-proof.
"""

import os, re, json, sys
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("radio/bug_hunt_state.json")
REPORT_FILE = Path("radio/bug_hunt_report.json")
REPORT_HTML = Path("radio/bug_hunt_report.html")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)

def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"scanned": [], "findings": []}

LISTENER_PATTERNS = [
    r"addEventListener\s*\(\s*['\"]message['\"]\s*,",
    r"\.onmessage\s*=",
]

ORIGIN_CHECK_PATTERNS = [
    r"event\.origin", r"e\.origin", r"\.origin\s*!==?",
    r"origin\s*===?\s*['\"]https://", r"allowed.*origin"
]

DANGEROUS_SINKS = [
    r"innerHTML\s*=\s*.*event\.data",
    r"eval\s*\(\s*event\.data",
    r"location\s*=\s*event\.data",
]

def has_origin_check(block):
    return any(re.search(p, block, re.I) for p in ORIGIN_CHECK_PATTERNS)

def scan_file(filepath: Path):
    findings = []
    try: text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e: return []

    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if re.search(LISTENER_PATTERNS[0], line, re.I) or re.search(LISTENER_PATTERNS[1], line, re.I):
            block = "\n".join(lines[idx:idx+50])
            if not has_origin_check(block):
                findings.append({
                    "file": str(filepath),
                    "line": idx+1,
                    "listener": line.strip()[:200],
                    "severity": "medium",
                    "snippet": block[:800],
                    "recommendation": "Add strict allowlist: if (event.origin!== 'https://trusted.com') return; before using event.data"
                })
    return findings

def scan_directory(root_dir: Path):
    state = load_state()
    scanned = set(state.get("scanned", []))
    all_findings = state.get("findings", [])

    files = [p for p in root_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".js",".html",".jsx",".ts"}]
    print(f"[FoDi Lab] Found {len(files)} files, {len(scanned)} already scanned (crash-safe resume)")

    for f in files:
        if str(f) in scanned or "node_modules" in str(f) or ".git" in str(f):
            continue
        print(f"Scanning {f}")
        all_findings.extend(scan_file(f))
        scanned.add(str(f))
        save_state({"scanned": list(scanned), "findings": all_findings, "last_file": str(f), "timestamp": datetime.now().isoformat()})

    report = {
        "scan_root": str(root_dir),
        "scanned_at": datetime.now().isoformat(),
        "total_files": len(scanned),
        "total_findings": len(all_findings),
        "findings": all_findings
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2))
    print(f"\nDONE. Report -> {REPORT_FILE} | Findings: {len(all_findings)}")
    return report

if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
    scan_directory(target)
