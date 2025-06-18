from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="stackspot-client",
    version="0.1.4",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "env": ["python-dotenv>=1.1.0"],
    },
    author="KaiofPrates",
    author_email="kaiofprudencio@gmail.com",
    maintainer="eltonjosesouza",
    maintainer_email="github@eltonjose.com.br",
    description="Cliente Python para a API do StackSpot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kaiofprates/stackspot-client",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)