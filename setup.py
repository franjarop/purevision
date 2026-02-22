from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="purevision",
    version="0.1.0",
    author="Javier Robles",
    description="Sistema modular para procesamiento de video con magnificación euleriana en Jetson Nano Orin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/purevision",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Image Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "scipy>=1.11.0",
        "PyYAML>=6.0",
        "Jetson.GPIO>=2.1.0",
        "Pillow>=10.0.0",
        "scikit-image>=0.21.0",
        "python-dotenv>=1.0.0",
        "colorlog>=6.7.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "viz": [
            "matplotlib>=3.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "purevision=main:main",
            "purevision-devices=device_list:main",
            "purevision-modules=module_manager:main",
        ],
    },
)
