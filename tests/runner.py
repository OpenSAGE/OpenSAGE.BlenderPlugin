# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import sys
import unittest

import coverage

if '--coverage' in sys.argv:
    # Start collecting coverage
    cov = coverage.Coverage()
    cov.start()


loader = unittest.defaultTestLoader

if '--prefix' in sys.argv:
    prefix = sys.argv[sys.argv.index('--prefix') + 1]
    if not prefix == '':
        loader.testMethodPrefix = prefix

loader.testMethodPrefix = 'test_mesh_roundtrip_invalid_triangles'
print(f'running all tests prefixed with \'{loader.testMethodPrefix}\'')

suite = loader.discover('.')
if not unittest.TextTestRunner().run(suite).wasSuccessful():
    exit(1)

if '--coverage' in sys.argv:
    cov.stop()
    cov.xml_report()

    if '--save-html-report' in sys.argv:
        cov.html_report()
