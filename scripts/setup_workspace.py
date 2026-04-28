#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/setup_workspace.py
v7.0 — 一键初始化工作目录（部署到服务器后第一步执行）

功能:
  1. 创建所有 v7.0 所需的目录结构
  2. 初始化仲裁权重配置文件
  3. 初始化 Episodic Memory SQLite 数据库
  4. 验证所有 v7.0 模块可正常导入
  5. 打印环境变量检查报告

运行: python3 scripts/setup_workspace.py
"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def banner(title: str, char: str = "="):
    print(f"\n{char * 60}")
    print(f"  {title}")
    print(f"{char * 60}")


def check(label: str, passed: bool, detail: str = ""):
    icon = "✅" if passed else "❌"
    suffix = f" ({detail})" if detail else ""
    print(f"  {icon} {label}{suffix}")
    return passed


def setup_directories():
    banner("Step 1: Creating v7.0 Directory Structure")
    dirs = [
        "workspace/evolution",
        "workspace/memory",
        "workspace/sandbox/memories",
        "workspace/sandbox/execution_logs",
        "workspace/analysis_output/patients",
        "evaluation/judge_prompts",
        "evaluation/results/R0",
        "evaluation/results/R1",
        "evaluation/results/R2",
        "evaluation/results/R3",
        "logs",
    ]
    all_ok = True
    for d in dirs:
        full_path = os.path.join(PROJECT_ROOT, d)
        os.makedirs(full_path, exist_ok=True)
        check(d, os.path.isdir(full_path))
    return all_ok


def setup_arbitration_weights():
    banner("Step 2: Initialize Arbitration Weights")
    try:
        from core.arbitration_weights import load_weights, WEIGHTS_FILE
        weights = load_weights()
        check(f"arbitration_weights.json ({weights['version']})", True, WEIGHTS_FILE)
        print(f"    EBM scores: {weights['ebm_level_scores']}")
        print(f"    Priority weights: {weights['clinical_priority_weights']}")
        return True
    except Exception as e:
        check("arbitration_weights.json", False, str(e))
        return False


def setup_episodic_memory():
    banner("Step 3: Initialize Episodic Memory (SQLite FTS5)")
    try:
        from core.episodic_memory import init_db, MEMORY_DB
        conn = init_db()
        # Verify tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        table_names = [t[0] for t in tables]
        has_cases = "cases" in table_names
        has_fts = "cases_fts" in table_names
        check("SQLite DB file created", os.path.exists(MEMORY_DB), MEMORY_DB)
        check("Table 'cases' exists", has_cases)
        check("Table 'cases_fts' (FTS5) exists", has_fts)
        return has_cases and has_fts
    except Exception as e:
        check("Episodic Memory DB", False, str(e))
        return False


def check_imports():
    banner("Step 4: v7.0 Module Import Verification")
    modules = [
        ("schemas.triage_schema", "TriageOutput"),
        ("schemas.conflict_schema", "AgreementMatrix"),
        ("schemas.conflict_schema", "STANDARD_KDP_IDS"),
        ("schemas.v6_expert_schemas", "CitedClaim"),
        ("core.safety_invariants", "run_safety_check"),
        ("core.arbitration_weights", "compute_selection_priority"),
        ("core.experience_library", "search_similar_cases"),
        ("core.episodic_memory", "init_db"),
        ("agents.triage_prompt", "TRIAGE_SYSTEM_PROMPT"),
        ("agents.orchestrator_prompt", "ORCHESTRATOR_SYSTEM_PROMPT"),
    ]
    errors = []
    for mod, attr in modules:
        try:
            m = __import__(mod, fromlist=[attr])
            getattr(m, attr)
            check(f"{mod}.{attr}", True)
        except Exception as e:
            check(f"{mod}.{attr}", False, str(e))
            errors.append(mod)
    return len(errors) == 0


def check_environment():
    banner("Step 5: Environment Variable Check")
    required = {
        "DASHSCOPE_API_KEY": "Qwen3.6-plus inference",
        "ONCOKB_API_KEY": "OncoKB molecular evidence",
        "PUBMED_EMAIL": "PubMed literature search",
    }
    optional = {
        "NCBI_API_KEY": "PubMed rate limit improvement",
        "JUDGE_API_KEY": "LLM-as-Judge evaluation (WS-3, optional for now)",
        "JUDGE_BASE_URL": "LLM-as-Judge base URL",
    }
    all_required_ok = True
    for key, desc in required.items():
        val = os.getenv(key)
        ok = bool(val)
        check(f"{key} [{desc}]", ok, "SET" if ok else "NOT SET ← REQUIRED")
        if not ok:
            all_required_ok = False

    print()
    for key, desc in optional.items():
        val = os.getenv(key)
        ok = bool(val)
        icon = "✅" if ok else "⚠️ "
        print(f"  {icon} {key} [{desc}]: {'SET' if ok else 'not set (optional)'}")

    return all_required_ok


def run_quick_sanity():
    banner("Step 6: Quick Sanity Check")
    ok = True

    # Safety invariants quick test
    try:
        from core.safety_invariants import run_safety_check
        result = run_safety_check(
            "Module 0 Module 1 Module 2 Module 3 Module 4 Module 5 Module 6 Module 7 Module 8 "
            "KPS 80 ECOG DS-GPA prognostic"
        )
        check(
            "Safety invariants: minimal report",
            result["total_violations"] == 0 or result["passed"],
            f"critical={len(result['critical_violations'])}"
        )
    except Exception as e:
        check("Safety invariants", False, str(e))
        ok = False

    # Arbitration weights quick test
    try:
        from core.arbitration_weights import compute_selection_priority
        pri = compute_selection_priority("Level 1", "Life-saving")
        check(
            f"Arbitration: Level1+Life-saving → {pri}",
            abs(pri - 500) < 1.0,
            "expected 500"
        )
    except Exception as e:
        check("Arbitration priority calc", False, str(e))
        ok = False

    # Conflict calculator tool exists and is runnable
    calc_path = os.path.join(PROJECT_ROOT, "tools", "conflict_calculator.py")
    check("tools/conflict_calculator.py exists", os.path.isfile(calc_path))

    validator_path = os.path.join(PROJECT_ROOT, "tools", "cross_agent_validator.py")
    check("tools/cross_agent_validator.py exists", os.path.isfile(validator_path))

    return ok


def print_summary(results: dict):
    banner("Setup Summary", "━")
    all_ok = all(results.values())
    for step, ok in results.items():
        check(step, ok)
    print()
    if all_ok:
        print("  🎉 All setup steps PASSED. Ready for testing.")
        print()
        print("  Next steps:")
        print("  1. Run Phase A unit tests (see docs/V7_Test_Plan_and_Config_Guide.md)")
        print("  2. Run Phase B smoke test")
        print("  3. Execute single case: python3 scripts/run_batch_eval.py --max_cases 1")
    else:
        print("  ⚠️  Some setup steps FAILED. Fix issues above before proceeding.")
        print("     Most common fix: set missing environment variables in .env or activate conda env")
    print()


def main():
    banner("TiantanBM v7.0 — Workspace Setup", "━")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Python: {sys.executable}")

    results = {
        "Directory structure": setup_directories(),
        "Arbitration weights": setup_arbitration_weights(),
        "Episodic Memory DB": setup_episodic_memory(),
        "Module imports": check_imports(),
        "Environment vars": check_environment(),
        "Sanity checks": run_quick_sanity(),
    }

    print_summary(results)
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
