from setuptools import setup, find_packages

setup(
    name="constitutional-llm",
    version="2.0.0",
    description="Constitutional Governance Framework for AI Agents",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pytest",
    ],
)
