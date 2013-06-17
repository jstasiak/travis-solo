# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from itertools import permutations
from os.path import join

from mock import Mock
from nose.tools import eq_, ok_

from travis_solo import Configuration, Loader, Runner, Step

class TestLoader(object):
	def setup(self):
		self.loader = Loader()

	def test_loading_steps(self):
		settings = (
			('before_install', ['do before install',]),
			('install', 'pip install .'),
			('before_script', 'xxx'),
			('script', 'nosetests'),
			('after_script', ['a', 'b']),
		)
		expected = (
			Step('before_install', ('do before install',)),
			Step('install', ('pip install .',)),
			Step('before_script', ('xxx',)),
			Step('script', ('nosetests',)),
			Step('after_script', ('a', 'b'), can_fail=True),
		)

		for i in range(len(settings)):
			yield self.check_loading_steps, dict(settings[:i] + settings[i + 1:]), expected[:i] + expected[i + 1:]

	def check_loading_steps(self, settings, expected):
		result = self.loader.load_steps(settings)
		eq_(result, expected)

	def test_loading_configurations(self):
		settings = dict(
			language='python',
			python=['2.7', '3.3'],
			env=['A=a B="asd qwe x=y"', 'A=b'],
			matrix=dict(
				include=[
					dict(
						python='2.7',
						env='A=c',
					),
				],
				exclude=[
					dict(
						python='3.3',
						env='A=a B="asd qwe x=y"',
					),
					dict(
						python='3.3',
					),
				],
				allow_failures=[
					dict(
						python='2.7',
						env='A=b',
					),
				]
			)
		)

		configurations = self.loader.load_configurations(settings)

		eq_(configurations, (
			Configuration(python='2.7', variables={'A': 'a', 'B': 'asd qwe x=y'}),
			Configuration(python='2.7', variables={'A': 'b'}, can_fail=True),
			Configuration(python='3.3', variables={'A': 'b'}),
			Configuration(python='2.7', variables={'A': 'c'}),
		))

class TestRunner(object):
	def setup(self):
		self.runner = Runner(None, ())

	def test_result_depends_on_configuration_runs(self):
		failing = Mock()
		failing.can_fail = False
		failing.run_build.side_effect = Exception()

		succeeding = Mock()
		succeeding.can_fail = False

		failing_and_can_fail = Mock()
		failing_and_can_fail.can_fail = True
		failing_and_can_fail.run_build.side_effect = Exception()

		for confs, result in (
				((failing,), 1),
				((succeeding,), 0),
				((failing_and_can_fail,), 0),
				((failing, succeeding), 1),
				((failing, failing_and_can_fail), 1),
				((succeeding, failing_and_can_fail), 0),
				((succeeding, failing, failing_and_can_fail), 1)):
			for confs_permutation in permutations(confs):
				yield self.check_configurations_and_result, confs_permutation, result

	def check_configurations_and_result(self, configurations, result):
		self.runner.configurations = configurations
		eq_(self.runner.run(), result)

class TestConfiguration(object):
	def setup(self):
		self.check_call = Mock()
		self.isdir = Mock()
		self.environ = dict(PATH='/usr/bin', __PYVENV_LAUNCHER__='x')
		self.configuration = Configuration(
			python='2.7', variables=dict(A='a', B='x'), check_call=self.check_call, isdir=self.isdir, environ=self.environ)

	def test_env_vars_are_set_before_running_a_build(self):
		outer = self

		class B(object):
			def run(self, environ):
				eq_(environ.get('CI'), 'true')
				eq_(environ.get('TRAVIS'), 'true')
				eq_(environ.get('TRAVIS_SOLO'), 'true')

				path_elements = environ.get('PATH', '').split(':')
				ok_(len(path_elements) > 0)
				eq_(path_elements[0], join(outer.configuration.virtualenv_path, 'bin'))
				assert '__PYVENV_LAUNCHER__' not in environ

		build = B()
		self.configuration.run_build(build)
