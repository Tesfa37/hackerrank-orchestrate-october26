import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation import main as evaluator
from evaluation.finalize_reports import validate_ledger, usage_report


class FinalReportTests(unittest.TestCase):
    def fixture(self, directory):
        path=directory/'output.csv'
        row={'case_id':'synthetic','deletion_status':'NOT_APPLICABLE','steps_json':'[]'}
        with path.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,list(row));writer.writeheader();writer.writerow(row)
        ledger={'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'assumption_cases':1,'cases':[{'case_id':'synthetic','assumptions':[{'kind':'synthetic'}],'row':dict(row)}]}
        return path,row,ledger

    def test_ledger_rejects_wrong_csv_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path,row,ledger=self.fixture(Path(temp));path.write_bytes(path.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'checksum'):validate_ledger(path,[row],ledger)

    def test_ledger_rejects_altered_case_even_when_csv_hash_is_correct(self):
        with tempfile.TemporaryDirectory() as temp:
            path,row,ledger=self.fixture(Path(temp));ledger['cases'][0]['row']['deletion_status']='COMPLETE'
            with self.assertRaisesRegex(ValueError,'differs'):validate_ledger(path,[row],ledger)

    def test_ledger_rejects_duplicated_assumption_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            path,row,ledger=self.fixture(Path(temp));ledger['cases']*=2;ledger['assumption_cases']=2
            with self.assertRaisesRegex(ValueError,'duplicated'):validate_ledger(path,[row],ledger)

    def test_generic_evaluation_does_not_overwrite_mandatory_selected_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path,row,ledger=self.fixture(root)
            report=root/'code/evaluation/evaluation_report.md';report.parent.mkdir(parents=True)
            report.write_text('Selected candidate report must remain intact')
            with patch.object(evaluator,'ROOT',root),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(['--predictions',str(path),'--expected',str(path)]),0)
            self.assertEqual(report.read_text(),'Selected candidate report must remain intact')
            self.assertTrue((root/'.cache/evaluation_summary.md').is_file())

    def test_usage_report_uses_measured_usage_and_selected_labels(self):
        rows=[{'case_id':'a','deletion_status':'COMPLETE','steps_json':'[]'}]
        ledger={'csv_sha256':'fixture','requested_cases':1,'cases':[],
                'usage_summary':dict(provider='fixture-provider',model='fixture-model',referenced_calls=2,
                                     cached_results_reused=2,new_calls_this_process=0,production_attempts=3,
                                     attempts_with_unavailable_usage=1,input_tokens=20,output_tokens=4,
                                     thinking_tokens=0,total_tokens=24)}
        report=usage_report(rows,ledger)
        self.assertIn('Selected output: 1/1',report)
        self.assertIn('It contains 1 COMPLETE, 0 INCOMPLETE',report)
        self.assertIn('| Known total tokens | 24 |',report)
        self.assertIn('1 attempts have no provider token usage',report)
