from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="f2t2f",
    version="0.3.9",
    author="Vova Auer",
    author_email="mail@vovaauer.com",
    description="A CLI tool to capture entire folders, including file content, as structured JSON or text.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vovaauer/f2t2f",
    packages=find_packages(),
    license="MIT",
    license_files=("LICENSE",),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
    python_requires='>=3.7',
    install_requires=[
        "click",
        "pyperclip",
        "platformdirs",
        "patch",
    ],
    entry_points={
        "console_scripts": [
            "f2t2f = f2t2f.cli:cli",
        ],
    },
)