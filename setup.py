# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in pibical/__init__.py
from pibical import __version__ as version

setup(
	name='pibical',
	version=version,
	description='Frappe App for Events syncronization with CalDav and iCalendar',
	author='pibico',
	author_email='pibico.sl@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
