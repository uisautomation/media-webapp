"""
Custom test suite runner.

"""
import unittest

import django.test.runner


class BufferedTextTestRunner(unittest.TextTestRunner):
    """
    A sub-class of :py:class:`unittest.TextTestRunner` with identical behaviour
    except that the *buffer* keyword argument to the constructor defaults to
    True.

    """
    def __init__(self, stream=None, descriptions=True, verbosity=1,
                 failfast=False, buffer=True, resultclass=None, warnings=None,
                 *, tb_locals=False, **kwargs):
        return super().__init__(stream, descriptions, verbosity, failfast,
                                buffer, resultclass, warnings,
                                tb_locals=tb_locals, **kwargs)


class BufferedDiscoverRunner(django.test.runner.DiscoverRunner):
    """
    A sub-class of :py:class:`django.test.runner.DiscoverRunner` which has
    exactly the same behaviour except that the :py:attr:`.test_runner` attribute
    is set to :py:class:`.BufferedTextTestRunner`.

    The upshot of this is that output to stdout and stderror is captured and
    only reported on test failure.

    """
    test_runner = BufferedTextTestRunner
