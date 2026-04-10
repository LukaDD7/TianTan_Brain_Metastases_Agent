---
name: patient_data_processor
description: |
  患者输入数据处理器（Patient Data Processor, PDP）- 医疗AI评估数据准备的标准化组件
  
  核心功能：
  1. 将原始临床数据（长表格式）转换为BM Agent标准化输入格式
  2. 严格执行输入特征（Input Features）与标签（Ground Truth Labels）的物理隔离
  3. 建立可追溯的数据处理审计链（Data Processing Audit Trail）
  4. 提供多层级验证机制确保数据无污染
  
  适用场景：
  - 脑转移瘤MDT评估系统的患者数据预处理
  - 任何需要严格区分输入/标签的医疗AI评估任务
  
  设计原则：
  - 不可变性（Immutability）：原始数据只读，绝不修改
  - 可追溯性（Traceability）：每个处理步骤留痕
  - 可复现性（Reproducibility）：相同输入产生相同输出
  - 可验证性（Verifiability）：多重校验确保数据质量

type: data_processing
version: 2.0.0
author: TianTan Brain Metastases Agent Team
last_updated: 2026-04-02
---

# Patient Data Processor Skill v2.0

## 1. 术语定义与概念框架

### 1.1 数据分类体系

本Skill严格遵循医疗AI评估的数据分类标准，将临床数据划分为三个互斥类别：

#### 1.1.1 输入特征（Input Features, X）
**定义**：患者就诊时客观采集的临床信息，不依赖于任何诊疗决策或结果判断。

**特征清单**：
| 字段英文名 | 字段中文名 | 数据类型 | 必需性 | 临床定义 |
|-----------|-----------|---------|--------|---------|
| patient_id | 住院号 | String | 必填 | 患者唯一标识符，贯穿整个住院周期 |
| admission_date | 入院时间 | DateTime | 必填 | 患者办理入院手续的时间戳 |
| age | 年龄 | Numeric | 必填 | 患者入院时的周岁年龄 |
| gender | 性别 | Categorical | 必填 | 生理性别（男/女） |
| chief_complaint | 主诉 | Text | 必填 | 患者主观感受到的最主要症状及持续时间 |
| history_of_present_illness | 现病史 | Text | 必填 | 本次疾病的起病、发展、诊疗过程（仅含外部诊疗史） |
| past_medical_history | 既往史 | Text | 必填 | 既往疾病、手术史、过敏史等 |
| brain_mri | 头部MRI | Text | 必填 | 脑部磁共振影像的客观描述 |
| chest_ct | 胸部CT | Text | 选填 | 胸部CT影像的客观描述 |
| cervical_mri | 颈椎MRI | Text | 选填 | 颈椎磁共振影像的客观描述 |
| thoracic_mri | 胸椎MRI | Text | 选填 | 胸椎磁共振影像的客观描述 |
| lumbar_mri | 腰椎MRI | Text | 选填 | 腰椎磁共振影像的客观描述 |
| abdominal_pelvic_ct | 腹盆CT | Text | 选填 | 腹部/盆腔CT影像的客观描述 |
| abdominal_pelvic_mri | 腹盆MRI | Text | 选填 | 腹部/盆腔MRI影像的客观描述 |
| abdominal_ultrasound | 腹部超声 | Text | 选填 | 腹部超声检查结果 |
| superficial_lymph_node_ultrasound | 浅表淋巴结超声 | Text | 选填 | 浅表淋巴结超声检查结果 |

#### 1.1.2 标签数据（Ground Truth Labels, Y）
**定义**：基于完整诊疗过程形成的诊断结论和治疗决策，用于评估Agent输出的准确性。

**严禁混入输入的字段（第一层检查）**：
| 字段英文名 | 字段中文名 | 排除原因 |
|-----------|-----------|---------|
| admission_diagnosis | 入院诊断 | 医生基于初步评估形成的诊断结论 |
| discharge_diagnosis | 出院诊断 | 完整诊疗后的确定性诊断 |
| **treatment_course** | **诊疗经过** | **包含本次住院期间的治疗决策、用药、手术等** |
| discharge_date | 出院时间 | 通常隐含诊疗结果信息 |

