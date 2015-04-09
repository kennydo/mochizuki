from setuptools import setup, find_packages


setup(
    name='mochizuki',
    version='0.0.1',
    description='Python IRC server',
    long_description='',
    url='https://github.com/kennydo/mochizuki',
    author='Kenny Do',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet',
    ],
    keywords='IRC server',
    packages=find_packages(),
    install_requires=[
    ],
    tests_require=[
    ],
    entry_points={
    },
)
