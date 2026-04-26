# TiantanBM Agent v7.0 — 测试规划书 & 配置说明

**版本**: v1.0  
**时间**: 2026-04-26  
**适用阶段**: 服务器部署后 → 单元测试 → 集成测试 → 进化迭代测试  

---

## 0. 前置：所有构件清单 & 配置状态

> [!IMPORTANT]
> 在执行任何测试之前，必须确认下表中所有构件均已就绪。

### 0.1 已完成构件（可直接使用）

| 构件 | 文件路径 | 状态 | 依赖 |
|:-----|:---------|:----:|:-----|
| **Triage Gate SA** | `agents/triage_prompt.py` + `schemas/triage_schema.py` | ✅ Ready | 无额外依赖 |
| **Conflict Calculator** | `tools/conflict_calculator.py` | ✅ Ready | 纯 stdlib，无需安装 |
| **Cross-Agent Validator** | `tools/cross_agent_validator.py` | ✅ Ready | 纯 stdlib，无需安装 |
| **Safety Invariants** | `core/safety_invariants.py` | ✅ Ready | 纯 re/stdlib |
| **Arbitration Weights** | `core/arbitration_weights.py` | ✅ Ready | 需要 `workspace/evolution/` 目录自动创建 |
| **Experience Library** | `core/experience_library.py` | ✅ Ready | 需要 `workspace/evolution/` 目录 |
| **Episodic Memory** | `core/episodic_memory.py` | ✅ Ready | SQLite（Python 内置） |
| **Orchestrator Prompt** | `agents/orchestrator_prompt.py` | ✅ Ready (v7.0) | — |
| **Expert Schemas** | `schemas/v6_expert_schemas.py` | ✅ Ready (v7.0) | Pydantic v2 |
| **Interactive Main** | `interactive_main.py` | ✅ Ready (v7.0) | 见下方 |

### 0.2 需要在服务器上确认/创建的构件

| 构件 | 状态 | 操作说明 |
|:-----|:----:|:---------|
| **`workspace/` 目录结构** | ⚠️ 需创建 | 运行 `python scripts/setup_workspace.py` |
| **`workspace/evolution/arbitration_weights.json`** | 🔄 自动创建 | 首次 `load_weights()` 时自动生成 |
| **`workspace/evolution/experience_library.jsonl`** | 🔄 首次为空 | R0 测试后开始填充 |
| **`workspace/memory/episodic.db`** | 🔄 自动创建 | 首次 `init_db()` 时自动创建 |
| **`evaluation/` 目录 (LLM-as-Judge)** | ❌ 待实现 | 见 WS-3 实施计划（本次测试不依赖） |
| **SA Prompts 置信度注解** | ⚠️ 未更新 | 5个专科 SA prompt 需追加 confidence 填写说明 |
| **`config_guidelines.py`** | ❌ 可选 | 指南版本锚定（不影响核心测试） |

### 0.3 检索策略与 Embedding Model 说明

> [!NOTE]
> **当前版本不需要 Embedding Model。** 这是有意为之的工程决策。

#### 当前检索策略（无向量检索）

**两层检索，均基于结构化元数据 + 关键词：**

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Experience Library (core/experience_library.py)       │
│  策略: 多维精确匹配打分                                           │
│  cancer_type 完全匹配: +4分                                       │
│  mutation 完全匹配:    +3分                                       │
│  treatment_line 匹配:  +2分                                       │
│  complexity 匹配:      +1分                                       │
│  取 Top-K (默认3)，按分数降序排列                                  │
│  → 适合: 相似病例的结构化经验检索                                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Episodic Memory SQLite FTS5 (core/episodic_memory.py) │
│  策略: BM25-like 全文检索 (SQLite FTS5 内置)                      │
│  索引字段: cancer_type, mutation, report_summary, errors,         │
│            expert_feedback                                        │
│  → 适合: 按错误类型/药名/突变关键词的非结构化检索                  │
└─────────────────────────────────────────────────────────────────┘
```

**何时引入 Embedding Model（v8.0 计划）：**
- 当 Experience Library > 500 Cases 时，结构化匹配精度仍够
- 当需要"语义相似而非精确匹配"时（如"EGFR外显子19缺失" ≈ "Del19"）
- 推荐方案: `text-embedding-v3` (通义), 维度1536, 存储在 `PGVector` 或 `ChromaDB`

---

## 1. 初始配置清单（部署到服务器后立即执行）

### Step 0: 创建工作目录
```bash
cd /path/to/TiantanBM_Agent

# 创建 v7.0 所需的新目录结构
mkdir -p workspace/{evolution,memory,sandbox/{patients,memories,execution_logs},analysis_output/patients}
mkdir -p evaluation/{judge_prompts,results}