**⚠️ 关键区分 - 既往治疗史 vs 本次诊疗经过**：

| 类别 | 定义 | 示例 | 处理方式 |
|------|------|------|---------|
| **既往治疗史** | 患者**之前**在其他医院或既往住院接受的治疗 | "患者2016年确诊肺癌，术后化疗4周期" | ✅ **保留** - 属于输入特征X |
| **本次诊疗经过** | 患者**本次住院期间**接受的治疗决策和用药 | "本次入院后行培美曲塞化疗" | ❌ **移除** - 属于标签Y |

**第二层检查重点**：  
检查"现病史"字段是否混入"本次诊疗经过"内容，而非"既往治疗史"。

#### 1.1.3 元数据（Metadata, M）
**定义**：用于数据管理和追溯的辅助信息，不参与模型输入或评估。

| 字段 | 说明 |
|-----|------|
| visit_id | 就诊批次标识 |
| source_file | 源文件路径 |
| processing_timestamp | 处理时间戳 |
| processor_version | 处理器版本 |

### 1.2 数据格式定义

#### 1.2.1 源数据格式（Source Format）
**格式类型**：长表格式（Long Format）
**文件类型**：Excel (.xlsx)
**必需列**：
- `id`: 患者唯一标识
- `Visit`: 就诊批次
- `Feature`: 特征名称（必须为1.1.1或1.1.2中定义的字段）
- `Value`: 特征值

#### 1.2.2 目标输出格式（Target Format）
**格式类型**：纯文本（Plain Text）
**文件编码**：UTF-8
**分隔符**：空格 + 句号（中文句号"，"或英文句号"."）
**换行符**：LF (\n)

**输出模板**：
```
住院号 {patient_id}。入院时间 {admission_date}。年龄 {age}。性别 {gender}。
主诉 {chief_complaint}。
现病史 {history_of_present_illness}。
既往史 {past_medical_history}。
头部MRI {brain_mri}。
[胸部CT {chest_ct}。]
[颈椎MRI {cervical_mri}。]
[胸椎MRI {thoracic_mri}。]
[腰椎MRI {lumbar_mri}。]
[腹盆CT {abdominal_pelvic_ct}。]
[腹盆MRI {abdominal_pelvic_mri}。]
[腹部超声 {abdominal_ultrasound}。]
[浅表淋巴结超声 {superficial_lymph_node_ultrasound}。]
```

**关键约束**：
1. **内容不可变性**：从Excel读取的Value字段必须原样输出，不得进行任何字符修改
2. **分隔符统一性**：字段名与值之间用空格分隔，字段结尾用句号
3. **可选字段处理**：空值字段整行省略，不输出空内容
4. **格式严格性**：不允许添加任何额外描述、注释或格式化字符

### 1.3 数据污染定义

**数据污染（Data Contamination）**：指将本应用于评估模型性能的Ground Truth标签意外混入模型输入，导致评估结果失真的现象。

**污染类型**：
1. **直接污染**：输入文件中包含标签字段（入院诊断、出院诊断、诊疗经过）
2. **间接污染**：输入字段中嵌套包含治疗决策信息（如现病史中详细描述本次住院的用药剂量）
3. **元数据泄漏**：文件路径、时间戳等信息暗示患者身份或治疗结果

## 2. 系统架构

### 2.1 处理流水线（Processing Pipeline）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Patient Data Processor Pipeline                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│  │   Input      │     │  Processing  │     │   Output     │             │
│  │   Stage      │ --> │    Stage     │ --> │    Stage     │             │
│  └──────────────┘     └──────────────┘     └──────────────┘             │
│         │                   │                   │                        │
│         ▼                   ▼                   ▼                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│  │ 1.1 Load     │     │ 2.1 Parse    │     │ 3.1 Format   │             │
│  │     Source   │     │     Records  │     │     Output   │             │
│  ├──────────────┤     ├──────────────┤     ├──────────────┤             │
│  │ 1.2 Validate │     │ 2.2 Filter   │     │ 3.2 Write    │             │
│  │     Schema   │     │     Features │     │     File     │             │
│  ├──────────────┤     ├──────────────┤     ├──────────────┤             │
│  │ 1.3 Check    │     │ 2.3 Detect   │     │ 3.3 Verify   │             │
│  │     Access   │     │     Leakage  │     │     Content  │             │
│  └──────────────┘     ├──────────────┤     ├──────────────┤             │
│                       │ 2.4 Generate │     │ 3.4 Create   │             │
│                       │     Audit    │     │     Receipt  │             │
│                       └──────────────┘     └──────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构规范

