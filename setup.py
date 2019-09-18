import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

fid = open('pysit2stand/version.py')
vers = fid.readlines()[-1].split()[-1].strip("\"'")
fid.close()

setuptools.setup(
    name="pysit2stand",
    version=vers,
    author="Lukas Adamowicz",
    author_email="lukas.adamowicz@pfizer.com",
    description="Sit-to-stand detection using a single lumbar-mounted accelerometer.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PfizerRD/pysit2stand",
    download_url="https://pypi.org/project/pysit2stand/",
    project_urls={
        "Documentation": "https://pysit2stand.readthedocs.io/en/latest/"
    },
    include_pacakge_data=True,
    package_data={'pysit2stand': ['data/*.csv']},
    packages=setuptools.find_packages(),
    license='MIT',
    python_requires='>=3.6',
    install_requires=[
        'numpy',
        'scipy',
        'pandas',
        'pywavelets'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3.7"
    ],
)