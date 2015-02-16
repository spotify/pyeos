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

from jsonrpclib import Server
from jsonrpclib import ProtocolError
from config import EOSConf

import exceptions


class EOS:
    def __init__(self, hostname, username, password, use_ssl=True):
        """
        Represents a device running EOS.

        The object will contain the following interesting attributes:

        * **running_config** - The configuration retrieved from the device using the method load_running_config
        * **candidate_config** - The configuration we desire for the device. Can be populated using the method load_candidate_config

        :param hostname: IP or FQDN of the device you want to connect to
        :param username: Username
        :param password: Password
        :param use_ssl: If set you True we will connect to the eAPI using https, otherwise http will be used
        """
        self.hostname = hostname
        self.username = username
        self.device = None
        self.password = password
        self.use_ssl = use_ssl
        self.running_config = EOSConf('running')
        self.candidate_config = EOSConf('candidate')
        self.original_config = None

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            cmd = [item.replace('_', ' ')]
            return self.run_commands(cmd, **kwargs)[1]

        if item.startswith('show'):
            return wrapper
        else:
            raise AttributeError("type object '%s' has no attribute '%s'" % (self.__class__.__name__, item))

    def open(self):
        """
        Opens the connection with the device.
        """
        if self.use_ssl:
            url = 'https://%s:%s@%s/command-api' % (self.username, self.password, self.hostname)
        else:
            url = 'http://%s:%s@%s/command-api' % (self.username, self.password, self.hostname)

        self.device = Server(url)

    def run_commands(self, commands, version=1, auto_format=False, format='json', timestamps=True):
        """
        This method will run as many commands as you want. The 'enable' command will be prepended automatically so you
        don't have to worry about that.

        :param commands: List of commands you want to run
        :param version: Version of the eAPI you want to connect to. By default is 1.
        :param auto_format: If set to True API calls not supporting returning JSON messages will be converted automatically to text. By default is False.
        :param format: Format you want to get; 'json' or 'text'. By default is json. This will trigger a CommandUnconverted exception if set to 'json' and auto_format is set to False. It will return text if set to 'json' but auto_format is set to True.
        :param timestamps: This will return some useful information like when was the command executed and how long it took.

        """

        if 'enable' is not commands[0]:
            commands.insert(0, 'enable')

        if auto_format:
            format = 'json'

        try:
            result = self.device.runCmds(
                version=version,
                cmds=commands,
                format=format,
                timestamps=timestamps,
            )
        except ProtocolError as e:
            code = e[0][0]
            error = e[0][1]

            # code 1003 means the command is not yet converted to json
            if code == 1003:
                if auto_format:
                    result = self.device.runCmds(
                        version=version,
                        cmds=commands,
                        format='text',
                        timestamps=timestamps
                    )
                else:
                    raise exceptions.CommandUnconverted(error)
            elif code == 1002:
                raise exceptions.CommandError(error)
            else:
                raise exceptions.UnknownError((code, error))

        return result

    def close(self):
        """
        Dummy, method. Today it does not do anything but it would be interesting to use it to fake closing a connection.

        """
        pass

    def get_config(self, format='json'):
        """

        :param format: Either 'json' or 'text'
        :return: The running configuration of the device.
        """
        if format == 'json':
            return self.run_commands(['sh running-config'])[1]['cmds']
        elif format == 'text':
            return self.run_commands(['sh running-config'], format='text')[1]['output']

    def load_running_config(self):
        """
        Populates the attribute running_config with the running configuration of the device.
        """
        self.running_config.load_config(config=self.get_config(format('text')))

    def load_candidate_config(self, filename=None, config=None):
        """
        Populates the attribute candidate_config with the desired configuration. You can populate it from a file or
        from a string. If you send both a filename and a string containing the configuration, the file takes precedence.

        :param filename: Path to the file containing the desired configuration. By default is None.
        :param config: String containing the desired configuration.
        """

        if filename is not None:
            self.candidate_config.load_config(filename=filename)
        else:
            self.candidate_config.load_config(config=config)

    def compare_config(self):
        """

        :return: A string showing the difference between the running_config and the candidate_config. The running_config is
            loaded automatically just before doing the comparison so there is no neeed for you to do it.
        """

        # We get the config in text format because you get better printability by parsing and using an OrderedDict
        self.load_running_config()
        return self.running_config.compare_config(self.candidate_config)

    def replace_config(self, config=None, force=False):
        """
        Applies the configuration changes on the device. You can either commit the changes on the candidate_config
        attribute or you can send the desired configuration as a string. Note that the current configuration of the
        device is replaced with the new configuration.

        :param config: String containing the desired configuration. If set to None the candidate_config will be used
        :param force: If set to False we rollback changes if we detect a config error.

        """
        if config is None:
            config = self.candidate_config.to_string()

        body = {
            'cmd': 'configure replace terminal: force',
            'input': config
        }
        self.original_config = self.get_config(format='text')
        result = self.run_commands([body])

        if len(result[1]['messages'][0]) == 64:
            return result
        else:
            if not force:
                self.rollback()
            raise exceptions.CommandError(result[1]['messages'][0])

    def rollback(self):
        """
        If used after a commit, the configuration will be reverted to the previous state.
        """
        return self.replace_config(config=self.original_config)