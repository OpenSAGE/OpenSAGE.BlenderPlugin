# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import unittest

def runTestCases(testCases):
    #Until a better solution for knowing if the logger's error count should be used to quit the testing,
    #we are currently saying only 1 is allow per suite at a time (which is likely how it should be anyways)
    assert len(testCases) == 1, "Currently, only one test case per suite is supported at a time"
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCases[0])
    test_result = unittest.TextTestRunner().run(suite)

    #See XPlane2Blender/tests.py for documentation. The strings must be kept in sync!
    return_string = "RESULT: After {testsRun} tests got {errors} errors, {failures} failures, and {skipped} skipped"\
        .format(testsRun=test_result.testsRun,
                errors=len(test_result.errors),
                failures=len(test_result.failures),
                skipped=len(test_result.skipped))
    print(return_string)
