# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import shlex
import sys

from argparse import ArgumentParser
from itertools import product
from collections import namedtuple
from os import getcwd
from os.path import abspath, dirname, isdir, isfile, join
from subprocess import CalledProcessError, check_call

from termcolor import colored
from yaml import safe_load

__version__ = '0.0.5'

def log(message=''):
	print(message)

def log_command(command):
	log('$ %s' % (colored(command, attrs=['bold']),))

def log_error(error):
	log(colored('%s' % (error,), 'red'))

def as_tuple(obj):
	return tuple(obj) if isinstance(obj, (list, tuple)) else (obj,)

not_set = object()

class Structure(object):
	fields = ()

	def __hash__(self):
		return hash([getattr(self, str(f)) for f in self.fields])

	def __eq__(self, other):
		return type(self) == type(other) and \
			[getattr(self, str(f)) for f in self.fields] == [getattr(other, str(f)) for f in self.fields]

	def __repr__(self):
		return '%s(%s)' % (
			self.__class__.__name__,
			', '.join(('%s=%r' % (key, getattr(self, str(key))) for key in self.fields))
		)


class Step(Structure):
	fields = ('name', 'commands', 'can_fail',)

	def __init__(self, name, commands, can_fail=False, check_call=check_call):
		self.name = name
		self.commands = commands
		self.can_fail = can_fail
		self.check_call = check_call

	def perform(self):
		try:
			for command in self.commands:
				self.execute(command)
		except Exception as e:
			log_error('Error performing %r step' % (self,))
			if not self.can_fail:
				raise

	def execute(self, command):
		if command.startswith('sudo'):
			log(colored(
				'%r ignored because it contains sudo reference' % (command,), 'yellow'))
		else:
			log_command(command)
			self.check_call(command, shell=True)

	def __unicode__(self):
		return self.name


class Build(Structure):
	fields = ('steps',)

	def __init__(self, steps):
		self.steps = steps

	def run(self):
		for step in self.steps:
			step.perform()


class Configuration(Structure):
	fields = ('python', 'variables', 'can_fail', 'recreate')

	def __init__(self,
			python, variables, base_path='.travis-solo', can_fail=False, recreate=False,
			check_call=check_call, isdir=isdir, environ=os.environ):
		self.base_path = base_path
		self.python = python
		self.variables = variables
		self.can_fail = can_fail
		self.recreate = recreate
		self.check_call = check_call
		self.isdir = isdir
		self.environ = environ

	@property
	def virtualenv_path(self):
		return join(self.base_path, self.python)

	@property
	def full_python(self):
		return ('python' if not self.python.startswith('py') else '') + self.python

	def run_build(self, build):
		original_environ = self.environ.copy()
		try:
			log(colored('\n\nBuild configuration %s running' % (self,), attrs=['bold']))
			log('Preparing the environment')
			self.prepare_virtualenv()
			self.prepare_environment()
			build.run()
		except Exception as e:
			log_error(e)
			raise
		finally:
			self.environ.clear()
			self.environ.update(original_environ)

	def prepare_virtualenv(self):
		try:
			command = 'virtualenv --distribute --python=%s %s' % (
				self.full_python, self.virtualenv_path)
			log_command(command)
			self.check_call(command, shell=True)
		except OSError as e:
			log_error(e)
			raise Exception('No virtualenv executable found, please install virtualenv')
		except CalledProcessError as e:
			if e.returncode == 3:
				log_error(e)
				raise Exception('Interpreter not found')
			else:
				raise

	def prepare_environment(self):
		self.environ['PATH'] = ':'.join((join(self.virtualenv_path, 'bin'), self.environ['PATH']))
		for name in ('CI', 'TRAVIS', 'TRAVIS_SOLO'):
			self.environ[name] = 'true'

		self.environ['TRAVIS_PYTHON_VERSION'] = self.python

		self.environ.update(self.variables)

	def __unicode__(self):
		envs = ', '.join(('%s=%r' % (k, v) for (k, v) in self.variables.items()))
		return self.full_python + (' (%s)' % (envs,) if envs else '')