# 验证目录创建成功
ls -la workspace/
```

### Step 1: 验证环境变量
```bash
# 必须设置的环境变量
echo "=== 检查必需的 API Keys ==="
[ -z "$DASHSCOPE_API_KEY" ] && echo "❌ DASHSCOPE_API_KEY 未设置" || echo "✅ DASHSCOPE_API_KEY OK"
[ -z "$ONCOKB_API_KEY" ]    && echo "❌ ONCOKB_API_KEY 未设置"    || echo "✅ ONCOKB_API_KEY OK"
[ -z "$PUBMED_EMAIL" ]       && echo "❌ PUBMED_EMAIL 未设置"      || echo "✅ PUBMED_EMAIL OK"

# 可选（不影响 v7.0 核心功能）
[ -z "$NCBI_API_KEY" ]      && echo "⚠️  NCBI_API_KEY 未设置（PubMed 速率限制较低）"
```

### Step 2: 验证 Python 依赖
```bash
conda activate tiantanBM_agent

python3 -c "
import pydantic; print(f'✅ pydantic {pydantic.VERSION}')
import deepagents; print(f'✅ deepagents {deepagents.__version__}')
import langgraph; print(f'✅ langgraph OK')
import langchain; print(f'✅ langchain OK')
import sqlite3; print(f'✅ sqlite3 (built-in) OK')
import json; print(f'✅ json (built-in) OK')
"
```

### Step 3: 初始化进化模块
```bash
# 初始化仲裁权重（会在 workspace/evolution/ 创建 arbitration_weights.json）
python3 -c "
from core.arbitration_weights import load_weights
w = load_weights()
print(f'✅ Arbitration weights initialized: {w[\"version\"]}')
print(f'   EBM scores: {w[\"ebm_level_scores\"]}')
print(f'   Priority weights: {w[\"clinical_priority_weights\"]}')
"

# 初始化 Episodic Memory DB
python3 -c "
from core.episodic_memory import init_db
conn = init_db()
conn.close()
print('✅ Episodic Memory SQLite DB initialized at workspace/memory/episodic.db')
"
```

### Step 4: v7.0 语法 + 模块导入验证
```bash
python3 -c "
# 验证所有 v7.0 新模块可导入
import sys; errors = []
modules = [
    ('schemas.triage_schema', 'TriageOutput'),
    ('schemas.conflict_schema', 'AgreementMatrix'),
    ('schemas.v6_expert_schemas', 'CitedClaim'),
    ('core.safety_invariants', 'run_safety_check'),
    ('core.arbitration_weights', 'load_weights'),
    ('core.experience_library', 'search_similar_cases'),
    ('core.episodic_memory', 'init_db'),
    ('agents.triage_prompt', 'TRIAGE_SYSTEM_PROMPT'),
]
for mod, attr in modules:
    try:
        m = __import__(mod, fromlist=[attr])
        getattr(m, attr)
        print(f'  ✅ {mod}.{attr}')
    except Exception as e:
        print(f'  ❌ {mod}: {e}')
        errors.append(mod)
if errors:
    print(f'FAIL: {len(errors)} import errors')
    sys.exit(1)
else:
    print(f'✅ All v7.0 modules import successfully')
"
```

---

## 2. 测试规划总览

```
Phase A: 单元测试 (2-3h)          ← 不启动 Agent，纯函数验证
Phase B: 集成冒烟测试 (1-2h)      ← 启动 Agent，用 mock 数据验证不崩溃
Phase C: 单 Case 端到端测试 (2-4h) ← 真实病例，验证完整流程输出质量
Phase D: 批量基线测评 R0 (1-2天)   ← 56 Cases，建立 Round 0 基线
Phase E: 进化迭代测试 R1→R3 (1-2周) ← 逐轮进化，记录指标变化
```

---

## 3. Phase A — 单元测试（Unit Tests）

### A1: Safety Invariants 单元测试
```bash
python3 -c "
from core.safety_invariants import run_safety_check

# 测试 1: 干净报告 → 应全部通过
clean_report = '''
Module 0: 患者 KPS 80分，ECOG 1，DS-GPA 2.5分
Module 1: EGFR L858R 突变，使用奥希替尼 (osimertinib) 80mg QD
  引用: [OncoKB Level 1] EGFR L858R
Module 2: 单发病灶 2.5cm，建议 SRS 18Gy/1f
  剂量双轨验证: ✅ 文本+视觉一致
  CNS 穿透率: 高 (osimertinib CSF penetrance ~2%)
Module 3: DS-GPA 2.5, prognostic 评估已完成
Module 4: MRI 随访 8 周 (2个月)
Module 5: 无冲突，Kendall\'s W=1.0
Module 6: 停药方案已记录
Module 7: 支持治疗已记录
Module 8: 患者教育已完成
'''
result = run_safety_check(clean_report)
print(f'Test 1 (clean): passed={result[\"passed\"]}, violations={result[\"total_violations\"]}')
assert result['passed'], f'FAIL: clean report should pass. Got: {result}'
assert result['total_violations'] == 0, f'FAIL: expected 0 violations, got {result[\"total_violations\"]}'
print('  ✅ Test 1 PASSED')

