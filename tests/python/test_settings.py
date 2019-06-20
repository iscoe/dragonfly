import unittest
import shutil
import tempfile
import os
import copy
from dragonfly.settings import SettingsManager


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_initial_creation(self):
        manager = SettingsManager(self.test_dir)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, manager.SETTINGS_FILENAME)))

    def test_defaults_get_added(self):
        manager = SettingsManager(self.test_dir)
        original_default = copy.copy(SettingsManager.DEFAULTS)
        SettingsManager.DEFAULTS.append(('test', True))
        manager.load()
        self.assertIn('test', manager.settings)
        self.assertTrue(manager.settings['test'])
        SettingsManager.DEFAULTS = original_default

    def test_save(self):
        manager = SettingsManager(self.test_dir)
        manager.load()
        settings = copy.copy(manager.settings)
        settings['Column Width'] = 20

        manager.save(settings)
        manager.settings = None

        manager.load()
        self.assertDictEqual(settings, manager.settings)
