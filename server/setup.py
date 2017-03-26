from setuptools import setup

setup(
    name='yaFootball',
    packages=['yaFootball'],
    include_package_data=True,
    install_requires=[
        'flask'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
