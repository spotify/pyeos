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

from collections import OrderedDict

class EOSConf:

    def __init__(self, name):
        """
        You will probably not have to bother that much about this module yourself as it is usually easier to parse the
        configuration from a file and then use the "load_config" methods on the EOS class to get this object populated.
        However, if you understand how the eAPI handles the configuration in JSON mode you should be able to
        manipulate it in the same way.

        :param name: Name of the configuration
        """
        self.name = name
        self.cmds = OrderedDict()

    def __getitem__(self, item):
        return self.cmds[item]['cmds'].keys()

    def __str__(self):
        return '%s config' % self.name

    def __repr__(self):
        return "EOSConf: %s" % self.__str__()

    @staticmethod
    def _parse_config(config):
        cmds = OrderedDict()
        prev_key = None
        separator = ' '

        if isinstance(config, unicode) or isinstance(config, str):
            config = config.splitlines()

        for line in config:
            line = line.strip('\n')
            if line.strip() == '' or line.startswith('!'):
                pass
            elif line.startswith('      '):
                cmds[prev_key]['cmds'][sub_prev_key]['cmds'][line.strip()] = None
            elif line.startswith('   '):
                sub_prev_key = line.strip()
                cmds[prev_key]['cmds'][sub_prev_key] = dict()
                cmds[prev_key]['cmds'][sub_prev_key]['comments'] = list()
                cmds[prev_key]['cmds'][sub_prev_key]['cmds'] = OrderedDict()
            else:
                prev_key = line
                cmds[line] = dict()
                cmds[line]['comments'] = list()
                cmds[line]['cmds'] = OrderedDict()

        return cmds

    def _load_file(self, filename):
        with open(filename, 'r') as f:
            return self._parse_config(f.readlines())

    def load_config(self, filename=None, config=None):
        """
        Reads the configuration from a file or from a string and loads the object. If you send both a filename and a
        string containing the configuration, the file takes precedence.

        :param filename: Path to the file containing the desired configuration. By default is None.
        :param config: String containing the desired configuration.
        """
        if isinstance(config, dict):
            self.cmds = config
        elif isinstance(config, str) or isinstance(config, unicode):
            self.cmds = self._parse_config(config)
        else:
            self.cmds = self._load_file(filename)

    def to_string(self):
        """

        :return: A string representation of the configuration.
        """
        txt = ''
        for key, value in self.cmds.iteritems():
            txt += '%s\n' % key

            for k in value['cmds'].keys():
                txt += '   %s\n' % k

                for sk in value['cmds'][k]['cmds'].keys():
                    txt += '      %s\n' % sk

        return txt

    def compare_config(self, other):
        """
        This method will compare the self object with the other object. The other object will be the target of the
        comparison.

        :param other: Configuration object you want to do the comparison with.
        :return: A string representation of the changes between the self object and other.
        """
        def _print(action, list, config):
            diff_text = ''
            for cmd in list:
                try:
                    diff_text += '%s %s\n' % (action, cmd)
                    for key in config.cmds[cmd]['cmds'].keys():
                        diff_text += '%s\n' % key
                except AttributeError as e:
                    pass
            return diff_text

        diff_text = ''

        added = set(other.cmds.keys()) - set(self.cmds.keys())
        removed = set(self.cmds.keys()) - set(other.cmds.keys())
        keep = set(other.cmds.keys()) & set(self.cmds.keys())

        diff_text += _print('+', added, other)
        diff_text += _print('-', removed, self)

        for cmd in keep:
            mine = self.cmds[cmd]['cmds']
            sother = other.cmds[cmd]['cmds']

            added = set(sother.keys()) - set(mine.keys())
            removed = set(mine.keys()) - set(sother.keys())
            keep = set(sother.keys()) & set(mine.keys())

            add_text = _print('+', added, sother)
            rem_text = _print('-', removed, mine)

            if add_text != '' or rem_text != '':
                diff_text += '%s\n' % cmd

            diff_text += add_text
            diff_text += rem_text

            for scmd in keep:
                orig = set(mine[scmd]['cmds'].keys())
                cand = set(sother[scmd]['cmds'].keys())

                new = cand - orig
                old = orig - cand

                if len(new) > 0 or len(old) > 0:
                    diff_text +=  "%s\n" % scmd

                    for cmd in new:
                        diff_text +=  "  + %s\n" % scmd

                    for cmd in old:
                        diff_text +=  "  - %s\n" % scmd

        return diff_text