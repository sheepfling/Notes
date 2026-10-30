"""Exercise the generated reports without storing benchmark evidence in Git."""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from typing import Final

from semantics import Capture, ProbeRecord

_SCRIPT_DIR: Final = pathlib.Path(__file__).resolve().parent


class ReportTests(unittest.TestCase):
    """Check semantic serialization and both command-line reports."""

    def test_probe_record_flattens_context_and_capture(self) -> None:
        capture = Capture(status='returned', value=[1, 2, 3], dtype='float64',
                          shape=[3], c_contiguous=True)
        record = ProbeRecord(capture, test='dtype', operation='rotate')
        self.assertEqual(record.to_dict(), {
            'test': 'dtype', 'operation': 'rotate', 'status': 'returned',
            'value': [1, 2, 3], 'dtype': 'float64', 'shape': [3],
            'c_contiguous': True, 'warnings': [],
        })
        failed = ProbeRecord(Capture(status='error', error_type='ValueError',
                                     message='invalid'), test='bad_input')
        self.assertEqual(failed.to_dict()['type'], 'ValueError')
        self.assertNotIn('error_type', failed.to_dict())
    ####

    def test_smoke_reports_are_parseable_and_complete(self) -> None:
        env = os.environ | {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
                            'MKL_NUM_THREADS': '1'}
        with tempfile.TemporaryDirectory() as directory:
            temp = pathlib.Path(directory)
            probe = subprocess.run([sys.executable, str(_SCRIPT_DIR / 'semantics.py')],
                                   cwd=temp, env=env, text=True, capture_output=True, check=True)
            semantic = json.loads((temp / 'semantics.json').read_text())
            self.assertTrue(semantic['passed'])
            self.assertTrue(semantic['diagnostics'])
            self.assertIn('Semantic probes passed', probe.stdout)
            run = subprocess.run([
                sys.executable, str(_SCRIPT_DIR / 'benchmark.py'), '--sizes', '1', '5',
                '--repeats', '1', '--target-seconds', '0.001', '--output', 'result.json',
            ], cwd=temp, env=env, text=True, capture_output=True, check=True)
            report = json.loads((temp / 'result.json').read_text())
            self.assertTrue(report['correctness']['passed'])
            self.assertEqual(len(report['correctness']['checks']), 72)
            self.assertEqual(len(report['results']), 76)
            self.assertEqual(len({row['implementation'] for row in report['results']}), 7)
            self.assertIn('| operation |', run.stdout)
            self.assertIn('| median us/call |', run.stdout)
            self.assertEqual(json.loads(json.dumps(report)), report)
        ####
    ####
####


if __name__ == '__main__':
    unittest.main()
####
