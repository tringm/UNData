import time
import filecmp
import logging
import os
import unittest
from pathlib import Path

from config import root_path, set_up_logger, DEFAULT_INPUT_FOLDER, DEFAULT_OUTPUT_FOLDER


class MeldInteractiveTestResult(unittest.TextTestResult):
    def addFailure(self, test, err):
        if hasattr(test, 'out_file') and hasattr(test, 'exp_file'):
            method_id = test.id().split('.')[-1]
            if method_id in test.out_file and method_id in test.exp_file:
                cont = True
                while cont:
                    res = input("[d]iff, [c]ontinue or [f]reeze? ")
                    if res == "f":
                        os.rename(test.out_file[method_id], test.exp_file[method_id])
                        cont = False
                    elif res == "c":
                        cont = False
                    elif res == "d":
                        os.system("meld " + str(test.exp_file[method_id]) + " " + str(test.out_file[method_id]))
        super().addFailure(test, err)

    def addError(self, test, err):
        super().addError(test, err)


class GenericTestCase(unittest.TestCase):
    currentResult = None

    @classmethod
    def setUpClass(cls):
        """
        Set up default folder for input, output, in, out, exp files
        :return:
        """
        cls.input_folder = DEFAULT_INPUT_FOLDER
        cls.output_folder = DEFAULT_OUTPUT_FOLDER
        cls.out_files = {}
        cls.exp_files = {}
        cls.in_files = {}
        cls.log_files = {}
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

    def setUp(self):
        """
        Init start time of test method
        :return:
        """
        self._started_at = time.time()

    def tearDown(self):
        """Init elapsed time of test method"""
        self._elapsed = time.time() - self._started_at
        ok = self.currentResult.wasSuccessful()
        errors = self.currentResult.errors
        failures = self.currentResult.failures
        result = 'success' if ok else 'failed'

        metrics_row = f"{self.id()}, {result}, {errors}, {failures}, {self._elapsed:5f}\n"

        if not (DEFAULT_OUTPUT_FOLDER / 'test_result_metrics.csv').is_file():
            with (DEFAULT_OUTPUT_FOLDER / 'test_result_metrics.csv').open(mode='w') as f:
                f.write("method, result, errors, failures, elapsed\n")
                f.write(metrics_row)
        else:
            with (DEFAULT_OUTPUT_FOLDER / 'test_result_metrics.csv').open(mode='a+') as f:
                f.write(metrics_row)

    def run(self, result=None):
        self.currentResult = result
        super().run(result)

    def file_compare(self, out_f: Path, exp_f: Path, msg=None):
        if not out_f.exists() or not exp_f.exists():
            raise ValueError(f"Either {out_f} or {exp_f} does not exist")
        if not out_f.is_file() or not exp_f.is_file():
            raise ValueError(f"Either {out_f} or {exp_f} is not a file")
        if not msg:
            self.assertTrue(filecmp.cmp(str(out_f), str(exp_f), shallow=False),
                            f"out file {str(out_f)} does not match exp file {str(exp_f)}")
        else:
            self.assertTrue(filecmp.cmp(str(out_f), str(exp_f), shallow=False), msg)

    def set_up_compare_files(self, method_id):
        self.out_files[method_id] = self.output_folder / (method_id + '_out.txt')
        self.exp_files[method_id] = self.output_folder / (method_id + '_exp.txt')

    def set_up_logger(self, method_id, logging_level=logging.INFO, path=None):
        def get_log_path():
            log_name = f"{method_id}_try_{n_try}.log"
            if not path:
                p = self.output_folder / log_name
            else:
                p = path / log_name
            return p

        n_try = 0
        log_path = get_log_path()
        while log_path.exists():
            n_try += 1
            log_path = get_log_path()
        self.log_files[method_id] = log_path
        set_up_logger(logging_level, log_path)


def get_suites(test_dir='test'):
    test_dir = root_path().joinpath(test_dir)

    checking_dirs = {test_dir}
    suites_dir = set()
    while checking_dirs:
        checking_d = checking_dirs.pop()
        sub_dirs = {d for d in checking_d.iterdir() if d.is_dir() and d.stem != '__pycache__'}
        if not sub_dirs:
            suites_dir.add(checking_d)
        else:
            checking_dirs = checking_dirs.union(sub_dirs)
    suites = {}
    for d in suites_dir:
        tests = unittest.TestLoader().discover(d)
        if tests.countTestCases() > 0:
            parent = d.parent.stem
            suites[f"{parent}.{d.stem}"] = tests
    return suites