**工作目录树**：
```
PROJECT_ROOT/
├── patients_folder/                    # 原始患者数据（只读）
│   └── 46个病例_诊疗经过.xlsx           # 源Excel文件
│
├── workspace/                          # 工作空间
│   ├── sandbox/                        # Agent工作目录（输入输出）
│   │   ├── patient_{id}_input.txt      # 生成的输入文件
│   │   ├── patient_{id}_V2_input.txt   # 同一患者第2次就诊
│   │   ├── patient_{id}_V3_input.txt   # 同一患者第3次就诊
│   │   └── input_backups/              # 备份目录
│   │       └── {timestamp}/
│   │           └── patient_{id}_input.txt.backup
│   │
│   └── processing_logs/                # 处理日志
│       ├── processing_{timestamp}.log
│       ├── batch_report_{timestamp}.json  # 批量处理统计报告
│       └── verification_{timestamp}.json
│
└── skills/
    └── patient_data_processor/         # 本Skill
        ├── SKILL.md
        ├── README.md
        └── scripts/
            ├── __init__.py
            ├── processor_core.py       # 核心处理模块
            └── cli.py                  # 命令行接口
```

#### 多次就诊记录处理

**问题背景**：同一患者可能多次住院，使用相同住院号。若简单覆盖，会导致数据丢失。

**处理方式**：
1. **自动检测**：扫描所有Case，识别重复住院号
2. **版本标记**：为重复住院号添加后缀 `_V{n}`
   - 第1次就诊：`patient_{住院号}_input.txt`
   - 第2次就诊：`patient_{住院号}_V2_input.txt`
   - 第3次就诊：`patient_{住院号}_V3_input.txt`
3. **统计报告**：在报告中详细记录重复情况

**示例**：
```
住院号 466104: 4次就诊
  - Case12 → patient_466104_input.txt
  - Case13 → patient_466104_V2_input.txt
  - Case35 → patient_466104_V3_input.txt
  - Case36 → patient_466104_V4_input.txt
```

### 2.3 版本控制策略

**版本命名规范**：遵循语义化版本控制（Semantic Versioning）
- 主版本号（Major）：数据格式或处理逻辑的重大变更
- 次版本号（Minor）：功能增强或性能优化
- 修订号（Patch）：Bug修复或文档更新

**版本追踪机制**：
1. 每个输出文件包含处理器版本号（文件头注释）
2. 处理日志记录版本号、输入文件哈希值、输出文件哈希值
3. 使用Git管理代码版本，标签（Tag）标记发布版本

## 3. 处理流程详解

### 3.1 输入阶段（Input Stage）

#### 3.1.1 加载源数据（Load Source）
**输入**：Excel文件路径
**输出**：DataFrame对象
**约束**：
- 文件必须为只读打开模式
- 禁止对源文件进行任何写操作
- 加载后计算文件MD5哈希值用于后续验证

#### 3.1.2 验证Schema（Validate Schema）
**验证项**：
1. 必需列存在性：`id`, `Visit`, `Feature`, `Value`
2. 数据类型：所有列为字符串类型或兼容类型
3. 特征名称白名单：所有`Feature`值必须在预定义列表中

**错误处理**：
- Schema验证失败 → 终止处理并记录错误
- 发现未知Feature → 标记警告并跳过该记录

#### 3.1.3 访问权限检查（Check Access）
**检查项**：
1. 源文件是否为只读
2. 输出目录是否有写入权限
3. 备份目录是否有写入权限

### 3.2 处理阶段（Processing Stage）