# 测试 2: SI-001 KRAS + cetuximab → 应触发 CRITICAL
kras_report = '''
Module 0 Module 1 Module 2 Module 3 Module 4 Module 5 Module 6 Module 7 Module 8
KRAS G12C 突变检测阳性 OncoKB Level R1
建议使用 cetuximab (西妥昔单抗) 方案治疗
KPS 80分 ECOG 1 DS-GPA prognostic
随访 2个月 MRI
'''
result = run_safety_check(kras_report)
print(f'Test 2 (SI-001): passed={result[\"passed\"]}, critical={len(result[\"critical_violations\"])}')
assert not result['passed'], 'FAIL: KRAS+cetuximab should be BLOCKED'
assert any(v['rule_id'] == 'SI-001' for v in result['critical_violations']), 'FAIL: SI-001 not triggered'
print('  ✅ Test 2 PASSED')

# 测试 3: SRS 剂量超上限 → 应触发 CRITICAL
srs_report = '''
Module 0 Module 1 Module 2 Module 3 Module 4 Module 5 Module 6 Module 7 Module 8
放疗方案: SRS 30Gy 单次分割 (单次)
KPS 80 ECOG DS-GPA prognostic osimertinib CNS penetrance
随访 6周
'''
result = run_safety_check(srs_report)
print(f'Test 3 (SI-002 SRS dose): passed={result[\"passed\"]}, critical={len(result[\"critical_violations\"])}')
assert not result['passed'], 'FAIL: SRS 30Gy should be BLOCKED (>24Gy ceiling)'
print('  ✅ Test 3 PASSED')

print()
print('✅ Safety Invariants Unit Tests: ALL PASSED')
"
```

### A2: Conflict Calculator 单元测试
```bash
# 创建测试投票文件
cat > /tmp/test_votes.json << 'EOF'
{
  "imaging-specialist": {
    "local_therapy_modality": "SRS",
    "surgery_indication": "No_Surgery",
    "treatment_urgency": "Semi_Elective_2weeks"
  },
  "primary-oncology-specialist": {
    "local_therapy_modality": "SRS",
    "systemic_therapy_class": "Targeted_TKI",
    "treatment_urgency": "Semi_Elective_2weeks"
  },
  "radiation-oncology-specialist": {
    "local_therapy_modality": "SRS",
    "treatment_urgency": "Semi_Elective_2weeks"
  }
}
EOF

python3 tools/conflict_calculator.py --votes-json /tmp/test_votes.json

# 预期输出: kendall_w_approx=1.0, total_conflicts=0 (全一致)

# 测试冲突场景
cat > /tmp/test_votes_conflict.json << 'EOF'
{
  "imaging-specialist": {
    "local_therapy_modality": "Surgery",
    "surgery_indication": "Emergency_Surgery",
    "treatment_urgency": "Emergency_24h"
  },
  "radiation-oncology-specialist": {
    "local_therapy_modality": "WBRT",
    "treatment_urgency": "Urgent_1week"
  },
  "neurosurgery-specialist": {
    "surgery_indication": "Emergency_Surgery",
    "treatment_urgency": "Emergency_24h"
  }
}
EOF

python3 tools/conflict_calculator.py --votes-json /tmp/test_votes_conflict.json
# 预期: total_conflicts >= 1 (local_therapy_modality 冲突: Surgery vs WBRT)
```

### A3: Experience Library 单元测试
```bash
python3 -c "
from core.experience_library import (
    make_experience_record, append_experience,
    search_similar_cases, get_library_stats
)

# 插入测试记录
record1 = make_experience_record(
    case_id='TEST-001',
    cancer_type='NSCLC_Adenocarcinoma',
    mutation='EGFR_L858R',
    treatment_line=1,
    complexity='simple',
    evolution_round='R0',
    final_local_therapy='SRS 18Gy/1f',
    final_systemic_therapy='Osimertinib 80mg QD',
    triage_subagents_used=['imaging-specialist', 'primary-oncology-specialist', 'radiation-oncology-specialist'],
    judge_scores={'esr_total': 35},
    auto_metrics={'EGR': 0.92, 'SCR': 0.89},
    key_insights=['EGFR L858R + 单发脑转移首选 SRS + 奥希替尼序贯'],
    total_conflicts=0,
    kendall_w=1.0,
)
append_experience(record1)

