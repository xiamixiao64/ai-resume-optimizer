"""Tests for fairness checks in ATS engine."""
import pytest
from ats_engine import ATSEngine


@pytest.fixture
def engine():
    """Create ATSEngine instance for testing."""
    return ATSEngine()


class TestPersonalInfoCheck:
    """Test cases for check_personal_info method."""

    def test_clean_resume_no_issues(self, engine):
        """Resume without personal info should have no issues."""
        resume = """
        John Smith
        Email: john@example.com
        Phone: 123-456-7890
        LinkedIn: linkedin.com/in/johnsmith
        
        Experience
        Software Engineer at Tech Corp
        - Developed Python applications
        - Led team of 5 developers
        
        Skills
        Python, JavaScript, React
        """
        result = engine.check_personal_info(resume)
        assert result["issues"] == []

    def test_age_detection(self, engine):
        """Should detect age information."""
        resume = "John Doe\nAge: 25岁\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("年龄" in issue or "生日" in issue for issue in result["issues"])

    def test_birthday_detection(self, engine):
        """Should detect birthday information."""
        resume = "John Doe\nBirthday: 1995-01-15\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("年龄" in issue or "生日" in issue for issue in result["issues"])

    def test_chinese_age_format(self, engine):
        """Should detect Chinese age format."""
        resume = "张三\n25岁\n电话: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("年龄" in issue for issue in result["issues"])

    def test_gender_male_detection(self, engine):
        """Should detect male gender."""
        resume = "John Doe\nGender: Male\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("性别" in issue for issue in result["issues"])

    def test_gender_female_detection(self, engine):
        """Should detect female gender."""
        resume = "Jane Doe\nGender: Female\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("性别" in issue for issue in result["issues"])

    def test_chinese_gender_detection(self, engine):
        """Should detect Chinese gender characters."""
        resume = "李四\n男\n电话: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("性别" in issue for issue in result["issues"])

    def test_marital_status_detection(self, engine):
        """Should detect marital status."""
        resume = "John Doe\nMarital Status: Married\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("性别" in issue or "婚姻" in issue for issue in result["issues"])

    def test_photo_detection(self, engine):
        """Should detect photo references."""
        resume = "John Doe\nPhoto: [attached]\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("照片" in issue for issue in result["issues"])

    def test_chinese_photo_detection(self, engine):
        """Should detect Chinese photo keywords."""
        resume = "王五\n证件照: 1张\n电话: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("照片" in issue for issue in result["issues"])

    def test_religion_detection(self, engine):
        """Should detect religion information."""
        resume = "John Doe\nReligion: Christian\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("宗教" in issue for issue in result["issues"])

    def test_political_detection(self, engine):
        """Should detect political information."""
        resume = "张伟\n政治面貌: 党员\n电话: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("政治" in issue for issue in result["issues"])

    def test_nationality_detection(self, engine):
        """Should detect nationality information."""
        resume = "John Doe\nNationality: American\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("国籍" in issue for issue in result["issues"])

    def test_ethnicity_detection(self, engine):
        """Should detect ethnicity information."""
        resume = "李华\n民族: 汉族\n电话: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("民族" in issue for issue in result["issues"])

    def test_multiple_issues(self, engine):
        """Should detect multiple personal info issues."""
        resume = """
        张三
        性别: 男
        年龄: 25岁
        政治面貌: 党员
        电话: 123-456-7890
        """
        result = engine.check_personal_info(resume)
        assert len(result["issues"]) >= 2

    def test_case_insensitive(self, engine):
        """Should be case insensitive for English keywords."""
        resume = "John Doe\nGENDER: Male\nPhone: 123-456-7890"
        result = engine.check_personal_info(resume)
        assert any("性别" in issue for issue in result["issues"])


class TestFullAnalysisWithPersonalInfo:
    """Test full analysis with personal information."""

    def test_analysis_includes_personal_info(self, engine):
        """Full analysis should include personal_info in breakdown."""
        resume = """
        John Doe
        Gender: Male
        Age: 25岁
        Email: john@example.com
        Phone: 123-456-7890
        
        Experience
        Software Engineer
        - Developed applications
        
        Skills
        Python
        """
        jd = "Python developer with experience"
        result = engine.analyze(resume, jd)
        
        assert "personal_info" in result["breakdown"]
        assert "issues" in result["breakdown"]["personal_info"]

    def test_improvements_include_personal_info(self, engine):
        """Improvements should include personal info suggestions."""
        resume = """
        John Doe
        Gender: Male
        Age: 25岁
        Email: john@example.com
        Phone: 123-456-7890
        
        Experience
        Software Engineer
        - Developed applications
        
        Skills
        Python
        """
        jd = "Python developer with experience"
        result = engine.analyze(resume, jd)
        
        personal_info_issues = result["breakdown"]["personal_info"]["issues"]
        assert any("年龄" in issue or "性别" in issue for issue in personal_info_issues)

    def test_score_not_affected_by_personal_info(self, engine):
        """Score should not be affected by personal info issues."""
        resume_clean = """
        John Doe
        Email: john@example.com
        Phone: 123-456-7890
        
        Experience
        Software Engineer
        - Developed applications
        
        Skills
        Python
        """
        
        resume_with_info = """
        John Doe
        Gender: Male
        Age: 25岁
        Email: john@example.com
        Phone: 123-456-7890
        
        Experience
        Software Engineer
        - Developed applications
        
        Skills
        Python
        """
        
        jd = "Python developer with experience"
        
        result_clean = engine.analyze(resume_clean, jd)
        result_with_info = engine.analyze(resume_with_info, jd)
        
        # Scores should be similar (personal info doesn't affect score)
        assert abs(result_clean["ats_score"] - result_with_info["ats_score"]) <= 5


class TestEdgeCases:
    """Test edge cases for personal info detection."""

    def test_empty_resume(self, engine):
        """Should handle empty resume."""
        result = engine.check_personal_info("")
        assert result["issues"] == []

    def test_no_false_positives(self, engine):
        """Should not flag normal content as personal info."""
        resume = """
        Software Engineer with 5 years of experience
        Led team of 10 developers
        Increased revenue by 50%
        Skills: Python, JavaScript, React
        """
        result = engine.check_personal_info(resume)
        assert result["issues"] == []

    def test_date_not_flagged_as_age(self, engine):
        """Work dates should not be flagged as age."""
        resume = """
        Experience
        2020-2023: Software Engineer at Tech Corp
        """
        result = engine.check_personal_info(resume)
        # Should not flag work dates as age
        assert not any("年龄" in issue for issue in result["issues"])
