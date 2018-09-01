import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="borg_pod",
    version="1.0.31",
    author="Andrew M. Hogan",
    author_email="drewthedruid@gmail.com",
    description="A lightweight, decoupled wrapper for dynamic class assignment.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Andrew-Hogan/borg_pod",
    packages=setuptools.find_packages(),
    install_requires=[],
    platforms=['any'],
    license="LICENSE",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
