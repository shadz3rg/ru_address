from setuptools import setup, find_packages
from ru_address import __version__

setup(
    name='ru_address',
    author='Oleg Aleksandrovich',
    author_email='oleg.shooz@gmail.com',
    version=__version__,
    url='http://github.com/shadz3rg/ru_address',
    py_modules=['ru_address'],
    description='Конвертор выгрузки БД ФИАС в SQL формат',
    long_description=open('README.rst').read(),
    license='MIT',
    packages=find_packages(),
    install_requires=["click", 'lxml', 'psutil'],
    entry_points='''
       [console_scripts]
        ru_address=ru_address.command:cli
    ''',
    classifiers=(
        'Environment :: Console',
    ),
)
