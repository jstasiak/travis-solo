# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from nose.tools import eq_, ok_

from travis_solo import Configuration, Loader, Step

class TestLoader(object):
    def setup(self):
        self.loader = Loader()

    def test_loading_steps(self):
        settings = dict(
            before_install=['do before install',],
            install='pip install .',
            script='nosetests',
            after_script=['a', 'b'],
        )
        steps = self.loader.load_steps(settings)
        eq_(steps, (
            Step('before_install', ('do before install',)),
            Step('install', ('pip install .',)),
            Step('script', ('nosetests',)),
            Step('after_script', ('a', 'b'), can_fail=True),
        ))

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
