from setuptools import find_packages, setup

setup(
    name='smswebapp',
    packages=find_packages(),
    install_requires=[
        'django>=2.0',
    ],
    test_requires=[
        'coverage',
    ],
)
