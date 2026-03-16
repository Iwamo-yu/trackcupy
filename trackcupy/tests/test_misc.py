import logging
import os
import types
import unittest
import warnings

import trackcupy
import trackcupy.diag
from trackcupy.tests.common import StrictTestCase
from trackcupy.try_numba import NUMBA_AVAILABLE

path, _ = os.path.split(os.path.abspath(__file__))


class DiagTests(StrictTestCase):
    def test_performance_report(self):
        trackcupy.diag.performance_report()

    def test_dependencies(self):
        trackcupy.diag.dependencies()


class LoggerTests(StrictTestCase):
    def test_heirarchy(self):
        self.assertTrue(trackcupy.linking.logger.parent is trackcupy.logger)
        self.assertTrue(trackcupy.feature.logger.parent is trackcupy.logger)
        self.assertTrue(trackcupy.preprocessing.logger.parent is trackcupy.logger)

    def test_convenience_funcs(self):
        trackcupy.quiet(True)
        self.assertEqual(trackcupy.logger.level, logging.WARN)
        trackcupy.quiet(False)
        self.assertEqual(trackcupy.logger.level, logging.INFO)

        trackcupy.ignore_logging()
        self.assertEqual(len(trackcupy.logger.handlers), 0)
        self.assertEqual(trackcupy.logger.level, logging.NOTSET)
        self.assertTrue(trackcupy.logger.propagate)

        trackcupy.handle_logging()
        self.assertEqual(len(trackcupy.logger.handlers), 1)
        self.assertEqual(trackcupy.logger.level, logging.INFO)
        self.assertEqual(trackcupy.logger.propagate, 1)


class NumbaTests(StrictTestCase):
    def setUp(self):
        if not NUMBA_AVAILABLE:
            raise unittest.SkipTest("Numba not installed. Skipping.")
        self.funcs = trackcupy.try_numba._registered_functions

    def tearDown(self):
        if NUMBA_AVAILABLE:
            trackcupy.enable_numba()

    def test_registered_numba_functions(self):
        self.assertGreater(len(self.funcs), 0)

    def test_enabled(self):
        trackcupy.enable_numba()
        for registered_func in self.funcs:
            module = __import__(registered_func.module_name, fromlist='.')
            func = getattr(module, registered_func.func_name)
            self.assertIs(func, registered_func.compiled)
            self.assertNotIsInstance(func, types.FunctionType)

    def test_disabled(self):
        trackcupy.disable_numba()
        for registered_func in self.funcs:
            module = __import__(registered_func.module_name, fromlist='.')
            func = getattr(module, registered_func.func_name)
            self.assertIs(func, registered_func.ordinary)
            self.assertIsInstance(func, types.FunctionType)
