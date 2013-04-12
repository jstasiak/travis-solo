# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from nose.tools import eq_, ok_

from travis_solo import Configuration, Loader, Step

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
			env=['A=a', 'A=b'],
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
						env='A=a',
					),
				],
			)
		)

		configurations = self.loader.load_configurations(settings)

		eq_(configurations, (
			Configuration(python='2.7', variables={'A': 'a'}),
			Configuration(python='2.7', variables={'A': 'b'}),
			Configuration(python='3.3', variables={'A': 'b'}),
			Configuration(python='2.7', variables={'A': 'c'}),
		))