class Runner(Structure):
	fields = ('build', 'configurations')

	def __init__(self, build, configurations):
		self.build = build
		self.configurations = configurations

	def run(self):
		results = []
		for c in self.configurations:
			try:
				c.run_build(self.build)
				results.append((c, True, 'Build succeeded'))
			except Exception as e:
				results.append((c, False, e))

		log(colored('\n\nBuild summary:', attrs=['bold']))
		for conf, result, message in results:
			color = 'green' if result else 'red'
			log(colored('%s: %s' % (conf, message), color))

		success = all(result for (configuration, result, _) in results if not configuration.can_fail)
		return 0 if success else 1

class Loader(object):
	def load_steps(self, settings):
		lifecycle = (
			('before_install', False),
			('install', False),
			('before_script', False),
			('script', False),
			('after_script', True),
		)

		steps = []
		for name, can_fail in lifecycle:
			commands = as_tuple(settings.get(name, []))
			if commands:
				steps.append(Step(
					name=name,
					commands=commands,
					can_fail=can_fail
				))

		return tuple(steps)

	def load_configurations(self, settings):
		assert settings['language'] == 'python', 'Only Python projects are supported right now'

		versions = as_tuple(settings.get('python', '2.7'))
		env_sets = [self.parse_env_set(es) for es in as_tuple(settings.get('env', ''))]

		build_matrix = list(product(versions, env_sets))

		matrix = settings.get('matrix', {})
		include = matrix.get('include', [])
		for i in include:
			version = i['python']
			env_set = self.parse_env_set(i.get('env', ''))
			element = (version, env_set)
			if element not in build_matrix:
				build_matrix.append(element)

		exclude = matrix.get('exclude', [])
		for e in exclude:
			version = e['python']
			env_set = self.parse_env_set(e.get('env', ''))
			element = (version, env_set)
			if element in build_matrix:
				build_matrix.remove(element)

		configurations = tuple((
			Configuration(python=p, variables=dict(v), base_path=join(getcwd(), '.travis-solo'))
			for (p, v) in build_matrix
		))
		allow_failures = matrix.get('allow_failures', [])
		for af in allow_failures:
			python = af.get('python')
			variables = dict(self.parse_env_set(af.get('env', '')))
			for c in configurations:
				if c.python == python and c.variables == variables:
					c.can_fail = True

		return configurations

	def parse_env_set(self, env_set):
		return tuple(tuple(e.strip().split('=')) for e in env_set.split())

class Application(object):
	def __init__(self, getcwd=getcwd, isfile=isfile, open=open):
		self.getcwd = getcwd
		self.isfile = isfile
		self.open = open

	def run(self, argv):
		args = self.get_args(argv)
		settings = self.get_settings(args)
		
		loader = Loader()
		steps = loader.load_steps(settings)
		configurations = loader.load_configurations(settings)

		build = Build(steps)
		runner = Runner(build, configurations)
		sys.exit(runner.run())

	def get_args(self, argv):
		parser = ArgumentParser(description='Local Travis build runner')
		parser.add_argument(
			'--overwrite', dest='overwrite', action='store',
			help='Overwrite settings loaded from file with JSON-encoded dict. Usage:\n'
			     '''--overwrite '{"python": "2.7", "env": ["A=a", "A=b"]}' ''')
		parser.add_argument('--version', action='version', version=__version__)
				
		return parser.parse_args(argv[1:])

	def get_settings(self, args):
		travis_file = join(self.getcwd(), '.travis.yml')
		assert self.isfile(travis_file), 'File %s not found' % (travis_file,)

		with self.open(travis_file) as fd:
			settings = safe_load(fd)

		overwrite = args.overwrite or '{}'
		decoded = json.loads(overwrite)
		settings.update(decoded)

		return settings

def main():
	app = Application()
	app.run(sys.argv)

if __name__ == '__main__':
	main()
