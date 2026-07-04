from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ats-engine",
    version="1.0.0",
    author="ResumeForge AI",
    author_email="xiamixiao64@gmail.com",
    description="Open-source ATS resume analyzer with 12 ATS type detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ats-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.7",
    install_requires=[
        "difflib",  # Built-in, listed for documentation
    ],
    keywords="ats resume optimizer job application tracker keywords",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ats-engine/issues",
        "Source": "https://github.com/yourusername/ats-engine",
        "Documentation": "https://github.com/yourusername/ats-engine#readme",
    },
)
