# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import unittest
import coverage
import sys

#Start collecting coverage
cov = coverage.Coverage()
cov.start()

#Until a better solution for knowing if the logger's error count should be used to quit the testing,
#we are currently saying only 1 is allow per suite at a time (which is likely how it should be anyways)
suite = unittest.defaultTestLoader.discover('.')
if not unittest.TextTestRunner().run(suite).wasSuccessful():
    exit(1)

cov.stop()
cov.xml_report()

if '--save-html-report' in sys.argv:
    cov.html_report()