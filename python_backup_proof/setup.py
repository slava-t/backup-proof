from setuptools import setup, find_packages

requires = [
  'requests==2.26',
]

setup(
  name='python_backup_proof',
  version='0.0.1',
  author='Debuggex',
  author_email='',
  description='Backup proof library',
  license='Unlicensed',
  keywords='',
  url='https://www.parsehub.com',
  packages=find_packages(),
  long_description='Backup proof library',
  install_requires=requires,
  entry_points={
    'console_scripts': [
      'run_confirm_process = backup_confirm.process:main',
      'confirm = backup_confirm.confirm:main',
    ],
  },
)
