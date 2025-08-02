from setuptools import setup

setup(
    name="pastebincli",
    version="1.0.0",
    packages=["pastebincli"],
    entry_points={
        "console_scripts": [
            "pastebincli = pastebincli.__main__:main"
        ],
    },
    install_requires=[
        "requests",
        "rich",
    ],
    python_requires=">=3.10",
    author="CoolSoulz",
    description="A command-line interface to paste to Pastebin",
    url="https://github.com/CoolSoulz/pastebincli",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
