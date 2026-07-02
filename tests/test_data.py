"""ATS 引擎测试数据"""

STRONG_RESUME = """
John Doe
john.doe@email.com | (555) 123-4567 | San Francisco, CA
LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

PROFESSIONAL SUMMARY
Senior Software Engineer with 8+ years of experience building scalable web applications. Led teams of 5-10 engineers and delivered products serving 10M+ users.

EXPERIENCE

Senior Software Engineer | Meta | 2021-2024
- Led development of React-based dashboard serving 10M monthly active users
- Increased API performance by 45% through database optimization and caching
- Managed team of 5 engineers across 3 cross-functional projects
- Delivered 12 features on time, reducing customer support tickets by 30%

Software Engineer | Startup Inc | 2019-2021
- Built microservices architecture handling 1M requests/day
- Reduced infrastructure costs by 30% using AWS Lambda and DynamoDB
- Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes
- Mentored 3 junior developers, all promoted within 18 months

EDUCATION

BS Computer Science | Stanford University | 2018
- GPA: 3.8/4.0
- Relevant coursework: Data Structures, Algorithms, Machine Learning

SKILLS

Python, JavaScript, TypeScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL, MongoDB, Git, Agile, Scrum
"""

WEAK_RESUME = """
Jane Smith

Work History

Company A (2020-2023)
- Did stuff
- Helped with things
- Was responsible for stuff

Company B (2018-2020)
- Worked on projects
- Did various tasks

Education
Some University

Skills
Computer stuff
"""

JD_WITH_ATS = """
Software Engineer - Google
Apply at https://wd5.myworkdayjobs.com/en-US/Google

Requirements:
- 5+ years of experience
- Python, JavaScript, React
- AWS, Docker, Kubernetes
- Strong communication skills
"""

JD_WITHOUT_ATS = """
Senior Developer at Tech Corp

Requirements:
- Python, JavaScript, React
- AWS, Docker
- Team leadership experience
"""

STRONG_RESUME_CN = """
张三
zhangsan@email.com | 138-0000-0000 | 北京
LinkedIn: linkedin.com/in/zhangsan

专业摘要
资深后端工程师，8年经验，主导过日活1000万+产品的架构设计。

工作经历

高级后端工程师 | 字节跳动 | 2021-2024
- 主导微服务架构重构，系统QPS从5万提升至20万
- 优化数据库查询，接口响应时间降低60%
- 带领5人团队完成3个核心项目交付

后端工程师 | 美团 | 2019-2021
- 设计并实现订单系统，日处理订单量100万+
- 推动CI/CD落地，部署时间从2小时缩短至15分钟

教育背景

计算机科学学士 | 北京大学 | 2018

技能
Go, Python, Java, MySQL, Redis, Docker, Kubernetes, AWS
"""
