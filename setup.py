from setuptools import setup, find_packages

setup(
    name="CAPM",
    version="1.3.0",
    packages=find_packages(),
    py_modules=["CAPM"],
    install_requires=[
        "pandas",
        "numpy",
        "statsmodels",
        "matplotlib",
        "openpyxl",
        "zhdate",
        "akshare",
    ],
    entry_points={
        "console_scripts": [
            "capm=CAPM:main",
        ],
    },
    author="User",
    description="Civil aviation passenger traffic volume prediction model",
)
