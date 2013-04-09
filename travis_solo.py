# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import shlex
import sys

from itertools import product
from collections import namedtuple
from os import getcwd
from os.path import abspath, dirname, isdir, isfile, join
from subprocess import CalledProcessError, check_call

from termcolor import colored
from yaml import safe_load

__version__ = '0.0.2'

def log(message=''):
	print(message)

def log_command(command):
	log('$ %s' % (colored(command, attrs=['bold']),))

def log_error(error):
	log(colored('%s' % (error,), 'red'))

def as_list(obj):
	return obj if isinstance(obj, list) else [obj]

class Step(object):
	def __init__(self, name, commands, can_fail, check_call=check_call):
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


class Build(object):
	def __init__(self, steps):
		self.steps = steps

	def run(self):
		for step in self.steps:
			step.perform()


class Configuration(object):
	def __init__(
			self, python, variables, recreate=False,
			check_call=check_call, isdir=isdir, environ=os.environ):
		self.python = python
		self.variables = variables
		self.recreate=recreate
		self.check_call = check_call
		self.isdir = isdir
		self.environ = environ

	@property
	def virtualenv_path(self):
		return join(getcwd(), '.travis-solo', self.python)

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
		if not self.isdir(self.virtualenv_path) or self.recreate:
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
		self.environ['PATH'] = ':'.join((self.virtualenv_path, self.environ['PATH']))
		for name in ('CI', 'TRAVIS', 'TRAVIS_SOLO'):
			self.environ[name] = 'true'

		self.environ['TRAVIS_PYTHON_VERSION'] = self.python

		self.environ.update(self.variables)

	def __unicode__(self):
		envs = ', '.join(('%s=%r' % (k, v) for (k, v) in self.variables.items()))
		return self.full_python + (' (%s)' % (envs,) if envs else '')

	def __repr__(self):
		return '%s(%s)' % (
			self.__class__.__name__,
			', '.join(('%s=%s' % (key, getattr(self, key)) for key in ('python', 'variables')))
		)


class Runner(object):
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

		success = all(result for (_, result, _) in results)
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
			commands = as_list(settings.get(name, []))
			if commands:
				steps.append(Step(
					name=name,
					commands=commands,
					can_fail=can_fail
				))

		return steps

	def load_configurations(self, settings):
		assert settings['language'] == 'python', 'Only Python projects are supported right now'

		versions = as_list(settings.get('python', '2.7'))
		env_sets = [self.parse_env_set(es) for es in as_list(settings.get('env', ''))]

		build_matrix = list(product(versions, env_sets))

		matrix = settings.get('matrix', {})
		include = matrix.get('include', [])
		for i in include:
			version = i['python']
			env_set = self.parse_env_set(i['env'])
			element = (version, env_set)
			if element not in build_matrix:
				build_matrix.append(element)

		exclude = matrix.get('exclude', [])
		for e in exclude:
			version = e['python']
			env_set = self.parse_env_set(e['env'])
			element = (version, env_set)
			if element in build_matrix:
				build_matrix.remove(element)

		return [Configuration(python=p, variables=dict(v)) for (p, v) in build_matrix]

	def load_from_file(self, file):
		with open(file) as fd:
			settings = safe_load(fd)

		steps = self.load_steps(settings)
		configurations = self.load_configurations(settings)

		build = Build(steps)
		return Runner(build, configurations)

	def parse_env_set(self, env_set):
		return tuple(tuple(e.strip().split('=')) for e in env_set.split())


def main():
	travis_file = join(getcwd(), '.travis.yml')
	assert isfile(travis_file), 'No .travis.yml file found in current directory'

	loader = Loader()
	runner = loader.load_from_file(travis_file)
	sys.exit(runner.run())

if __name__ == '__main__':
	main()