#### 3.2.1 解析记录（Parse Records）
**处理逻辑**：
1. 按`id`分组，将长表格式转换为宽表格式
2. 每个患者生成一个记录字典
3. 保留`Feature`→`Value`的原始映射关系

**数据转换示例**：
```python
# 长表输入
# id | Feature | Value
# 1  | 住院号   | 640880
# 1  | 年龄     | 49岁

# 宽表输出
# {
#   "patient_id": "640880",
#   "age": "49岁"
# }
```

#### 3.2.2 特征过滤（Filter Features）
**过滤规则**：
1. 仅保留白名单字段（1.1.1节定义）
2. 移除黑名单字段（1.1.2节定义）
3. 可选字段为空时从输出中省略

#### 3.2.3 信息泄露检查（Leakage Detection）
**双重检查机制**（Double-Check System）：

| 检查层 | 执行者 | 检查方式 | 处理能力 | 记录方式 |
|--------|--------|----------|----------|----------|
| **第一层 - 字段级** | Python代码自动 | 白名单/黑名单过滤 | 字段存在性 | `removed_fields` |
| **第二层 - 语义级** | Claude Code (LLM) | 语义分析理解 | 隐含治疗信息 | `semantic_warnings` |

**第一层 - 字段级检查（自动）**：
- 白名单过滤：只保留 `ALLOWED_FEATURES` 中定义的16个字段
- 黑名单移除：强制移除 `BLACKLIST_FEATURES`（入院诊断、出院诊断、诊疗经过、出院时间）
- 未知字段警告：记录并忽略未定义字段

**第二层 - 语义级检查（LLM）**：
> ⚠️ **关键要求**：此层检查必须由 Claude Code 通过大语言模型的语义理解能力执行，而非简单的关键词匹配。
> 
> **核心任务：区分"既往治疗史"与"本次诊疗经过"**
> 
> | 类别 | 定义 | 正确示例 | 错误示例（需标记） |
> |------|------|---------|------------------|
> | **既往治疗史** ✅ | 患者**之前**接受的治疗 | "患者2016年确诊肺癌，术后化疗4周期" | - |
> | **本次诊疗经过** ❌ | 患者**本次住院期间**接受的治疗 | - | "本次入院后行培美曲塞化疗3周期" |

Claude Code 需要：
1. **读取生成的输出文件**（如 `patient_640880_input.txt`）
2. **语义分析每个字段内容**，识别以下内容：
   - **时间词识别**："本次入院"、"入院后"、"本次住院" → 暗示本次诊疗经过
   - **治疗决策词**："拟行"、"计划"、"给予" → 暗示入院后的治疗计划
   - **疗效评估词**："本次治疗后病变缩小" → 暗示入院后的治疗反应

3. **生成语义警告**：当检测到以下情况时记录警告：
   - ⚠️ **HIGH**: 现病史中包含"本次入院后"的治疗记录
   - ⚠️ **MEDIUM**: 主诉中包含入院后的治疗计划
   - ⚠️ **LOW**: 既往史中混有本次住院信息

**语义检查示例**：
```
✅ 正确的既往治疗史（保留）:
"患者2016-3确诊肺癌...术后多西他赛+奈达铂化疗4周期..."
→ 这是既往治疗史，属于合理的输入特征

❌ 错误的本次诊疗经过（需标记）:
"本次入院后行右额顶转移瘤切除术，术后病理提示..."
→ 这是本次住院期间的治疗，属于标签Y，不应出现在输入中

❌ 错误的治疗计划（需标记）:
"拟行全脑放疗，总剂量30Gy/10f"
→ 这是入院后的治疗计划，属于标签Y
```

**与第一层检查的区别**：
- 第一层：字段级过滤，移除"诊疗经过"字段（机械过滤）
- 第二层：语义级识别，检查"现病史"中是否混入"本次诊疗经过"（语义理解）
- **关键**：既往治疗史是合理的，本次诊疗经过才是不应该的

**审计记录**：
```json
{
  "patient_id": "640880",
  "removed_fields": ["入院诊断", "诊疗经过"],  // 第一层
  "semantic_warnings": [                       // 第二层
    "现病史包含'本次入院后'的治疗记录",
    "主诉包含入院后的治疗计划：拟行化疗"
  ]
}
```

