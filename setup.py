import setuptools

setuptools.setup(
    name="tika-client",
    version="0.0.3",
    author="Trenton H.",
    description="A modern Python REST client for Apache Tika server.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/stumpylog/tika-client",
    packages=setuptools.find_packages(exclude=('tests*',)),
    license="GPL3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    install_requires=[],
    python_requires=">=3.7"
)
