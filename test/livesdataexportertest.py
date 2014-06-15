import unittest
from livesdataexporter import LivesDataExporter
from datetime import date, timedelta
import mongolab
import os
import shutil


class LivesDataExporterTestCase(unittest.TestCase):
    def setUp(self):
        test_data_dir = os.path.join(os.path.dirname(__file__), "testLivesData")

        try:
            print "cleaning out export dir"
            shutil.rmtree(test_data_dir)
        except OSError:
            print "nothing to clean out"

        collection = mongolab.connect().va
        self.lives = LivesDataExporter(collection, 'Norfolk', test_data_dir)


class Metadata(LivesDataExporterTestCase):
    def runTest(self):
        md = self.lives.metadata
        self.assertIsInstance(md, dict)
        self.assertEqual(md["path"], "lives-file/Norfolk")
        self.assertEqual(md["available"], False)


class HasResults(LivesDataExporterTestCase):
    def runTest(self):
        has_results = self.lives.has_results
        self.assertTrue(has_results)


class IsStale(LivesDataExporterTestCase):
    def runTest(self):
        is_stale = self.lives.is_stale
        self.assertTrue(is_stale)


class IsStaleWithFakedStaleData(LivesDataExporterTestCase):
    def runTest(self):
        # pretend like it was written 2 days ago
        last_written = date.today() - timedelta(days=2)
        self.lives.metadata["last_written"] = last_written.strftime("%c")
        self.lives.save_metadata()

        is_stale = self.lives.is_stale
        self.assertTrue(is_stale)


class IsStaleWithFakedFreshData(LivesDataExporterTestCase):
    def runTest(self):
        # pretend like it was last written today
        last_written = date.today()
        self.lives.metadata["last_written"] = last_written.strftime("%c")
        self.lives.save_metadata()

        is_stale = self.lives.is_stale
        self.assertFalse(is_stale)


class WriteLock(LivesDataExporterTestCase):
    def runTest(self):
        is_writing = self.lives.is_writing
        self.assertFalse(is_writing)


class WriteLockWhileWriting(LivesDataExporterTestCase):
    def runTest(self):
        # pretend like we're writing
        self.lives.set_write_lock()

        is_writing = self.lives.is_writing
        self.assertTrue(is_writing)

# class WriteFile(LivesDataExporterTestCase):
#     def runTest(self):
#         self.lives.write_file()





