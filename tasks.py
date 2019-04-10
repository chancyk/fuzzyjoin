# -*- coding: utf-8 -*-
import os
import shutil
import subprocess

import click

# flake8: noqa

def execute_command(cmd_name, cmd):
    result = subprocess.run(cmd)
    if result.returncode == 0:
        import punch_version as v
        version = f'{v.major}.{v.minor}.{v.patch}'
        msg = f'[INFO] {cmd_name} complete: {version}'
        print('-' * len(msg))
        print(msg + '\n')
    else:
        msg = f'[ERROR] {cmd_name} failed. See above.'
        print('-' * len(msg))
        print(msg + '\n')


@click.group()
def tasks_cli():
    pass


@click.command()
def check():
    execute_command('Flake8', ['flake8'])
    execute_command('MyPy', ['mypy', 'fuzzyjoin'])
    execute_command('PyTest', ['python', '-m', 'pytest', 'tests'])


@click.command()
def build():
    this_dir = os.path.dirname(__file__)
    # Remove build/
    dir_path = os.path.join(this_dir, 'build')
    if os.path.exists(dir_path):
        print('[INFO] Removing: %s' % dir_path)
        shutil.rmtree(dir_path)
    # Remove dist/
    dir_path = os.path.join(this_dir, 'dist')
    if os.path.exists(dir_path):
        print('[INFO] Removing: %s' % dir_path)
        shutil.rmtree(dir_path)

    cmd = ['python', 'setup.py', 'sdist', 'bdist_wheel']
    execute_command('Build', cmd)


@click.command()
@click.option('--test', is_flag=True, help="Publish to TestPyPI.")
def publish(test):
    if test:
        repo = r'https://test.pypi.org/legacy/'
        cmd = ['twine', 'upload', f'--repository-url={repo}', 'dist/*']
    else:
        cmd = ['twine', 'upload', 'dist/*']

    print(cmd)
    execute_command('Publish', cmd)


tasks_cli.add_command(check)
tasks_cli.add_command(build)
tasks_cli.add_command(publish)

if __name__ == '__main__':
    tasks_cli()
