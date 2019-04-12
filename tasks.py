# -*- coding: utf-8 -*-
import os
import re
import sys
import shutil
import subprocess
from pathlib import Path

import click
import faker

from fuzzyjoin import utils

# flake8: noqa

#############
## HELPERS ##
#############

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


def check_for_sentinel(filename):
    this_dir = os.path.dirname(__file__)
    filepath = os.path.join(this_dir, filename)
    context = utils.scan_for_token('xxx', filepath, context_lines=5)
    if context:
        msg = f"Sentinel found in {filename}"
        print()
        print('=' * len(msg))
        print(msg)
        print('=' * len(msg))
        print(*context)
        sys.exit(0)


def bump_version_file(version_part):
    this_dir = os.path.dirname(__file__)
    version_file = os.path.join(this_dir, 'VERSION')
    version_text = open(version_file).read()
    new_version = utils.bump_version(version_text, part=version_part)
    with open(version_file, 'w') as out:
        out.write(new_version)

    return new_version


def bump_version_init_file(new_version):
    this_dir = os.path.dirname(__file__)
    fuzzy_init_file = os.path.join(this_dir, 'fuzzyjoin', '__init__.py')
    fuzzy_init_text = open(fuzzy_init_file).read()
    rx_version = r'\d+\.\d+\.\d+'
    rx_version_line = f"__version__ = '{rx_version}'"
    old_version = re.search(rx_version_line, fuzzy_init_text).group()
    new_line = re.sub(rx_version, new_version, old_version)
    new_text = re.sub(rx_version_line, new_line, fuzzy_init_text)
    with open(fuzzy_init_file, 'w') as out:
        out.write(new_text)


#########
## CLI ##
#########


@click.group()
def tasks_cli():
    pass


@click.command('create-sample')
@click.argument('sample_type', type=click.Choice(['names']))
def cmd_create_sample(sample_type):
    if sample_type == 'names':
        this_dir = os.path.dirname(__file__)
        out_file = os.path.join(this_dir, 'data', 'names.txt')
        with open(out_file, 'w') as out:
            f = faker.Faker()
            out.write('id,name\n')
            for id in range(1, 10_001):
                out.write(f'{id},{f.name()}\n')

        print(f'[INFO] Wrote file: {out_file}')


@click.command('bump')
@click.argument('version_part', type=click.Choice(['major', 'minor', 'patch']))
def cmd_bump(version_part):
    new_version = bump_version_file(version_part)
    bump_version_init_file(new_version)


@click.command('check')
def cmd_check():
    execute_command('Flake8', ['flake8'])
    execute_command('MyPy', ['mypy', 'fuzzyjoin'])
    execute_command('PyTest', ['python', '-m', 'pytest', 'tests'])


@click.command('build')
def cmd_build():
    this_dir = os.path.dirname(__file__)
    check_for_sentinel('README.md')
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


@click.command('publish')
@click.option('--test', is_flag=True, help="Publish to TestPyPI.")
def cmd_publish(test):
    if test:
        repo = r'https://test.pypi.org/legacy/'
        cmd = ['twine', 'upload', f'--repository-url={repo}', 'dist/*']
    else:
        cmd = ['twine', 'upload', 'dist/*']

    print(cmd)
    execute_command('Publish', cmd)


tasks_cli.add_command(cmd_check)
tasks_cli.add_command(cmd_build)
tasks_cli.add_command(cmd_publish)
tasks_cli.add_command(cmd_create_sample)
tasks_cli.add_command(cmd_bump)

if __name__ == '__main__':
    tasks_cli()
