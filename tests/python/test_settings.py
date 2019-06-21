import unittest
import shutil
import tempfile
import os
import copy
from dragonfly.settings import SettingsManager


class SettingsTest(unittest.TestCase):
    DEFAULTS = [('setting1', 36)]

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_initial_creation(self):
        manager = SettingsManager(self.test_dir, self.DEFAULTS)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, manager.SETTINGS_FILENAME)))

    def test_defaults_get_added(self):
        manager = SettingsManager(self.test_dir, self.DEFAULTS)
        manager.load()
        self.assertIn('setting1', manager.settings)
        self.assertEqual(36, manager.settings['setting1'])

    def test_save(self):
        manager = SettingsManager(self.test_dir, self.DEFAULTS)
        manager.load()
        settings = copy.copy(manager.settings)
        settings['setting1'] = 20

        manager.save(settings)
        manager.settings = None

        manager.load()
        self.assertDictEqual(settings, manager.settings)
