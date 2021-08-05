import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='rob_aci',
    url='https://github.com/bobbourke/rb_aci',
    author='Rob Bourke',
    author_email='bourke.bob@gmail.com',
    # packages=['rob_aci'],
    install_requires=['requests', 'configparser', 'prettytable'],
    version='0.1',
    description='Python Class to work with ACI',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
