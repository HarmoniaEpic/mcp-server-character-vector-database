# vector_database_mcp/setup.py
from setuptools import setup, find_packages

def read_requirements(filename):
    """Read requirements from file, handling -r references"""
    requirements = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('-r '):
                    # Recursively read referenced requirements
                    ref_file = line[3:].strip()
                    requirements.extend(read_requirements(ref_file))
                else:
                    requirements.append(line)
    return requirements

setup(
    name="vector_database_mcp",
    version="3.1.4",
    packages=find_packages(),
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': read_requirements('requirements-dev.txt'),
        'test': read_requirements('requirements-test.txt'),
    },
    python_requires='>=3.8',
    author="Your Name",
    author_email="your.email@example.com",
    description="AI Agent Integrated Vector Database MCP Server",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
