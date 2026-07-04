# ats_engine.py
import re
from difflib import SequenceMatcher
from services.constants import (
    EMAIL_PATTERN, PHONE_PATTERN, STANDARD_HEADERS, TECH_KEYWORDS,
    SOFT_KEYWORDS, STRONG_VERBS, WEAK_VERBS, DEGREE_KEYWORDS,
    SCHOOL_KEYWORDS, LOCATIONS, SEMANTIC_GROUPS, XYZ_PATTERNS,
    PORTFOLIO_PATTERNS, PORTFOLIO_KEYWORDS, SYNONYM_GROUPS
)

class ATSEngine:
    """ATS 评分引擎"""

    def __init__(self):
        self.ats_patterns = {
            "workday": {
                "patterns": ["workday", "myworkdayjobs", "wd5.myworkday", "wday.com"],
                "tips": [
                    "Workday 系统重视关键词精确匹配",
                    "确保技能名称与 JD 完全一致",
                    "使用标准的章节标题"
                ]
            },
            "lever": {
                "patterns": ["lever.co", "jobs.lever", "lever.co/"],
                "tips": [
                    "Lever 系统重视格式简洁",
                    "避免使用表格和复杂格式",
                    "保持简历简洁明了"
                ]
            },
            "greenhouse": {
                "patterns": ["greenhouse.io", "boards.greenhouse", "greenhouse.com"],
                "tips": [
                    "Greenhouse 重视技能标签",
                    "在技能列表中明确列出技术栈",
                    "使用标准的职位名称"
                ]
            },
            "icims": {
                "patterns": ["icims.com", "jobs.icims", "icims.com/"],
                "tips": [
                    "iCIMS 系统解析能力较强",
                    "保持标准格式即可",
                    "确保关键词自然分布"
                ]
            },
            "taleo": {
                "patterns": ["taleo", "oracle.com/taleo", "talent.oracle"],
                "tips": [
                    "Taleo 系统较为严格",
                    "避免使用特殊字符",
                    "使用标准的章节标题"
                ]
            },
            "smartrecruiters": {
                "patterns": ["smartrecruiters", "smartrecruiters.com"],
                "tips": [
                    "SmartRecruiters 重视关键词匹配",
                    "确保技能与 JD 匹配",
                    "保持格式简洁"
                ]
            },
            "bamboohr": {
                "patterns": ["bamboohr.com", "bamboo hr", "bamboohr"],
                "tips": [
                    "BambooHR 系统界面友好",
                    "保持格式简洁清晰",
                    "确保联系方式完整"
                ]
            },
            "successfactors": {
                "patterns": ["successfactors", "sap.com/careers", "sapsf"],
                "tips": [
                    "SuccessFactors 重视结构化数据",
                    "使用标准的职位名称和技能术语",
                    "确保日期格式一致"
                ]
            },
            "jobvite": {
                "patterns": ["jobvite.com", "jobvite"],
                "tips": [
                    "JobVite 重视社交招聘",
                    "确保 LinkedIn 链接可访问",
                    "使用行业标准关键词"
                ]
            },
            "applicantstack": {
                "patterns": ["applicantstack.com", "applicantstack"],
                "tips": [
                    "ApplicantStack 重视关键词匹配",
                    "确保技能与职位要求一致",
                    "使用标准格式"
                ]
            },
            "bullhorn": {
                "patterns": ["bullhorn.com", "bullhorn"],
                "tips": [
                    "Bullhorn 用于招聘机构",
                    "确保简历格式标准化",
                    "关键词要与职位描述匹配"
                ]
            },
            "clearcompany": {
                "patterns": ["clearcompany.com", "clearcompany"],
                "tips": [
                    "ClearCompany 重视人才匹配",
                    "突出与职位相关的成就",
                    "使用量化数据"
                ]
            }
        }
        self.weights = {
            "formatting": 20,
            "keywords": 35,
            "experience": 25,
            "education": 10,
            "contact": 10
        }
    
    def analyze(self, resume_text: str, jd_text: str) -> dict:
        """Analyze resume for ATS compatibility.

        Args:
            resume_text: Resume content text.
            jd_text: Job description text.

        Returns:
            Dictionary with ATS score, breakdown, improvements, and ATS type.
        """
        # 执行所有检查
        formatting = self.check_formatting(resume_text)
        keywords = self.check_keywords(resume_text, jd_text)
        semantic = self.check_semantic_match(resume_text, jd_text)
        experience = self.check_experience(resume_text)
        education = self.check_education(resume_text)
        contact = self.check_contact(resume_text)
        portfolio = self.check_portfolio(resume_text)
        personal_info = self.check_personal_info(resume_text)
        ats_type = self.identify_ats(jd_text)

        # 合并关键词和语义匹配分数
        combined_keyword_score = int((keywords["score"] * 0.6 + semantic["score"] * 0.4))

        # 计算加权总分
        total_score = (
            formatting["score"] * self.weights["formatting"] / 100 +
            combined_keyword_score * self.weights["keywords"] / 100 +
            experience["score"] * self.weights["experience"] / 100 +
            education["score"] * self.weights["education"] / 100 +
            contact["score"] * self.weights["contact"] / 100 +
            portfolio["score"] * 5  # 作品集加分（最多5分）
        )

        # 生成改进建议
        improvements = self._generate_improvements(
            formatting, keywords, semantic, experience, education, contact, portfolio, personal_info, ats_type
        )

        return {
            "ats_score": min(100, round(total_score)),
            "breakdown": {
                "formatting": formatting,
                "keywords": keywords,
                "semantic_match": semantic,
                "experience": experience,
                "education": education,
                "contact": contact,
                "portfolio": portfolio,
                "personal_info": personal_info
            },
            "improvements": improvements,
            "ats_type": ats_type
        }

    def _generate_improvements(self, formatting: dict, keywords: dict, semantic: dict,
                               experience: dict, education: dict, contact: dict,
                               portfolio: dict, personal_info: dict, ats_type: dict) -> list:
        """Generate improvement suggestions based on analysis results.

        Args:
            formatting: Formatting check results.
            keywords: Keyword matching results.
            semantic: Semantic matching results.
            experience: Experience check results.
            education: Education check results.
            contact: Contact check results.
            portfolio: Portfolio check results.
            ats_type: ATS type detection results.

        Returns:
            List of improvement suggestions.
        """
        improvements = []

        # 按优先级添加建议
        if keywords["missing"]:
            improvements.append(f"添加缺失的关键词: {', '.join(keywords['missing'][:5])}")

        if semantic.get("related_missing"):
            groups = list(semantic["related_missing"].keys())[:3]
            improvements.append(f"考虑补充相关技能组: {', '.join(groups)}")

        if formatting["issues"]:
            improvements.extend(formatting["issues"][:2])

        if experience["issues"]:
            improvements.extend(experience["issues"][:2])

        if education["issues"]:
            improvements.extend(education["issues"][:1])

        if contact["issues"]:
            improvements.extend(contact["issues"][:1])

        if portfolio["issues"]:
            improvements.extend(portfolio["issues"][:1])

        # 公平性建议
        if personal_info.get("issues"):
            improvements.extend(personal_info["issues"])

        # 添加 ATS 特定建议
        if ats_type["type"] != "unknown" and ats_type["tips"]:
            improvements.append(f"针对 {ats_type['type']} 系统: {ats_type['tips'][0]}")

        return improvements[:8]  # 最多返回 8 条建议

    def check_formatting(self, resume_text: str) -> dict:
        """Check resume formatting compatibility with 30+ checks.

        Args:
            resume_text: Resume content text.

        Returns:
            Dictionary with score and issues list.
        """
        score = 100
        issues = []
        checks_passed = 0
        total_checks = 30

        # 1. Section headers check
        found_headers = [h for h in STANDARD_HEADERS if h in resume_text.lower()]
        if len(found_headers) >= 2:
            checks_passed += 1
        else:
            score -= 15
            issues.append("缺少标准章节标题（Experience, Education, Skills）")

        # 2. Email format
        if re.search(EMAIL_PATTERN, resume_text):
            checks_passed += 1
        else:
            score -= 10
            issues.append("缺少有效的电子邮件地址")

        # 3. Phone format
        if re.search(PHONE_PATTERN, resume_text):
            checks_passed += 1
        else:
            score -= 10
            issues.append("缺少有效的电话号码")

        # 4. No tabs
        if '\t' not in resume_text:
            checks_passed += 1
        else:
            score -= 5
            issues.append("使用了制表符，可能影响 ATS 解析")

        # 5. Word count
        words = resume_text.split()
        if 20 <= len(words) <= 1000:
            checks_passed += 1
        elif len(words) < 20:
            score -= 10
            issues.append("简历内容过短，建议至少 20 词")
        else:
            score -= 5
            issues.append("简历内容过长，建议控制在 1000 词以内")

        # 6. No special characters
        special_chars = re.findall(r'[!@#$%^&*()_+={}\[\]|\\:";<>?`~]', resume_text)
        if len(special_chars) < 5:
            checks_passed += 1
        else:
            score -= 3
            issues.append("包含过多特殊字符，可能影响 ATS 解析")

        # 7. Standard fonts check (detect non-standard)
        non_standard_fonts = ['comic sans', 'papyrus', 'wingdings']
        has_non_standard = any(f in resume_text.lower() for f in non_standard_fonts)
        if not has_non_standard:
            checks_passed += 1
        else:
            score -= 5
            issues.append("使用了非标准字体，建议使用 Arial、Calibri 或 Times New Roman")

        # 8. Single column check (detect multi-column indicators)
        multi_column_indicators = ['│', '┃', '║', 'column', 'sidebar']
        has_multi_column = any(ind in resume_text for ind in multi_column_indicators)
        if not has_multi_column:
            checks_passed += 1
        else:
            score -= 8
            issues.append("检测到多列布局，ATS 可能无法正确解析")

        # 9. No tables
        table_indicators = ['│', '┃', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
        has_tables = any(ind in resume_text for ind in table_indicators)
        if not has_tables:
            checks_passed += 1
        else:
            score -= 8
            issues.append("检测到表格格式，ATS 无法解析表格内容")

        # 10. No images/graphics indicators
        image_indicators = ['![', '<img', 'image:', 'figure:']
        has_images = any(ind in resume_text.lower() for ind in image_indicators)
        if not has_images:
            checks_passed += 1
        else:
            score -= 5
            issues.append("检测到图片引用，ATS 无法解析图片内容")

        # 11. Contact info not in header/footer
        lines = resume_text.split('\n')
        first_line = lines[0].lower() if lines else ''
        last_line = lines[-1].lower() if lines else ''
        contact_in_body = any(re.search(EMAIL_PATTERN, line) for line in lines[1:-1])
        if contact_in_body or not first_line.startswith('[') and not last_line.startswith('['):
            checks_passed += 1
        else:
            score -= 5
            issues.append("联系方式可能在页眉/页脚中，ATS 无法读取")

        # 12. Reverse chronological order
        years = re.findall(r'20\d{2}', resume_text)
        if len(years) >= 2:
            if int(years[0]) >= int(years[-1]):
                checks_passed += 1
            else:
                score -= 3
                issues.append("建议按时间倒序排列工作经历")
        else:
            checks_passed += 1

        # 13. Spell check (basic)
        common_misspelling = ['recieve', 'seperate', 'occured', 'definately', 'accomodate']
        has_misspelling = any(m in resume_text.lower() for m in common_misspelling)
        if not has_misspelling:
            checks_passed += 1
        else:
            score -= 3
            issues.append("检测到拼写错误，请检查拼写")

        # 14. No abbreviations without full terms
        abbreviations = ['AI', 'ML', 'UX', 'UI', 'SEO', 'API']
        for abbr in abbreviations:
            if abbr in resume_text and f'({abbr})' not in resume_text:
                score -= 1
                issues.append(f"建议先写出全称再使用缩写 {abbr}")
                break
        else:
            checks_passed += 1

        # 15. Date format consistency
        date_formats = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|\w+ \d{4}', resume_text)
        if len(date_formats) > 0:
            checks_passed += 1
        else:
            score -= 2
            issues.append("建议使用一致的日期格式")

        # 16. Professional summary present
        summary_indicators = ['summary', 'objective', 'profile', 'about']
        has_summary = any(ind in resume_text.lower() for ind in summary_indicators)
        if has_summary:
            checks_passed += 1
        else:
            score -= 5
            issues.append("建议添加专业摘要（Professional Summary）")

        # 17. Skills section present
        has_skills = 'skills' in resume_text.lower()
        if has_skills:
            checks_passed += 1
        else:
            score -= 5
            issues.append("建议添加技能列表（Skills）")

        # 18. Education section present
        has_education = 'education' in resume_text.lower()
        if has_education:
            checks_passed += 1
        else:
            score -= 3
            issues.append("建议添加教育背景（Education）")

        # 19. Experience section present
        has_experience = any(ind in resume_text.lower() for ind in ['experience', 'work history', 'employment'])
        if has_experience:
            checks_passed += 1
        else:
            score -= 5
            issues.append("建议添加工作经历（Experience）")

        # 20. No personal information beyond contact
        personal_info = ['birthday', 'date of birth', 'age', 'marital status', 'religion', 'gender']
        has_personal = any(info in resume_text.lower() for info in personal_info)
        if not has_personal:
            checks_passed += 1
        else:
            score -= 5
            issues.append("包含个人信息（生日/年龄/婚姻状况），ATS 可能会过滤")

        # 21. No references section
        has_references = 'references' in resume_text.lower()
        if not has_references:
            checks_passed += 1
        else:
            score -= 2
            issues.append("不需要包含推荐人信息，节省空间")

        # 22. Bullet points format
        bullet_lines = [l for l in lines if l.strip().startswith(('- ', '• ', '* '))]
        if len(bullet_lines) > 0:
            checks_passed += 1
        else:
            score -= 3
            issues.append("建议使用项目符号（bullet points）格式化内容")

        # 23. No email in header/footer
        if not first_line.endswith('.com') and not last_line.endswith('.com'):
            checks_passed += 1
        else:
            score -= 3
            issues.append("邮箱地址应放在正文区域，而非页眉/页脚")

        # 24. LinkedIn URL format
        if 'linkedin.com' in resume_text.lower():
            checks_passed += 1
        else:
            score -= 2
            issues.append("建议添加 LinkedIn 个人主页链接")

        # 25. Consistent date format
        date_patterns = re.findall(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', resume_text)
        if len(date_patterns) > 0 or len(date_formats) > 0:
            checks_passed += 1
        else:
            score -= 2
            issues.append("建议使用一致的日期格式（如：Jan 2024）")

        # 26. No personal pronouns
        pronouns = ['i ', 'i\'m', 'my ', 'me ']
        has_pronouns = any(p in resume_text.lower().split() for p in pronouns)
        if not has_pronouns:
            checks_passed += 1
        else:
            score -= 3
            issues.append("建议避免使用第一人称代词（I, my, me）")

        # 27. Action verbs at start
        strong_verbs = ['led', 'built', 'managed', 'developed', 'implemented', 'created', 'improved']
        lines_with_verbs = [l for l in lines if any(l.lower().startswith(v) for v in strong_verbs)]
        if len(lines_with_verbs) >= 3:
            checks_passed += 1
        else:
            score -= 3
            issues.append("建议以行动动词开头（如：Led, Built, Improved）")

        # 28. Quantified achievements
        quantified = re.findall(r'\d+%|\$[\d,]+|\d+ (users|customers|projects|team|employees)', resume_text)
        if len(quantified) >= 2:
            checks_passed += 1
        else:
            score -= 5
            issues.append("建议添加量化数据（百分比、金额、用户数）")

        # 29. No colors in text
        color_indicators = ['color:', 'rgb(', '#', 'font color']
        has_colors = any(ind in resume_text.lower() for ind in color_indicators)
        if not has_colors:
            checks_passed += 1
        else:
            score -= 3
            issues.append("避免使用彩色文字，ATS 可能无法正确读取")

        # 30. Page length appropriate
        line_count = len(lines)
        if 20 <= line_count <= 100:
            checks_passed += 1
        elif line_count < 20:
            score -= 3
            issues.append("简历内容较少，建议补充更多细节")
        else:
            score -= 2
            issues.append("简历较长，建议精简到 1-2 页")

        # Calculate final score based on checks passed
        check_score = (checks_passed / total_checks) * 100
        final_score = min(score, check_score)

        return {"score": max(0, int(final_score)), "issues": issues, "checks_passed": checks_passed, "total_checks": total_checks}

    def check_keywords(self, resume_text: str, jd_text: str) -> dict:
        """Check keyword matching between resume and job description.

        Args:
            resume_text: Resume content text.
            jd_text: Job description text.

        Returns:
            Dictionary with score, matched keywords, and missing keywords.
        """
        jd_keywords = self._extract_keywords(jd_text)
        resume_lower = resume_text.lower()

        matched = []
        missing = []
        synonym_matches = 0
        weighted_score = 0
        total_weight = 0

        for kw_info in jd_keywords:
            keyword = kw_info["keyword"]
            importance = kw_info["importance"]
            total_weight += importance

            if keyword.lower() in resume_lower:
                matched.append(keyword)
                weighted_score += importance
            else:
                # Check for synonyms
                found_synonym = False
                for main_word, synonyms in SYNONYM_GROUPS.items():
                    if keyword.lower() == main_word or keyword.lower() in synonyms:
                        all_variants = [main_word] + synonyms
                        for variant in all_variants:
                            if variant in resume_lower:
                                synonym_matches += 1
                                weighted_score += importance * 0.5  # Synonyms count half
                                found_synonym = True
                                break
                if not found_synonym:
                    missing.append(keyword)

        # Also check resume synonyms against JD
        for main_word, synonyms in SYNONYM_GROUPS.items():
            all_variants = [main_word] + synonyms
            jd_has = any(v in jd_text.lower() for v in all_variants)
            if jd_has:
                resume_has = any(v in resume_lower for v in all_variants)
                if resume_has and main_word not in matched:
                    already_counted = any(v in matched for v in all_variants)
                    if not already_counted:
                        synonym_matches += 1

        if total_weight == 0:
            score = 70
            weighted_match_rate = 0.7
        else:
            weighted_match_rate = weighted_score / total_weight
            synonym_bonus = min(0.2, (synonym_matches / max(1, len(jd_keywords))) * 0.2)
            score = min(100, int((weighted_match_rate + synonym_bonus) * 100))

        bonus = self._calculate_position_bonus(matched, resume_text)
        score = min(100, score + bonus)

        return {
            "score": score,
            "matched": matched,
            "missing": missing,
            "synonym_matches": synonym_matches,
            "weighted_score": round(weighted_match_rate * 100, 1)
        }

    def _extract_keywords(self, text: str) -> list:
        """Extract keywords from text with importance weighting.

        Args:
            text: Text to extract keywords from.

        Returns:
            List of found keywords with importance weights.
        """
        all_keywords = TECH_KEYWORDS + SOFT_KEYWORDS
        text_lower = text.lower()
        text_words = text.lower().split()

        found = []
        for kw in all_keywords:
            if kw in text_lower:
                # Calculate importance based on frequency
                freq = text_lower.count(kw)
                importance = min(1.0, 0.5 + (freq * 0.1))
                found.append({"keyword": kw, "importance": importance})

        # Extract capitalized words as potential keywords
        words = text.split()
        for word in words:
            if word.isupper() and len(word) > 2 and word.lower() not in [f["keyword"] for f in found]:
                found.append({"keyword": word, "importance": 0.6})

        return found

    def _calculate_position_bonus(self, matched_keywords, resume_text):
        """根据关键词位置计算加分"""
        bonus = 0
        resume_lower = resume_text.lower()

        if "skills" in resume_lower:
            skills_section = resume_lower.split("skills")[1][:500]
            for kw in matched_keywords:
                if kw.lower() in skills_section:
                    bonus += 1

        return min(10, bonus)

    def check_semantic_match(self, resume_text, jd_text):
        """语义匹配检查 - 使用BERT语义匹配和技能组匹配"""
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        # 尝试使用BERT语义匹配
        bert_score = 50  # 默认分数
        bert_analysis = ""
        try:
            from services.bert_matcher import calculate_semantic_similarity
            bert_result = calculate_semantic_similarity(resume_text, jd_text)
            bert_score = bert_result.get("score", 50)
            bert_analysis = bert_result.get("analysis", "")
        except Exception as e:
            # 回退到传统方法
            logger.warning(f"BERT matching failed, falling back to SequenceMatcher: {e}")
            similarity = SequenceMatcher(None, resume_lower, jd_lower).ratio()
            bert_score = min(100, int(similarity * 100 * 2))

        # 技能组匹配
        matched_groups = []
        related_missing = {}

        for group_name, keywords in SEMANTIC_GROUPS.items():
            jd_has = [kw for kw in keywords if kw in jd_lower]
            resume_has = [kw for kw in keywords if kw in resume_lower]

            if jd_has:
                overlap = len(set(jd_has) & set(resume_has))
                coverage = overlap / len(jd_has) if jd_has else 0

                if coverage > 0.5:
                    matched_groups.append(group_name)
                elif coverage > 0:
                    matched_groups.append(f"{group_name} (部分)")
                else:
                    related_missing[group_name] = jd_has

        # 技能组分数
        group_score = min(100, int(len(matched_groups) / max(1, len(related_missing) + len(matched_groups)) * 100))

        # 综合分数 (BERT 70% + 技能组 30%)
        semantic_score = min(100, int(bert_score * 0.7 + group_score * 0.3))

        return {
            "score": semantic_score,
            "text_similarity": round(bert_score, 1),
            "matched_groups": matched_groups,
            "related_missing": related_missing,
            "bert_analysis": bert_analysis
        }

    def check_experience(self, resume_text: str) -> dict:
        """Check work experience quality.

        Args:
            resume_text: Resume content text.

        Returns:
            Dictionary with score, issues list, and X-Y-Z format count.
        """
        score = 100
        issues = []

        bullets = self._extract_bullets(resume_text)

        if len(bullets) == 0:
            return {"score": 30, "issues": ["未找到工作经历描述"]}

        # 检查 bullet point 数量
        if len(bullets) < 3:
            score -= 15
            issues.append("工作经历描述过少，建议每个职位 3-5 个 bullet points")

        # 检查量化数据（X-Y-Z格式）
        quantified = 0
        xyz_formatted = 0
        for bullet in bullets:
            if re.search(r'\d+%|\$[\d,]+|\d+ (users|customers|projects|team)', bullet, re.IGNORECASE):
                quantified += 1
            for pattern in XYZ_PATTERNS:
                if re.search(pattern, bullet, re.IGNORECASE):
                    xyz_formatted += 1
                    break

        if len(bullets) > 0:
            quantified_rate = quantified / len(bullets)
            if quantified_rate < 0.3:
                score -= 20
                issues.append("缺少量化数据，建议使用 X-Y-Z 格式：做了什么(X) + 怎么做(Y) + 结果(Z)")

            # X-Y-Z 格式加分
            if xyz_formatted / len(bullets) > 0.5:
                score = min(100, score + 5)  # 鼓励 X-Y-Z 格式

        # 检查动词强度
        strong_count = 0
        weak_count = 0
        for bullet in bullets:
            bullet_lower = bullet.lower()
            for verb in STRONG_VERBS:
                if bullet_lower.startswith(verb):
                    strong_count += 1
                    break
            for verb in WEAK_VERBS:
                if verb in bullet_lower:
                    weak_count += 1
                    break

        if weak_count > strong_count:
            score -= 15
            issues.append("使用了较弱的动词，建议使用更强的行动动词（Led, Built, Increased）")

        # 检查长度
        avg_length = sum(len(b.split()) for b in bullets) / len(bullets) if bullets else 0
        if avg_length < 6:
            score -= 10
            issues.append("Bullet points 过短，建议每个 10-20 词")
        elif avg_length > 30:
            score -= 5
            issues.append("Bullet points 过长，建议控制在 20 词以内")

        return {"score": max(0, score), "issues": issues, "xyz_count": xyz_formatted}

    def check_resume_quality(self, resume_text: str) -> dict:
        """Evaluate resume content quality and impact.

        Args:
            resume_text: Resume content text.

        Returns:
            Dictionary with quality score, strengths, and weaknesses.
        """
        score = 100
        strengths = []
        weaknesses = []
        bullets = self._extract_bullets(resume_text)
        words = resume_text.split()

        # 1. Content depth - word count
        if len(words) >= 300:
            strengths.append("Good content depth with sufficient detail")
        elif len(words) >= 150:
            score -= 5
            weaknesses.append("Content could be more detailed")
        else:
            score -= 15
            weaknesses.append("Resume is too brief - add more details")

        # 2. Quantified achievements
        quantified_count = 0
        for bullet in bullets:
            if re.search(r'\d+%|\$[\d,]+|\d+ (users|customers|projects|team)', bullet, re.IGNORECASE):
                quantified_count += 1

        if len(bullets) > 0:
            quantified_rate = quantified_count / len(bullets)
            if quantified_rate >= 0.5:
                strengths.append(f"Strong quantified achievements ({quantified_count}/{len(bullets)} bullets)")
            elif quantified_rate >= 0.3:
                score -= 5
                weaknesses.append(f"Some bullets lack quantification ({quantified_count}/{len(bullets)})")
            else:
                score -= 15
                weaknesses.append(f"Most bullets lack quantified achievements ({quantified_count}/{len(bullets)})")

        # 3. Action verbs
        strong_verbs_used = 0
        for bullet in bullets:
            bullet_lower = bullet.lower()
            if any(bullet_lower.startswith(v) for v in STRONG_VERBS):
                strong_verbs_used += 1

        if len(bullets) > 0:
            verb_rate = strong_verbs_used / len(bullets)
            if verb_rate >= 0.7:
                strengths.append("Strong action verbs throughout")
            elif verb_rate >= 0.4:
                score -= 5
                weaknesses.append("Some bullet points use weak verbs")
            else:
                score -= 10
                weaknesses.append("Most bullet points use weak verbs")

        # 4. X-Y-Z format
        xyz_count = 0
        for bullet in bullets:
            for pattern in XYZ_PATTERNS:
                if re.search(pattern, bullet, re.IGNORECASE):
                    xyz_count += 1
                    break

        if len(bullets) > 0:
            xyz_rate = xyz_count / len(bullets)
            if xyz_rate >= 0.5:
                strengths.append("Good use of X-Y-Z format (What + How + Result)")
            elif xyz_rate >= 0.3:
                score -= 5
                weaknesses.append("Some bullets could follow X-Y-Z format better")
            else:
                score -= 10
                weaknesses.append("Bullets lack structured impact format")

        # 5. Skills section
        if 'skills' in resume_text.lower():
            skills_section = resume_text.lower().split('skills')[1][:500]
            skill_count = len([w for w in skills_section.split(',') if w.strip()])
            if skill_count >= 5:
                strengths.append(f"Good skills section ({skill_count} skills listed)")
            elif skill_count >= 3:
                score -= 3
                weaknesses.append("Skills section could list more technologies")
            else:
                score -= 8
                weaknesses.append("Skills section is too brief")
        else:
            score -= 10
            weaknesses.append("Missing skills section")

        # 6. Professional summary
        summary_indicators = ['summary', 'objective', 'profile', 'about']
        has_summary = any(ind in resume_text.lower() for ind in summary_indicators)
        if has_summary:
            strengths.append("Has professional summary")
        else:
            score -= 5
            weaknesses.append("Missing professional summary")

        # 7. Contact completeness
        has_email = bool(re.search(EMAIL_PATTERN, resume_text))
        has_phone = bool(re.search(PHONE_PATTERN, resume_text))
        has_linkedin = 'linkedin' in resume_text.lower()

        contact_score = sum([has_email, has_phone, has_linkedin])
        if contact_score == 3:
            strengths.append("Complete contact information")
        elif contact_score == 2:
            score -= 3
            weaknesses.append("Missing one contact method")
        else:
            score -= 8
            weaknesses.append("Incomplete contact information")

        # 8. Bullet point quality
        if len(bullets) >= 5:
            strengths.append(f"Good number of bullet points ({len(bullets)})")
        elif len(bullets) >= 3:
            score -= 5
            weaknesses.append(f"Could add more bullet points ({len(bullets)}/5+)")
        else:
            score -= 10
            weaknesses.append(f"Too few bullet points ({len(bullets)}/5+)")

        return {
            "score": max(0, min(100, score)),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "metrics": {
                "word_count": len(words),
                "bullet_count": len(bullets),
                "quantified_count": quantified_count,
                "strong_verbs_count": strong_verbs_used,
                "xyz_count": xyz_count
            }
        }

    def _extract_bullets(self, text: str) -> list:
        """Extract bullet points from resume text.

        Args:
            text: Resume content text.

        Returns:
            List of bullet point strings.
        """
        bullets = []
        lines = text.split('\n')
        in_experience = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测经验章节开始
            if 'experience' in line.lower() or 'work history' in line.lower():
                in_experience = True
                continue

            # 检测其他章节开始
            if line.isupper() and len(line) > 3:
                in_experience = False
                continue

            # 提取 bullet points
            if in_experience and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                bullet = line.lstrip('-•* ').strip()
                if len(bullet) > 10:
                    bullets.append(bullet)

        return bullets

    def check_education(self, resume_text: str) -> dict:
        """Check education background.

        Args:
            resume_text: Resume content text.

        Returns:
            Dictionary with score and issues list.
        """
        score = 100
        issues = []

        resume_lower = resume_text.lower()

        # 检查是否有教育章节
        if "education" not in resume_lower:
            return {"score": 50, "issues": ["缺少教育背景章节"]}

        # 检查学位
        has_degree = any(d in resume_lower for d in DEGREE_KEYWORDS)
        if not has_degree:
            score -= 30
            issues.append("未找到学位信息")

        # 检查学校
        if not any(school in resume_lower for school in SCHOOL_KEYWORDS):
            score -= 20
            issues.append("未找到学校名称")

        # 检查年份
        if not re.search(r'20\d{2}', resume_text):
            score -= 10
            issues.append("未找到毕业年份")

        return {"score": max(0, score), "issues": issues}

    def check_contact(self, resume_text):
        """检查联系方式"""
        score = 0
        issues = []

        # 电子邮件 (25分)
        if re.search(EMAIL_PATTERN, resume_text):
            score += 25
        else:
            issues.append("缺少有效的电子邮件地址")

        # 电话 (25分)
        if re.search(PHONE_PATTERN, resume_text):
            score += 25
        else:
            issues.append("缺少有效的电话号码")

        # LinkedIn (25分)
        if "linkedin" in resume_text.lower():
            score += 25
        else:
            issues.append("建议添加 LinkedIn 个人主页链接")

        # 地点 (25分)
        if any(loc in resume_text.lower() for loc in LOCATIONS):
            score += 25
        else:
            issues.append("建议添加所在城市")

        return {"score": score, "issues": issues}

    def identify_ats(self, jd_text: str) -> dict:
        """Identify ATS type from job description.

        Args:
            jd_text: Job description text.

        Returns:
            Dictionary with ATS type, confidence, and tips.
        """
        jd_lower = jd_text.lower()

        for ats_name, config in self.ats_patterns.items():
            for pattern in config["patterns"]:
                if pattern in jd_lower:
                    return {
                        "type": ats_name,
                        "confidence": 0.85,
                        "tips": config["tips"]
                    }

        return {
            "type": "unknown",
            "confidence": 0,
            "tips": [
                "无法识别具体 ATS 系统",
                "建议使用标准格式和关键词",
                "保持简历简洁明了"
            ]
        }

    def check_portfolio(self, resume_text: str) -> dict:
        """Check for portfolio and online links.

        Args:
            resume_text: Resume content text.

        Returns:
            Dictionary with score, issues list, and found links.
        """
        score = 0
        issues = []
        found_links = []

        # 检查常见的作品集链接
        for pattern in PORTFOLIO_PATTERNS:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            found_links.extend(matches)

        # 检查作品集关键词
        has_portfolio_keyword = any(kw in resume_text.lower() for kw in PORTFOLIO_KEYWORDS)

        if found_links:
            score = min(25, len(found_links) * 10)
        elif has_portfolio_keyword:
            score = 15
        else:
            issues.append("建议添加作品集链接（GitHub、个人网站等）")

        # 检查 LinkedIn
        if "linkedin.com/in/" in resume_text.lower():
            score = min(50, score + 25)

        return {"score": score, "issues": issues, "links": found_links}

    def check_personal_info(self, resume_text: str) -> dict:
        """Check for unnecessary personal information that may cause bias.

        Does not deduct score - only provides advice.
        """
        issues = []
        text_lower = resume_text.lower()

        # 年龄/生日
        age_patterns = [
            r'\b(19|20)\d{2}[-/年.]\d{1,2}[-/月.]\d{1,2}',
            r'\b\d{1,2}\s*(岁|years?\s*old)\b',
            r'\b(birth|出生|生日)\s*[:：]?\s*\d',
        ]
        for pattern in age_patterns:
            if re.search(pattern, text_lower):
                issues.append("建议删除年龄/生日信息，ATS不需要且可能引起偏见")
                break

        # 性别/婚姻状况
        gender_keywords = ['男', '女', '已婚', '未婚', '单身', '离异',
                          'male', 'female', 'married', 'single', 'divorced',
                          'gender', 'sex']
        if any(kw in text_lower for kw in gender_keywords):
            issues.append("建议删除性别/婚姻状况信息，与工作能力无关")

        # 照片
        photo_keywords = ['photo', '照片', '证件照', '头像', '近照']
        if any(kw in text_lower for kw in photo_keywords):
            issues.append("建议删除照片，ATS无法解析且可能引起偏见")

        # 宗教/政治
        sensitive_keywords = ['religion', '宗教', '政治', 'political', 'party member',
                             '党员', '民主党', '共和党', 'christian', 'muslim', 'buddhist']
        if any(kw in text_lower for kw in sensitive_keywords):
            issues.append("建议删除宗教/政治信息，与工作能力无关")

        # 国籍/民族
        nationality_keywords = ['国籍', '民族', 'nationality', 'ethnicity', 'race']
        if any(kw in text_lower for kw in nationality_keywords):
            issues.append("建议删除国籍/民族信息，可能引起偏见")

        return {"issues": issues}
