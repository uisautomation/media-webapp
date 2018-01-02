from setuptools import find_packages, setup

setup(
    name='smswebapp',
    packages=find_packages(),
    install_requires=[
        'django>=2.0',
        'django-automationcommon>=1.14',
        'django-ucamwebauth>=1.4.5',
        'psycopg2',
    ],
)