#### 3.2.4 生成审计日志（Generate Audit）
**审计记录内容**：
```json
{
  "processing_id": "uuid",
  "timestamp": "ISO8601",
  "processor_version": "2.0.0",
  "source": {
    "file_path": "...",
    "file_hash": "md5",
    "total_records": 538,
    "unique_patients": 46
  },
  "operations": [
    {
      "patient_id": "640880",
      "removed_fields": ["入院诊断", "诊疗经过"],
      "warnings": [],
      "output_hash": "md5"
    }
  ]
}
```

### 3.3 输出阶段（Output Stage）

#### 3.3.1 格式化输出（Format Output）
**格式规范**：
1. 字段顺序固定：住院号→入院时间→年龄→性别→主诉→现病史→既往史→影像字段（按定义顺序）
2. 分隔符：`{字段名} {值}。`
3. 换行：每个字段结束后换行
4. 编码：UTF-8，无BOM

#### 3.3.2 写入文件（Write File）
**文件命名规范**：`patient_{patient_id}_input.txt`
**写入策略**：
1. 原子写入：先写入临时文件，成功后重命名
2. 备份原文件（如果存在）
3. 设置文件权限为只读（可选）

#### 3.3.3 内容验证（Verify Content）
**验证项**：
1. 文件可读取性
2. 敏感字段不存在性
3. 必需字段存在性
4. 文件哈希值与审计记录一致

#### 3.3.4 生成回执（Create Receipt）
**回执内容**：
- 处理ID和时间戳
- 输入文件哈希
- 输出文件哈希
- 验证结果签名

## 4. 验证流水线（Verification Pipeline）

### 4.1 四级验证体系

