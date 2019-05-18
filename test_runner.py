import argparse
import importlib
import sys
import unittest

from config import root_path
from test.setup import get_suites, MeldInteractiveTestResult

global DEFAULT_OUTPUT_FOLDER
global DEFAULT_INPUT_FOLDER


class ArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(2)


if __name__ == '__main__':
    parser = ArgParser(description='test file-converter')
    parser.add_argument('test',
                        help=f"Test a/all test suite(s) or a specific test cases inside the test folder",
                        type=str)
    parser.add_argument('--verbosity', choices=[1, 2], help=f"Test verbosity (default 2)", type=int, default=2)
    parser.add_argument('--interactive', help='Interactive testing with meld (default False)', action='store_true')
    parser.add_argument('--folder', help='Test folder (e.g: test/sub_test) (default test)', type=str, default='test')

    args = parser.parse_args()

    t_suites = get_suites(args.folder)

    DEFAULT_INPUT_FOLDER = root_path().joinpath(args.folder) / 'io' / 'in'
    DEFAULT_OUTPUT_FOLDER = root_path().joinpath(args.folder) / 'io' / 'out'
    DEFAULT_INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    if args.interactive:
        result_class = MeldInteractiveTestResult
    else:
        result_class = unittest.TextTestResult
    runner = unittest.TextTestRunner(verbosity=args.verbosity, resultclass=result_class)

    final_res = False
    if args.test:
        if args.test == 'all':
            results = set()
            for s in t_suites:
                results.add(runner.run(t_suites[s]).wasSuccessful())
            final_res = all(results)
        else:
            if args.test in list(t_suites.keys()):
                final_res = runner.run(t_suites[args.test]).wasSuccessful()
            else:
                try:
                    test_path = args.test.split('.')
                    module = importlib.import_module('.'.join(test_path[:-1]))
                    test_case_class = getattr(module, test_path[-1])
                    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_case_class)
                    final_res = runner.run(suite).wasSuccessful()
                except ValueError:
                    sys.stderr.write(f"error: Suite or test case {args.test} not found. "
                                     f"The suite are the sub-folder of testing folder among {list(t_suites.keys())}\n")
                    parser.print_help()
        if not final_res:
            sys.exit("Some tests failed")
