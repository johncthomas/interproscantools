from setuptools import setup, find_packages
#print(find_packages())

setup(
    name='interproscantools',
    description='Run a batch of InterProScan searches from a FastA file, tabulate the results in an Excel document.',
    version='1.2',
    author='John C. Thomas',
    author_email='jaytee00@gmail.com',
    include_package_data=True,
    install_requires = ['biopython >= 1.43','openpyxl >= 2',],
    #extras_require = {'Excel':'openpyxl >= 2'},
    classifiers= ['Programming Language :: Python :: 3',
                  'Development Status :: 4 - beta',],
    keywords = "interpro interproscan interproscan_tools bioinformatics protein biopython",
    packages = find_packages(),
)

