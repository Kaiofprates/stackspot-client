from setuptools import setup, find_packages

setup(
    name="stackspot-client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
    ],
    author="KaiofPrates",
    author_email="kaiofprudencio@gmail.com",
    description="Cliente Python para a API do StackSpot",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kaiofprates/stackspot-client",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 