# 检索
results = search_similar_cases('NSCLC_Adenocarcinoma', mutation='EGFR_L858R', high_quality_only=False)
print(f'Search results: {len(results)} cases found')
assert len(results) >= 1, 'FAIL: should find at least 1 result'
assert results[0]['case_id'] == 'TEST-001', f'FAIL: wrong case_id: {results[0][\"case_id\"]}'
print('✅ Experience Library Unit Tests: PASSED')

# 打印库状态
stats = get_library_stats()
print(f'Library stats: {stats}')
"
```

### A4: Cross-Agent Validator 单元测试
```bash
# 创建测试输出文件（模拟 CR-002 冲突：急诊手术 + WBRT 并存）
cat > /tmp/test_sa_outputs.json << 'EOF'
{
  "imaging-specialist": {
    "max_diameter_cm": 4.5,
    "lesion_count": 1,
    "midline_shift": true,
    "mass_effect_level": "severe",
    "hydrocephalus": false,
    "is_eloquent_area": false,
    "location_details": "右侧额叶",
    "edema_index": 3.0,
    "hemorrhage_present": false,
    "imaging_citations": [],
    "local_rejected_alternatives": [],
    "kdp_votes": [],
    "decision_confidence": 0.85
  },
  "neurosurgery-specialist": {
    "surgical_urgency": "emergency",
    "surgical_goal": "decompression",
    "surgical_rationale": [],
    "anesthesia_risk_asa": 2,
    "bleeding_risk_concern": false,
    "medication_holding": [],
    "local_rejected_alternatives": [],
    "kdp_votes": [],
    "decision_confidence": 0.90
  },
  "radiation-oncology-specialist": {
    "is_radioresistant_histology": false,
    "radiation_modality": "WBRT",
    "dose_fractionation": "30Gy/10f",
    "dose_dual_track_verified": true,
    "radionecrosis_risk_score": 0.1,
    "radiation_citations": [],
    "local_rejected_alternatives": [],
    "kdp_votes": [],
    "decision_confidence": 0.70
  }
}
EOF

python3 tools/cross_agent_validator.py --outputs-json /tmp/test_sa_outputs.json
# 预期 exit_code=1 (CR-002 violation: emergency surgery + WBRT conflict)
echo "Exit code: $?"
```

---

## 4. Phase B — 集成冒烟测试（Smoke Tests）

### B1: 模块级冒烟（不启动 Agent）
```bash
# 冒烟测试脚本
python3 -c "
import sys, os
sys.path.insert(0, '.')
print('=== v7.0 Component Smoke Test ===')
errors = []

# 测试1: 仲裁权重计算
from core.arbitration_weights import compute_selection_priority
priority = compute_selection_priority('Level 1', 'Life-saving')
expected = 100 * 5.0  # = 500
assert abs(priority - 500) < 0.1, f'Priority calc wrong: {priority}'
print(f'  ✅ Arbitration: Level1+LifeSaving → Priority={priority}')

# 测试2: Safety check 空报告 → 应提示 minor warning
from core.safety_invariants import run_safety_check
result = run_safety_check('Module 0 Module 1 Module 2 Module 3 Module 4 Module 5 Module 6 Module 7 Module 8')
print(f'  ✅ Safety check: critical={len(result[\"critical_violations\"])}, minor={len(result[\"minor_violations\"])}')

# 测试3: Triage schema 可创建
from schemas.triage_schema import TriageOutput
triage = TriageOutput(
    complexity_level='simple',
    required_subagents=['imaging-specialist', 'primary-oncology-specialist', 'radiation-oncology-specialist'],
    activate_debate=False,
    triage_rationale='单发小病灶，EGFR突变明确',
    estimated_lesion_count=1,
    midline_shift_suspected=False,
    primary_known=True,
    estimated_treatment_line=1,
    emergency_flag=False,
    cancer_type_hint='NSCLC_Adenocarcinoma',
)
print(f'  ✅ TriageOutput schema: complexity={triage.complexity_level}, SAs={triage.required_subagents}')

# 测试4: AgreementMatrix schema 可创建
from schemas.conflict_schema import AgreementMatrix
matrix = AgreementMatrix(
    kendall_w_approx=0.92,
    pairwise_kappa={'agentA_vs_agentB': 0.85},
    per_kdp_agreement={'local_therapy_modality': 1.0},
    total_agents_participating=3,
    total_conflicts=0,
)
print(f'  ✅ AgreementMatrix schema: W={matrix.kendall_w_approx}')

