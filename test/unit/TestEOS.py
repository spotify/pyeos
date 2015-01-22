# Copyright 2014 Spotify AB. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import unittest

from pyEOS import EOS
import pyEOS.exceptions as exceptions

import config

class TestEOS(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.device = EOS(config.hostname, config.username, config.password, config.use_ssl)
        cls.device.open()

        with open(config.config_file_1, 'r') as f:
            cls.config_1 = f.readlines()

    @classmethod
    def tearDownClass(cls):
        cls.device.close()

    def test_dynamic_show_command(self):
        lldp = self.device.show_lldp_neighbors()
        self.assertGreater(len(lldp), 0)

    def test_dynamic_show_command_format_text(self):
        lldp = self.device.show_lldp_neighbors(format='text')['output']
        self.assertGreater(len(lldp), 0)

    def test_dynamic_show_command_unconverted(self):
        routes = self.device.show_ip_route(auto_format=True)['output']
        self.assertGreater(len(routes), 0)

    def test_dynamic_show_command_raises_unconverted(self):
        self.assertRaises(exceptions.CommandUnconverted, self.device.show_ip_route)

    def test_wrong_command(self):
        self.assertRaises(exceptions.CommandError, self.device.show_ip_rout)

    def test_arbitrary_command(self):
        output = self.device.run_commands(['dir /all'])[1]['messages'][0]
        self.assertGreater(len(output), 0)

    def test_loading_config(self):
        self.device.load_candidate_config(filename=config.config_file_1)
        self.device.replace_config()
        diff = self.device.compare_config()
        self.assertEqual(len(diff), 0)

    def test_loading_modified_config_and_diff(self):
        self.device.load_candidate_config(filename=config.config_file_2)
        diff = self.device.compare_config()
        self.assertGreater(len(diff), 0)

    def test_loading_modified_config_replace_config_and_rollback(self):
        self.device.load_candidate_config(filename=config.config_file_2)
        orig_diff = self.device.compare_config()
        self.device.replace_config()
        replace_config_diff = self.device.compare_config()
        self.device.rollback()
        last_diff = self.device.compare_config()

        result = (orig_diff == last_diff) and ( len(replace_config_diff) == 0 )

        self.assertTrue(result)

    def test_get_interface_config(self):
        self.device.load_running_config()
        interface = self.device.running_config['interface Ethernet2']
        self.assertGreater(len(interface), 0)