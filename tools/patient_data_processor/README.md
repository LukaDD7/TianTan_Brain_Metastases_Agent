# Patient Data Processor Skill

患者输入数据处理器 Skill - 确保BM Agent输入数据的纯净性

## 快速开始

### 1. 验证现有文件是否污染

```bash
cd /media/luzhenyang/project/TianTan_Brain_Metastases_Agent

# 预览模式（只检测，不修改）
python skills/patient_data_processor/scripts/clean_contaminated_files.py

# 实际清理（会备份原文件）
python skills/patient_data_processor/scripts/clean_contaminated_files.py --execute
```

### 2. 从Excel重新生成干净输入文件

```bash
# 批量处理所有患者
python skills/patient_data_processor/scripts/batch_process.py

# 处理指定患者
python skills/patient_data_processor/scripts/batch_process.py \
    --patients 640880,708387,747724

# 仅验证（不生成）
python skills/patient_data_processor/scripts/batch_process.py --validate-only
```

### 3. Python API使用

```python
from skills.patient_data_processor.scripts.patient_data_processor import PatientDataProcessor

# 初始化
processor = PatientDataProcessor("workspace/test_cases_wide.xlsx")

# 处理单个患者
result = processor.process_patient(
    patient_id="640880",
    output_path="workspace/sandbox/patient_640880_input.txt"
)

print(f"成功: {result.success}")
print(f"移除字段: {result.removed_fields}")
print(f"警告: {result.warnings}")

# 验证文件
is_valid, violations = processor.validate_input_file(
    "workspace/sandbox/patient_640880_input.txt"
)
```

## 字段定义

### ✅ 允许的输入字段（白名单）

| 字段名 | 类型 | 必需 |
|--------|------|------|
| 住院号 | 标识 | ✅ |
| 入院时间 | 日期 | ✅ |
| 年龄 | 数值 | ✅ |
| 性别 | 枚举 | ✅ |
| 主诉 | 文本 | ✅ |
| 现病史 | 文本 | ✅ |
| 既往史 | 文本 | ✅ |
| 头部MRI | 文本 | ✅ |
| 胸部CT | 文本 | ❌ |
| 颈椎MRI | 文本 | ❌ |
| 腰椎MRI | 文本 | ❌ |
| 腹盆CT | 文本 | ❌ |
| 病理诊断 | 文本 | ❌ |

### ❌ 禁止的敏感字段（黑名单）

| 字段名 | 原因 |
|--------|------|
| 入院诊断 | Ground Truth标签 |
| 出院诊断 | Ground Truth标签 |
| 诊疗经过 | 包含治疗方案和剂量 |

## 数据污染案例

### 污染示例（❌）

```
住院号 640880。入院时间 2025年03月07日。年龄 54。性别 女。
主诉 肺癌病史...
现病史 患者于2016年发现肺部肿物...
既往史 无心血管疾病...
入院诊断 初步诊断：恶性肿瘤放疗 颅内继发恶性肿瘤(肺癌)  ❌ 敏感字段
出院诊断 确定诊断：恶性肿瘤放疗 颅内继发恶性肿瘤(肺癌)  ❌ 敏感字段
诊疗经过 2％利多卡因局麻下Leksell立体定向架...给予周边剂量16 Gy...  ❌ 包含剂量
头部MRI 右额顶部骨质呈术后改变...
```

### 清理后示例（✅）

```
住院号 640880。入院时间 2025年03月07日。年龄 54。性别 女。
主诉 肺癌病史，脑转移瘤开颅术后4年，发现颅内新发强化结节2月。
现病史 患者于2016年发现肺部肿物，手术切除，病理：肺癌，术后化疗。2020年因脑转移瘤我院开颅手术...
既往史 无心血管疾病，无代谢性疾病...
头部MRI 右额顶部骨质呈术后改变...
```

## 处理流程

```
Excel原始数据
    ↓
[PatientDataProcessor]
    ↓
检测敏感字段 ──→ 移除敏感字段
    ↓
内容安全检查 ──→ 警告治疗关键词
    ↓
格式化输出 ──→ patient_xxx_input.txt
    ↓
验证 ──→ 确认无敏感内容
```

## 输出示例

```
$ python batch_process.py

================================================================================
  批量患者数据处理器
  Batch Patient Data Processor v1.0
================================================================================

数据源: workspace/test_cases_wide.xlsx
输出目录: workspace/sandbox
处理全部 9 例患者

[INFO] 加载Excel: workspace/test_cases_wide.xlsx
[INFO] 共 9 例患者, 21 个字段
[WARNING] Excel中包含敏感字段: ['入院诊断', '出院诊断', '诊疗经过']
[INFO] 处理时将自动移除这些字段

[INFO] 已保存: workspace/sandbox/patient_605525_input.txt
[INFO] 已保存: workspace/sandbox/patient_612908_input.txt
...

统计:
  成功: 9/9
  警告: 3 例需要人工复核

详细报告: workspace/sandbox/batch_processing_report_20260402_143052.md
```

## 报告内容

处理报告包含：
- 处理统计（成功/失败/警告）
- 自动移除的敏感字段列表
- 内容安全警告（需要人工复核的条目）
- 每个患者的详细处理结果

## 注意事项

1. **备份**：实际清理前会自动备份原文件到 `input_backups/` 目录
2. **警告**：部分现病史可能包含治疗信息，需要人工复核
3. **验证**：处理后务必运行 `--validate-only` 确认无残留

## 文件结构

```
skills/patient_data_processor/
├── SKILL.md                              # Skill定义文档
├── README.md                             # 本文件
└── scripts/
    ├── patient_data_processor.py        # 核心处理器
    ├── batch_process.py                 # 批量处理脚本
    └── clean_contaminated_files.py      # 污染清理脚本
```

## 与Baseline的对齐

本Skill生成的输入文件与Baseline评估严格一致：

- **Baseline CSV** → 使用相同白名单字段
- **BM Agent Input** → 本Skill生成的输入
- **Excel原始数据** → Ground Truth（仅用于评估对比）

## 版本历史

- v1.0.0 (2026-04-02): 初始版本，解决数据污染问题