print()
print('✅ v7.0 Component Smoke Test: ALL PASSED')
"
```

### B2: Agent 启动冒烟测试
```bash
# 仅测试 interactive_main.py 能否完成初始化（不运行任何 Case）
timeout 30 python3 -c "
import sys
sys.argv = ['interactive_main']  # 阻止 argparse 消费参数
# 只验证模块级代码（全局变量初始化）能运行
exec(open('interactive_main.py').read().split('if __name__')[0])
print('✅ interactive_main.py: Global initialization PASSED (no crashes)')
" 2>&1 | grep -E "(✅|❌|ERROR|Traceback|initialized|v7\.0)" | head -30
```

---

## 5. Phase C — 单 Case 端到端测试

### C1: 选择测试病例
```bash
# 从100例中选1个最简单的（单发、原发已知、有靶点）作为端到端测试
ls workspace/patients/ 2>/dev/null || ls data/patients/ 2>/dev/null | head -5
# 记录病例ID，后续使用
CASE_ID="YOUR_CASE_ID_HERE"
```

### C2: 执行单 Case 测试
```bash
conda activate tiantanBM_agent

# 使用 --max_cases 1 运行
python3 scripts/run_batch_eval.py \
  --max_cases 1 \
  --case_id "$CASE_ID" \
  --output_dir workspace/analysis_output/test_c2/ \
  2>&1 | tee logs/test_c2_$(date +%Y%m%d_%H%M%S).log
```

### C3: 验证 v7.0 特性是否生效
```bash
# 检查输出目录
ls -la workspace/analysis_output/test_c2/

# 检查1: Triage Gate 是否执行
grep -i "triage\|complexity_level\|required_subagents" logs/test_c2_*.log | head -10

# 检查2: Conflict Quantification 是否执行
ls workspace/sandbox/votes_*.json 2>/dev/null && echo "✅ KDP votes file created"
ls workspace/sandbox/all_sa_outputs_*.json 2>/dev/null && echo "✅ SA outputs file created"

# 检查3: Safety Audit JSON 是否生成
ls workspace/analysis_output/patients/*/reports/*_safety_audit.json 2>/dev/null \
  && echo "✅ Safety audit log exists"

# 检查4: 报告内容包含 Module 0-8
REPORT=$(ls workspace/analysis_output/patients/*/reports/*.md 2>/dev/null | head -1)
if [ -n "$REPORT" ]; then
  for MOD in "Module 0" "Module 1" "Module 2" "Module 3" "Module 4" "Module 5" "Module 6" "Module 7" "Module 8"; do
    grep -q "$MOD" "$REPORT" && echo "  ✅ $MOD present" || echo "  ❌ $MOD MISSING"
  done
fi

# 检查5: 安全审计结果
python3 -c "
import json, glob
files = glob.glob('workspace/analysis_output/patients/*/reports/*_safety_audit.json')
if not files:
    print('❌ No safety audit files found')
else:
    for f in files:
        data = json.load(open(f))
        status = '✅ PASSED' if data['passed'] else '🚨 BLOCKED'
        print(f'{status} - {f}')
        print(f'  Critical: {len(data[\"critical_violations\"])} | Major: {len(data[\"major_violations\"])} | Minor: {len(data[\"minor_violations\"])}')
"
```

### C4: 验证 Conflict Quantification 输出
```bash
python3 -c "
import json, glob

# 查找最新的 votes 文件
vote_files = glob.glob('workspace/sandbox/votes_*.json')
if not vote_files:
    print('⚠️  No votes files — 可能 Orchestrator 在此 Case 中跳过了冲突量化')
    print('   检查日志确认 Orchestrator 是否执行了 Phase 1.5')
else:
    for f in vote_files:
        data = json.load(open(f))
        print(f'Votes file: {f}')
        print(f'  Agents: {list(data.keys())}')
        for agent, votes in data.items():
            print(f'  {agent}: {votes}')
"
```

---

## 6. Phase D — 批量基线测评（R0 Baseline）

### D1: R0 批量运行
```bash
# 运行所有 56 Cases（10 + 46），建立 Round 0 基线
conda activate tiantanBM_agent

python3 scripts/run_batch_eval.py \
  --max_cases 56 \
  --output_dir workspace/analysis_output/R0/ \
  --evolution_round R0 \
  2>&1 | tee logs/R0_$(date +%Y%m%d_%H%M%S).log

echo "R0 运行完成，报告数量:"
ls workspace/analysis_output/R0/*.md 2>/dev/null | wc -l
```

### D2: R0 指标汇总
```bash
python3 -c "
import json, glob, statistics

results = []
for f in glob.glob('workspace/analysis_output/R0/**/*_safety_audit.json', recursive=True):
    data = json.load(open(f))
    results.append(data)