```
┌─────────────────────────────────────────────────────────────┐
│                    Verification Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Level 1: Pre-processing Verification                        │
│  ├── 源文件完整性检查（MD5校验）                              │
│  ├── Schema合规性验证                                        │
│  └── 访问权限验证                                            │
│                          │                                   │
│                          ▼                                   │
│  Level 2: Processing Verification                            │
│  ├── 白名单字段过滤验证                                      │
│  ├── 黑名单字段移除验证                                      │
│  └── 内容泄漏检测                                            │
│                          │                                   │
│                          ▼                                   │
│  Level 3: Post-processing Verification                       │
│  ├── 输出文件格式验证                                        │
│  ├── 内容不可变性验证（与原数据比对）                          │
│  └── 敏感信息二次扫描                                        │
│                          │                                   │
│                          ▼                                   │
│  Level 4: Integration Verification                           │
│  ├── Agent可读性测试                                         │
│  └── Baseline一致性验证                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 验证点详细定义

#### 4.2.1 Level 1: 预处理验证
| 验证点 | 验证方法 | 通过标准 | 失败处理 |
|-------|---------|---------|---------|
| 源文件存在性 | 文件系统检查 | 文件存在且可读 | 报错终止 |
| 源文件完整性 | MD5哈希比对（如有历史记录） | 哈希匹配 | 警告继续 |
| Schema合规性 | 列名白名单检查 | 所有必需列存在 | 报错终止 |
| 访问权限 | 权限位检查 | 源文件只读，输出目录可写 | 报错终止 |

#### 4.2.2 Level 2: 处理中验证
| 验证点 | 验证方法 | 通过标准 | 失败处理 |
|-------|---------|---------|---------|
| 白名单过滤 | 字段名匹配检查 | 仅白名单字段进入处理 | 报错终止 |
| 黑名单移除 | 黑名单字段存在性检查 | 黑名单字段值为空 | 强制移除并警告 |
| 内容泄漏 | 关键词匹配+正则扫描 | 无高危关键词 | 标记警告 |

#### 4.2.3 Level 3: 后处理验证
| 验证点 | 验证方法 | 通过标准 | 失败处理 |
|-------|---------|---------|---------|
| 文件编码 | 编码检测 | UTF-8 | 报错终止 |
| 格式规范 | 模板匹配 | 符合输出模板 | 报错终止 |
| 敏感字段残留 | 全文搜索 | 无黑名单字段名 | 报错终止 |
| 内容一致性 | 原文比对 | 白名单字段值与源数据完全一致 | 报错终止 |

#### 4.2.4 Level 4: 集成验证
| 验证点 | 验证方法 | 通过标准 | 失败处理 |
|-------|---------|---------|---------|
| Agent可读性 | 模拟读取测试 | BM Agent可正常解析 | 警告 |
| Baseline一致性 | 与Baseline输入比对 | 字段集合一致 | 警告 |

### 4.3 验证报告格式

```json
{
  "verification_id": "uuid",
  "timestamp": "2026-04-02T10:30:00Z",
  "patient_id": "640880",
  "levels": {
    "L1_preprocessing": {
      "status": "PASSED",
      "checks": [
        {"check": "file_exists", "status": "PASSED"},
        {"check": "schema_valid", "status": "PASSED"}
      ]
    },
    "L2_processing": {
      "status": "PASSED",
      "checks": [
        {"check": "whitelist_filter", "status": "PASSED"},
        {"check": "blacklist_removal", "status": "PASSED", "removed": ["入院诊断", "诊疗经过"]},
        {"check": "content_leakage", "status": "WARNING", "warnings": ["现病史包含'术后化疗'"]}
      ]
    },
    "L3_postprocessing": {
      "status": "PASSED",
      "checks": [
        {"check": "encoding_utf8", "status": "PASSED"},
        {"check": "format_compliance", "status": "PASSED"},
        {"check": "no_sensitive_fields", "status": "PASSED"},
        {"check": "content_immutability", "status": "PASSED"}
      ]
    },
    "L4_integration": {
      "status": "PASSED"
    }
  },
  "overall_status": "PASSED_WITH_WARNINGS"
}
```

### 4.4 批量处理报告格式

```json
{
  "processor_version": "2.1.0",
  "timestamp": "2026-04-03T10:20:29",
  "source_file": "patients_folder/46个病例_诊疗经过.xlsx",
  "source_hash": "3a50ad77842c89b9...",
  "source_statistics": {
    "total_cases_in_source": 46,
    "unique_patients": 34,
    "total_visits": 46,
    "duplicate_patient_ids": 9,
    "duplicate_details": {
      "466104": {
        "visit_count": 4,
        "cases": ["Case12", "Case13", "Case35", "Case36"]
      }
    }
  },
  "processing_summary": {
    "total": 46,
    "success": 0,
    "warning": 46,
    "failed": 0
  },
  "details": [
    {
      "patient_id": "640880",
      "status": "warning",
      "output_path": "workspace/sandbox/patient_640880_input.txt",
      "warnings": ["[待LLM检查] 现病史需要语义级审查"],
      "error": ""
    }
  ]
}
```

**统计字段说明**：
| 字段 | 说明 |
|-----|------|
| `total_cases_in_source` | 源Excel文件中的Case总数 |
| `unique_patients` | 唯一住院号数量 |
| `total_visits` | 总就诊次数（含重复） |
| `duplicate_patient_ids` | 重复住院号的数量 |
| `duplicate_details` | 重复住院号的详细映射关系 |

## 5. 使用接口

### 5.1 命令行接口（CLI）

```bash
# 完整处理流程
python -m skills.patient_data_processor process \
    --source patients_folder/46个病例_诊疗经过.xlsx \
    --output workspace/sandbox/ \
    --patient-id 640880

# 批量处理
python -m skills.patient_data_processor batch \
    --source patients_folder/46个病例_诊疗经过.xlsx \
    --output workspace/sandbox/

# 仅验证（不生成）
python -m skills.patient_data_processor verify \
    --file workspace/sandbox/patient_640880_input.txt

# 验证源数据
python -m skills.patient_data_processor inspect \
    --source patients_folder/46个病例_诊疗经过.xlsx
```

### 5.2 Python API

```python
from skills.patient_data_processor import PatientDataProcessor

# 初始化处理器
processor = PatientDataProcessor(
    source_path="patients_folder/46个病例_诊疗经过.xlsx",
    output_dir="workspace/sandbox/",
    backup_dir="workspace/sandbox/input_backups/"
)

