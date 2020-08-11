import setuptools

with open('README.rst', 'r') as fh:
    long_description = fh.read()


with open('requirements', 'r') as fh:
    pip_req = fh.read().split('\n')
    pip_req = [x.strip() for x in pip_req if len(x.strip()) > 0]

with open('optional_requirements', 'r') as fh:
    opt_req = fh.read().split('\n')
    opt_req = [x.strip() for x in opt_req if len(x.strip()) > 0]


setuptools.setup(
    name='pypaper',
    version='0.6.0',
    long_description=long_description,
    url='https://github.com/danielk333/pypaper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU-GPLv3',
        'Operating System :: OS Independent',
    ],
    entry_points={'console_scripts': ['pypaper=pypaper.paper:run']},
    install_requires=pip_req,
    extras_require={'extras': opt_req},
    packages=setuptools.find_packages(),
    # metadata to display on PyPI
    author='Daniel Kastinen',
    author_email='daniel.kastinen@irf.se',
    description='Python Paper citation database handler',
    license='GNU-GPLv3',
)