if not results:
    print('❌ No R0 results found')
else:
    n = len(results)
    blocked = sum(1 for r in results if not r['passed'])
    critical_counts = [len(r['critical_violations']) for r in results]
    major_counts = [len(r['major_violations']) for r in results]

    print(f'=== R0 Safety Invariant Summary ({n} cases) ===')
    print(f'  Pass rate:     {(n-blocked)/n*100:.1f}% ({n-blocked}/{n})')
    print(f'  Blocked:       {blocked}')
    print(f'  Avg Critical:  {statistics.mean(critical_counts):.2f}')
    print(f'  Avg Major:     {statistics.mean(major_counts):.2f}')
"
```

---

## 7. 进化机制：完整调整策略说明

> [!IMPORTANT]
> 这是规划书中最关键的部分：明确 Orchestrator 如何实施三种进化调整。

### 7.1 三种进化机制详解

#### 机制一：Prompt Refinement（R1 阶段）

**触发条件**: R0 完成后，EGR < 0.85 的 Case 或 Judge 分 < 30/40 的 Case

**执行主体**: 开发者（人工操作）+ LLM 辅助分析

**具体步骤**:

```python
# Step 1: 从 R0 结果中提取失败模式
python3 -c "
import json, glob, re
from collections import Counter

# 汇总所有错误
all_errors = []
for f in glob.glob('workspace/analysis_output/R0/**/*_safety_audit.json', recursive=True):
    data = json.load(open(f))
    for v in data['critical_violations'] + data['major_violations']:
        all_errors.append(v['rule_id'] + ':' + v['rule_name'])

counter = Counter(all_errors)
print('=== Top Error Patterns in R0 ===')
for error, count in counter.most_common(10):
    print(f'  {count}x {error}')
"

# Step 2: 人工判断哪个 SA 最常触发哪类错误
# (例如: SI-007 缺少 OncoKB 引用 → primary-oncology SA 需要加强提示)

# Step 3: 修改对应的 SA prompt 文件
# 示例：在 agents/primary_oncology_prompt.py 中添加：
# "### 强制: 每条靶向药推荐必须附 [OncoKB Level X] 引用，否则不合格"
```

**Prompt 修改规则**（防止过拟合）:
- 每次只修改 1 个 SA 的 prompt
- 修改内容限于：new mandatory rules、new output examples、warning emphasis
- 禁止修改核心角色定义和航道限制
- 每次修改前 commit 一个 git tag

#### 机制二：Experience Library 注入（R2 阶段）

**触发条件**: R1 完成后，Experience Library 有 ≥ 10 条高质量 Case 记录

**执行主体**: Orchestrator 在 Phase 0 (Triage) 后自动执行

**具体步骤**:

```python
# Orchestrator 在 Phase 0 完成后，Prompt 中现在已有以下指令：
# "将经验库检索结果注入后续 SA 上下文"

# 开发者需要实现: 在 interactive_main.py 的 Orchestrator 初始化之前
# 将经验库检索结果预置为系统 context

# 推荐实现方式: 在 run_batch_eval.py 中，每次 Case 开始前：
from core.experience_library import search_similar_cases, format_for_context_injection

similar = search_similar_cases(
    cancer_type=case_metadata.get('cancer_type', ''),
    mutation=case_metadata.get('mutation', ''),
    treatment_line=case_metadata.get('treatment_line', -1),
    top_k=3,
    high_quality_only=True
)
experience_context = format_for_context_injection(similar)
# 将 experience_context 注入 Orchestrator 的初始 user message 前缀
```

**注入位置**: 作为每个 Case 的用户消息的头部前缀（不修改 system prompt）

#### 机制三：Arbitration Weight Tuning（R3 阶段）

**触发条件**: R2 完成后，发现某类冲突被系统性裁错（专家标注与系统裁决不一致 ≥ 3 次）

**执行主体**: 开发者通过专家标注结果调用 `adjust_weight()`

**Orchestrator 如何执行调整**（关键流程）:

```python
# Orchestrator 本身不主动调整权重
# 权重调整由如下循环驱动：

# 1. R2 完成后，收集专家标注结果 vs 系统裁决对比
# 2. 发现系统性偏差（例如：Functional_Survival 权重太低，导致靶向药场景被
#    错误压制为 Life-saving 路径）
# 3. 调用 adjust_weight() 微调

from core.arbitration_weights import adjust_weight

