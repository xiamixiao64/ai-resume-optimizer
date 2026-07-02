# ATS Engine 使用指南

## 概述

ATS Engine 是一个本地简历 ATS 兼容性评分系统，提供准确、可解释的评分和改进建议。

## 功能

- **格式检查**：验证简历格式是否兼容 ATS 系统
- **关键词匹配**：分析与职位描述的关键词匹配度
- **经验质量**：评估工作经历描述的质量
- **ATS 识别**：识别目标公司使用的 ATS 系统
- **改进建议**：提供具体、可操作的优化建议

## 使用方法

```python
from ats_engine import ATSEngine

engine = ATSEngine()
result = engine.analyze(resume_text, jd_text)

print(f"ATS 评分: {result['ats_score']}/100")
print(f"改进建议: {result['improvements']}")
```

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 格式兼容性 | 20% | 文件格式、章节标题、联系方式 |
| 关键词匹配 | 35% | 与 JD 的关键词匹配度 |
| 经验质量 | 25% | 量化数据、动词强度、长度 |
| 教育背景 | 10% | 学位、学校、年份 |
| 联系方式 | 10% | 邮箱、电话、LinkedIn |

## 支持的 ATS 系统

- Workday
- Lever
- Greenhouse
- iCIMS
- Taleo
- SmartRecruiters

## 返回格式

```json
{
  "ats_score": 85,
  "breakdown": {
    "formatting": {"score": 90, "issues": []},
    "keywords": {"score": 80, "matched": ["Python", "React"], "missing": ["AWS"]},
    "experience": {"score": 85, "issues": []},
    "education": {"score": 100, "issues": []},
    "contact": {"score": 75, "issues": ["建议添加所在城市"]}
  },
  "improvements": ["添加缺失的关键词: AWS", "建议添加所在城市"],
  "ats_type": {"type": "workday", "confidence": 0.85, "tips": ["Workday 系统重视关键词精确匹配"]}
}
```

## 运行测试

```bash
pytest tests/test_ats_engine.py -v
```
