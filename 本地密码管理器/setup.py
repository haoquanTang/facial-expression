from setuptools import setup, find_packages

setup(
    name="password-manager",
    version="1.0.0",
    description="本地密码管理器",
    author="开发团队",
    packages=find_packages(),
    install_requires=[
        "pycryptodome>=3.19.0",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        "console_scripts": [
            "password-manager=main:main",
        ],
    },
    python_requires=">=3.8",
)