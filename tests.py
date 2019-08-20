import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time

def main(argv=None)->int:
    exit_code = 0

    TEST_RESULTS_REGEX = re.compile(r"RESULT: After (?P<testsRun>\d+) tests got (?P<errors>\d+) errors, (?P<failures>\d+) failures, and (?P<skipped>\d+) skipped")


    total_testsCompleted, total_errors, total_failures, total_skipped = (0,) * 4
    timer_start = time.perf_counter()

    def printTestBeginning(text):
        # Why the hex escapes? So we don't fold our own code!
        print(("\x2F*=== " + text + " ").ljust(75, '=')+'\x7B\x7B\x7B')

    def printTestEnd():
        print(('=' *75)+"}}}*/")

    exit_code = 0
    for root, dirs, files in os.walk('./tests'):
        filtered_files = list(filter(lambda file: file.endswith('.test.py'), files))
        if exit_code != 0:
            break

        for pyFile in filtered_files:
            if exit_code != 0:
                break

            pyFile = os.path.join(root, pyFile)
            blendFile = pyFile.replace('.py', '.blend')

    print((
        "FINAL RESULTS: {total_testsCompleted} {test_str} completed,"
        " {total_errors} errors,"
        " {total_failures} failures,"
        " {total_skipped} skipped. Finished in {total_seconds:.4f} seconds"
        ).format(
            total_testsCompleted = total_testsCompleted,
            test_str = "test case" if total_testsCompleted == 1 else "tests cases",
            total_errors   = total_errors,
            total_failures = total_failures,
            total_skipped  = total_skipped,
            total_seconds  = time.perf_counter() - timer_start
        )
    )
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