# 示例: 提高 Functional_Survival 权重 5%
adjust_weight(
    factor_path="clinical_priority_weights.Functional_Survival",
    direction="increase",
    case_id="CASE-042",  # 触发此调整的具体案例
    reason="专家标注显示EGFR+单发脑转移应优先靶向主导路径，但系统低估了Functional_Survival权重"
)

# 4. 下次 Orchestrator 运行时，自动通过 load_weights() 使用新权重
# 无需重启 Agent，权重在每次 compute_selection_priority 调用时实时读取
```

**关键原则**:
- `damping=0.05`（每次只调整 5%），防止单个 Case 导致过拟合
- 每次调整后验证在 5 个历史 Case 上的结果是否改善
- 最多连续调整 3 次同一因子，然后观察批量效果

### 7.2 进化调整完整时序图

```
R0: 56 Cases × 原始 v7.0
    ↓ 收集: EGR, SCR, Safety Audit, Conflict Stats
    ↓ 分析: Top Error Patterns, Conflict Frequency Heat Map

R1: 修改 SA Prompts (Prompt Refinement)
    ↓ 针对 Top-3 错误类型，只改对应 SA 的 prompt 文件
    ↓ 重新运行 56 Cases
    ↓ 对比 ΔMetrics (R1 vs R0)
    ↓ 将 R0+R1 的高质量 Case 写入 Experience Library

R2: +Experience Library Injection
    ↓ 每个 Case 开始前检索相似历史，注入 Orchestrator context
    ↓ 重新运行 56 Cases
    ↓ 对比 ΔMetrics (R2 vs R1)
    ↓ 分析剩余的错误集中在什么场景

R3: +Arbitration Weight Tuning
    ↓ 根据专家复核 + Judge 评分，调整被系统性误判的仲裁权重
    ↓ 重新运行 56 Cases
    ↓ 最终 ΔMetrics (R3 vs R0) = 论文核心结果图
```

---

## 8. Phase E — 进化迭代测试（R1-R3）

### E1: R1 指标对比脚本
```bash
# 运行 R1（已修改 SA prompts 后）
python3 scripts/run_batch_eval.py \
  --max_cases 56 \
  --output_dir workspace/analysis_output/R1/ \
  --evolution_round R1 \
  2>&1 | tee logs/R1_$(date +%Y%m%d_%H%M%S).log

# 对比 R0 vs R1
python3 -c "
import json, glob

def get_metrics(round_dir):
    files = glob.glob(f'workspace/analysis_output/{round_dir}/**/*_safety_audit.json', recursive=True)
    if not files:
        return None
    n = len(files)
    blocked = sum(1 for f in files if not json.load(open(f))['passed'])
    critical = sum(len(json.load(open(f))['critical_violations']) for f in files)
    return {'n': n, 'pass_rate': (n-blocked)/n, 'avg_critical': critical/n}

r0 = get_metrics('R0')
r1 = get_metrics('R1')

if r0 and r1:
    print(f'=== R0 vs R1 Comparison ===')
    print(f'Pass Rate: R0={r0[\"pass_rate\"]*100:.1f}% → R1={r1[\"pass_rate\"]*100:.1f}%  Δ={((r1[\"pass_rate\"]-r0[\"pass_rate\"])*100):+.1f}%')
    print(f'Avg Critical: R0={r0[\"avg_critical\"]:.2f} → R1={r1[\"avg_critical\"]:.2f}  Δ={r1[\"avg_critical\"]-r0[\"avg_critical\"]:+.2f}')
