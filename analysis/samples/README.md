# 分析样本库

## 目录结构

```
samples/
├── 868183/          # 患者868183 (Case3) - 肺癌脑转移(SMARCA4突变) - 新增
├── 747724/          # 患者747724 (Case10)
├── 708387/          # 患者708387 (Case9) - 肺癌脑转移(MET扩增)
├── 665548/          # 患者665548 (Case4)
├── 648772/          # 患者648772 (Case1)
├── 640880/          # 患者640880 (Case2) - 肺癌脑转移
├── 638114/          # 患者638114 (Case6) - 乳腺癌脑转移
├── 612908/          # 患者612908 (Case7) - 肺癌脑转移
├── 605525/          # 患者605525 (Case8) - 结肠癌脑转移
└── README.md        # 本文件
```

## 每个样本包含

| 文件 | 说明 |
|------|------|
| `MDT_Report_{id}.md` | BM Agent生成的8模块MDT报告 |
| `patient_{id}_input.txt` | 原始患者输入数据 |
| `bm_agent_execution_log.jsonl` | 结构化执行日志 |
| `bm_agent_complete.log` | 人类可读完整日志 |
| `baseline_results.json` | 3种Baseline方法结果 |

## 样本统计

| 患者ID | Case标签 | 医院ID | BM Agent | Baseline | 状态 |
|--------|----------|--------|----------|----------|------|
| 868183 | Case3 | 868183 | ✅ | ✅ | **可分析** |
| 747724 | Case10 | 747724 | ✅ | ✅ | **可分析** |
| 708387 | Case9 | 708387 | ✅ | ✅ | **可分析** |
| 665548 | Case4 | 665548 | ✅ | ✅ | **可分析** |
| 648772 | Case1 | 648772 | ✅ | ✅ | **可分析** |
| 640880 | Case2 | 640880 | ✅ | ✅ | **可分析** |
| 638114 | Case6 | 638114 | ✅ | ✅ | **可分析** |
| 612908 | Case7 | 612908 | ✅ | ✅ | **可分析** |
| 605525 | Case8 | 605525 | ✅ | ✅ | **可分析** |

## 使用方法

```python
# 加载样本数据
import json

# 加载BM Agent报告
with open('samples/605525/MDT_Report_605525.md') as f:
    report = f.read()

# 加载执行日志提取token和latency
data = []
with open('samples/605525/bm_agent_execution_log.jsonl') as f:
    for line in f:
        data.append(json.loads(line))

# 加载Baseline结果
with open('samples/605525/baseline_results.json') as f:
    baseline = json.load(f)
```

