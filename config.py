# -*- coding: utf-8 -*-
"""
opengrid

The config module provides support for handling configuration
such as the location to store files, etc.

The configuration is composed from different sources in a
hierarchical fashion:
    * The defaults hard-coded in this file.
    * If it exists: the opengrid.cfg file in the directory
      of this module
    * If it exists: the opengrid.cfg file in the 'current'
      directory
    * If provided: the file given to the constructor
The lower a source is in the list, to more it has precedence.

Not all files must contain all configuration properties. A
configuration file can also overwrite only a subset of the
configuration properties.
"""

from ConfigParser import SafeConfigParser
import inspect
import os


class Config(SafeConfigParser):
    """
    The config class implements the ConfigParser interface.
    More specifically, it inherits from SafeConfigParser.

    See the documentation of SafeConfigParser for the available
    methods.
    """

    def __init__(self, configfile=None):
        SafeConfigParser.__init__(self)
        configfiles = []
        # Add the filename for the config file in the modules
        # directory
        self.opengrid_libdir = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))
        configfiles.append(os.path.join(self.opengrid_libdir, 'opengrid.cfg'))
        # Add the filename for the config file in the 'current' directory
        configfiles.append('opengrid.cfg')
        # Add the filename for the config file passed in
        if configfile:
            configfiles.append(configfile)
        self.read(configfiles)