"
```

### E2: 进化日志追踪
```bash
python3 -c "
from core.arbitration_weights import get_evolution_summary
summary = get_evolution_summary()
print(f'=== Evolution Log ===')
print(f'Current version: {summary[\"version\"]}')
print(f'Total adjustments: {summary[\"total_adjustments\"]}')
print(f'Factors adjusted: {summary[\"factors_adjusted\"]}')
import json
print(json.dumps(summary.get(\"log\", [])[-5:], indent=2, ensure_ascii=False))
"
```

---

## 9. 可靠性 & 可维护性设计说明

### 9.1 可靠性保障

| 风险点 | 现有防护 | 建议增强 |
|:-------|:---------|:---------|
| SA 输出 schema 不合规 | Pydantic v2 强制校验 | 添加 `model_validator` 对 confidence 范围的额外校验 |
| Orchestrator 绕过 Auditor | `submit_mdt_report` 强制 3 关卡 | 增加 mutex 防止并发提交 |
| 仲裁权重文件损坏 | `reset_to_defaults()` | 增加 JSON schema 校验 |
| SQLite 并发写入 | 串行处理 | 批量模式下添加 WAL journal mode |
| Experience Library 增长过快 | JSONL 追加，FTS5 检索 | > 1000 条时自动归档旧记录到 `archive/` |
| Safety Invariant 漏报 | 15条规则覆盖 | 每次 SA prompt 修改后运行 Safety Unit Test |

### 9.2 可扩展性设计

```python
# 添加新 Safety Rule 的步骤（1-2分钟操作）:
# 在 core/safety_invariants.py 的 SAFETY_INVARIANTS 列表中添加:
{
    "id": "SI-016",
    "name": "new_rule_name",
    "severity": "major",
    "description": "规则说明",
    "check_type": "regex",  # 或 "custom" / "keyword_required"
    "check_pattern": r"...",
    "reference": "[文献] ...",
    "remediation": "修复建议",
}
# 无需修改任何其他文件，规则自动被 run_safety_check() 执行

# 添加新 KDP 的步骤:
# 在 schemas/conflict_schema.py 的 STANDARD_KDP_IDS 和
# KDP_OPTIONS 中添加新项，所有 SA Schema 的 kdp_votes 字段自动包含

# 添加新 SubAgent 的步骤:
# 1. 创建 agents/new_specialist_prompt.py
# 2. 在 schemas/v6_expert_schemas.py 添加输出 Schema
# 3. 在 interactive_main.py 注册 SA dict
# 4. 在 agents/triage_prompt.py 的 required_subagents 说明中添加
```

### 9.3 可维护性约定

| 约定 | 说明 |
|:-----|:-----|
| **版本控制** | 每次 SA prompt 修改前打 git tag (如 `v7.0-R1-oncology-prompt`) |
| **权重变更记录** | 所有权重调整自动写入 `evolution_log`，可完整复现 |
| **日志分级** | `logs/R0_*.log`, `logs/R1_*.log` 按进化轮次分离 |
| **测试隔离** | 每个进化轮次使用独立 `output_dir`，防止结果污染 |
| **回滚机制** | `reset_to_defaults()` 可随时复原仲裁权重；git revert 可复原 prompt |
| **文档同步** | 每次架构修改后更新 `CHANGELOG.md`，标注 v7.0.x |

---

## 10. 快速参考：本次测试指令顺序

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Day 1: 部署验证
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
git pull origin main
conda activate tiantanBM_agent
mkdir -p workspace/{evolution,memory,sandbox,analysis_output/patients} logs
python3 -c "from core.arbitration_weights import load_weights; load_weights()"
python3 -c "from core.episodic_memory import init_db; init_db().close()"

# Phase A: Unit Tests
python3 -m pytest tests/test_safety_invariants.py -v 2>/dev/null || \
  python3 -c "[A1 test above]"  # 使用上文的内联测试
python3 tools/conflict_calculator.py --votes-json /tmp/test_votes.json

# Phase B: Smoke Test
python3 -c "[B1 test above]"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Day 1-2: 单 Case 端到端
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python3 scripts/run_batch_eval.py --max_cases 1 --output_dir workspace/analysis_output/test/
[验证 C3, C4 所有检查项]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Day 2-3: R0 Baseline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python3 scripts/run_batch_eval.py --max_cases 56 --output_dir workspace/analysis_output/R0/ --evolution_round R0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Week 2: R1 (Prompt Refinement)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[分析 R0 错误模式 → 修改 SA prompts → git commit → run R1]

# Week 3: R2 + R3
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[填充 Experience Library → run R2 → Weight Tuning → run R3]
```

---

## 11. 未完成构件说明（需后续实施）

| 构件 | WS | 优先级 | 影响 |
|:-----|:--:|:------:|:-----|
| **SA Prompts confidence 注解** | WS-4 | 🔴 高 | SA 不会填写 confidence 字段，所有 decisions_confidence=0.75 (默认) |
| **Evaluation LLM-as-Judge** | WS-3 | 🔴 高 | judge_scores 为空，无法评估 esr_total，进化信号缺失 |
| **`run_batch_eval.py` v7.0 适配** | — | 🔴 高 | 现有批量脚本可能不支持 `evolution_round` 参数和经验库写入 |
| **Orchestrator Phase 1.5 沙盒写文件** | WS-2 | 🟡 中 | votes JSON 写入需要正确的沙盒路径，Orchestrator 需要明确的文件命名约定 |
| **`setup_workspace.py` 脚本** | — | 🟡 中 | 部署时需手动建目录，自动化脚本缺失 |
| **Guideline 版本锚定** | — | 🟢 低 | 当前未限制，NCCN 版本不一致风险 |

> 优先级排序: **SA Prompts confidence注解** 和 **LLM-as-Judge** 是下一步最需要完成的两个构件，因为没有它们，进化信号（judge_scores）无从产生，R1-R3 的改善将无法定量评估。
