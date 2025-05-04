from setuptools import setup, find_packages

setup(
    name="memcore",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "python-dotenv",
        "requests",
        "numpy",
        "rich",
        "fastapi",
        "uvicorn",
        "ttkbootstrap"
    ],
    entry_points={
        "console_scripts": [
            "memcore=memcore:cli_main",
        ],
    },
    author="Arubik Dev",
    description="A comprehensive memory management system with vector search capabilities",
    keywords="memory, vector search, embeddings, ai",
    python_requires=">=3.7",
)
