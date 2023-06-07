"""Tests of top-level test run script
These assume we have access to two copies of the reference implementation:
- $$NQCC is the path to the fully implemented compiler
- $$NQCC_PARTIAL is a path to version of the compiler that is implemented
  through chapter 19 but doesn't include register allocation
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Union

from ..regalloc import REGALLOC_TESTS
from ..basic import EXPECTED_RESULTS
from ..tacky.dead_store_elim import STORE_ELIMINATED

ROOT_DIR = Path(__file__).parent.parent.parent
TEST_PATTERN = re.compile("^Ran ([0-9]+) tests", flags=re.MULTILINE)
FAILURE_PATTERN = re.compile("failures=([0-9]+)")


def run_test_script(cmd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        shell=True,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
    )


def get_test_count(
    testrun: Union[subprocess.CalledProcessError, subprocess.CompletedProcess[str]]
) -> int:
    run_output = re.search(TEST_PATTERN, testrun.stderr)
    if not run_output:
        raise RuntimeError(f"Unexpected test output: {testrun.stderr}")

    return int(run_output.group(1))


def get_failure_count(failure: subprocess.CalledProcessError) -> int:
    fail_output = re.search(FAILURE_PATTERN, failure.stderr)
    if not fail_output:
        raise RuntimeError(f"Unexpected test output: {failure.stderr}")

    return int(fail_output.group(1))


class TopLevelTest(unittest.TestCase):
    def test_one_chapter(self) -> None:
        """We can run tests for a single chapter with --latest-only"""
        expected_test_count = len(list((ROOT_DIR / "chapter2").rglob("*.c")))
        try:
            testrun = run_test_script("./test_compiler $NQCC --chapter 2 --latest-only")
        except subprocess.CalledProcessError as err:
            self.fail(f"Test command failed with message {err.stderr}")

        actual_test_count = get_test_count(testrun)
        self.assertEqual(expected_test_count, actual_test_count)

    def test_multiple_chapters_intermediate(self) -> None:
        """We can test through an intermediate stage through multiple chapters"""
        expected_test_count = len(list((ROOT_DIR / "chapter1").rglob("*.c"))) + len(
            list((ROOT_DIR / "chapter2").rglob("*.c"))
        )
        try:
            testrun = run_test_script("./test_compiler $NQCC --chapter 2 --stage parse")
        except subprocess.CalledProcessError as err:
            self.fail(f"Test command failed with message {err.stderr}")

        actual_test_count = get_test_count(testrun)
        self.assertEqual(expected_test_count, actual_test_count)

    def test_regalloc_failure(self) -> None:
        """Partially-completed NQCC fails register allocation tests"""
        expected_test_count = len(
            list((ROOT_DIR / "chapter20/int_only").rglob("*.c"))
        ) + len(list((ROOT_DIR / "chapter20/all_types").rglob("*.c")))
        expected_failure_count = len(REGALLOC_TESTS.keys())
        with self.assertRaises(subprocess.CalledProcessError) as err:
            run_test_script("./test_compiler $NQCC_PARTIAL --chapter 20 --latest-only")
        failure_count = get_failure_count(err.exception)
        test_count = get_test_count(err.exception)
        self.assertEqual(
            expected_failure_count,
            failure_count,
            msg=f"Expected {expected_failure_count} failures but got {failure_count}",
        )
        self.assertEqual(expected_test_count, test_count)

    def test_optimization_success(self) -> None:
        """With optimizations, NQCC passes the chapter 19 tests"""
        expected_test_count = len(list((ROOT_DIR / "chapter19").rglob("*.c")))
        try:
            testrun = run_test_script(
                "./test_compiler $NQCC --chapter 19 --latest-only"
            )

        except subprocess.CalledProcessError as err:
            self.fail(f"Test command failed with message {err.stderr}")
        actual_test_count = get_test_count(testrun)
        self.assertEqual(expected_test_count, actual_test_count)


class BadSourceTest(unittest.TestCase):
    # paths that we'll refer to in setup/teardown
    ret2 = ROOT_DIR / "chapter1/valid/return_2.c"
    ret0 = ROOT_DIR / "chapter1/valid/return_0.c"
    hello_world = ROOT_DIR / "chapter9/valid/arguments_in_registers/hello_world.c"
    dse_relative = Path("chapter19/dead_store_elimination/int_only/simple.c")
    dse = ROOT_DIR / dse_relative

    def setUp(self) -> None:
        # save these to a temporary directory before overwriting them
        self.tmpdir = tempfile.TemporaryDirectory()
        shutil.copy(self.hello_world, self.tmpdir.name)
        shutil.copy(self.ret0, self.tmpdir.name)
        shutil.copy(self.dse, self.tmpdir.name)

        # overwrite hello_world with another file that has same retcode but different stdout
        shutil.copy(self.ret0, self.hello_world)

        # overwrite ret0 with another file with different retcode
        shutil.copy(self.ret2, self.ret0)

        # replace a dead store elimination test w/ a different program that has the same
        # result, but where the dead store can't be eliminated
        expected_retval = EXPECTED_RESULTS[str(self.dse_relative)]["return_code"]
        store_to_elim = STORE_ELIMINATED[self.dse.name]
        with open(
            ROOT_DIR / "chapter19/dead_store_elimination/int_only/simple.c",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                f"""
            int f(int arg) {{
                return arg;
            }}
            int target(void) {{
                int x = {store_to_elim};
                f(x);
                return {expected_retval};
            }}
            int main(void) {{ return target(); }}
            """
            )

    def tearDown(self) -> None:
        """Restore files we overwrote from temporary directory"""
        tmp_path = Path(self.tmpdir.name)
        tmp_ret0 = tmp_path / self.ret0.name
        tmp_helloworld = tmp_path / self.hello_world.name
        tmp_dse = tmp_path / self.dse.name

        shutil.copy(tmp_ret0, self.ret0)
        shutil.copy(tmp_helloworld, self.hello_world)
        shutil.copy(tmp_dse, self.dse)
        self.tmpdir.cleanup()

    def test_bad_retval(self) -> None:
        """Make sure the test fails if retval is different than expected"""

        expected_test_count = len(list((ROOT_DIR / "chapter1").rglob("*.c")))
        with self.assertRaises(subprocess.CalledProcessError) as cpe:
            run_test_script("./test_compiler $NQCC --chapter 1")
        actual_test_count = get_test_count(cpe.exception)
        failure_count = get_failure_count(cpe.exception)
        self.assertEqual(actual_test_count, expected_test_count)
        self.assertEqual(1, failure_count)

    def test_bad_stdout(self) -> None:
        """Make sure test fails if stdout is different than expected"""

        expected_test_count = len(list((ROOT_DIR / "chapter9").rglob("*.c"))) - len(
            list((ROOT_DIR / "chapter9").rglob("**/extra_credit/*.c"))
        )
        with self.assertRaises(subprocess.CalledProcessError) as cpe:
            run_test_script("./test_compiler $NQCC --chapter 9 --latest-only")
        actual_test_count = get_test_count(cpe.exception)
        failure_count = get_failure_count(cpe.exception)
        self.assertEqual(actual_test_count, expected_test_count)
        self.assertEqual(1, failure_count)

    def test_optimization_failure(self) -> None:
        """Test fails if code hasn't been optimized as expected"""
        expected_test_count = len(
            list((ROOT_DIR / "chapter19/dead_store_elimination").rglob("*.c"))
        )

        with self.assertRaises(subprocess.CalledProcessError) as err:
            run_test_script(
                "./test_compiler $NQCC --chapter 19 --eliminate-dead-stores --latest-only"
            )
        failure_count = get_failure_count(err.exception)
        test_count = get_test_count(err.exception)
        self.assertEqual(
            1,
            failure_count,
            msg=f"Expected 1 failure but got {failure_count}",
        )
        self.assertEqual(expected_test_count, test_count)

    def test_intermediate(self) -> None:
        """Changed code shouldn't impact intermediate stages"""
        expected_test_count = len(list((ROOT_DIR / "chapter1").rglob("*.c")))
        try:
            testrun = run_test_script("./test_compiler $NQCC --chapter 1 --stage parse")
        except subprocess.CalledProcessError as err:
            self.fail(f"Test command failed with message {err.stderr}")

        actual_test_count = get_test_count(testrun)
        self.assertEqual(expected_test_count, actual_test_count)