# 处理单个患者
result = processor.process(
    patient_id="640880",
    verification=True  # 启用验证流水线
)

# 访问处理结果
print(result.status)           # "SUCCESS" | "FAILED" | "WARNING"
print(result.output_path)      # 输出文件路径
print(result.verification_report)  # 验证报告
print(result.audit_log)        # 审计日志

# 批量处理
batch_results = processor.batch_process(
    patient_ids=["640880", "708387"],  # None表示全部
    verification=True
)

# 生成处理报告
report = processor.generate_report(batch_results)
```

## 6. 错误处理与恢复

### 6.1 错误分类

| 错误级别 | 错误类型 | 示例 | 处理策略 |
|---------|---------|------|---------|
| CRITICAL | 系统级错误 | 源文件不可读 | 终止处理 |
| ERROR | 数据级错误 | Schema验证失败 | 跳过该患者，记录错误 |
| WARNING | 内容警告 | 现病史含治疗信息 | 标记警告，继续处理 |
| INFO | 信息提示 | 可选字段为空 | 记录日志，正常处理 |

### 6.2 恢复机制

1. **原子写入**：输出文件先写入临时文件，验证通过后重命名
2. **自动备份**：处理前自动备份原文件
3. **断点续传**：批量处理时记录进度，支持从中断处恢复

## 7. 论文引用规范

### 7.1 方法描述（Method Section）

```markdown
### Patient Data Processing Pipeline

To ensure rigorous evaluation of the BM Agent, we implemented a standardized 
patient data processing pipeline that strictly segregates input features (X) 
from ground truth labels (Y).

**Data Classification Framework:**
- Input Features (X): Objective clinical data collected at admission, including 
  demographics (age, gender), symptoms (chief complaint), history (present illness, 
  past medical history), and imaging findings (brain MRI, chest CT, etc.)
- Ground Truth Labels (Y): Diagnostic conclusions and treatment decisions derived 
  from complete medical records, including admission diagnosis, discharge diagnosis, 
  and treatment course.

**Processing Workflow:**
1. Load source data (Excel long-format) in read-only mode
2. Validate schema compliance (required columns: id, Visit, Feature, Value)
3. Filter features using whitelist approach (16 allowed fields)
4. Remove blacklisted fields (admission_diagnosis, discharge_diagnosis, treatment_course)
5. Detect content leakage using keyword matching and regex patterns
6. Format output as plain text with strict immutability constraints
7. Execute 4-level verification pipeline
8. Generate audit trail with cryptographic hashing

**Immutability Constraint:**
The processor guarantees that feature values are extracted from source data 
without any character-level modification, ensuring reproducibility and 
preventing information distortion.
```

### 7.2 验证声明（Validation Statement）

```markdown
All patient input files were generated using Patient Data Processor v2.0 
following a 4-level verification protocol. No ground truth labels were 
included in the input files, as verified by automated sensitive field 
detection and manual spot-checking. The processing audit logs are available 
in the supplementary materials.
```

## 8. 附录

### 8.1 变更日志

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| 2.1.0 | 2026-04-03 | **重大改进**：支持同一患者多次就诊记录处理，添加详细统计报告 |
| 2.0.0 | 2026-04-02 | 重构为论文级处理器，增加4级验证流水线 |
| 1.0.0 | 2026-04-02 | 初始版本，基础数据清理功能 |

**v2.1.0 详细变更：**
1. **支持多次就诊记录**：同一住院号多次就诊时，自动添加 `_V2`, `_V3` 等后缀区分
2. **详细统计报告**：添加源数据统计，包括：
   - 源文件Case总数
   - 唯一住院号数
   - 总就诊次数
   - 重复住院号数及详情
3. **重复住院号检测**：自动识别并报告哪些住院号对应多次就诊
4. **统计报告持久化**：详细统计信息保存至JSON报告文件

### 8.2 依赖清单

```
pandas >= 2.0.0
openpyxl >= 3.1.0
```

### 8.3 参考标准

- HL7 FHIR R4: Clinical data exchange standards
- DICOM: Medical imaging data standards
- FAIR Principles: Data management guidelines
