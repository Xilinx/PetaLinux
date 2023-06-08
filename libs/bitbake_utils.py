#!/usr/bin/env python

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import os
import subprocess
import re
import sys
import shutil
import logging

scripts_path = os.path.dirname(os.path.realpath(__file__))
libs_path = scripts_path + '/libs'
sys.path = sys.path + [libs_path]
import plnx_utils

logger = logging.getLogger('PetaLinux')

def bb_updatevar(recipename, bbvar, value, append=False):
    ''' 
    bb_updatevar will update the bbvar with given value
    recipename - bb file path
    bbvar - variable that needs to be update(Ex: SRC_URI)
    value - value for the bbvar
    append - setting this True will append the value to the existing value
    '''
    lines = []
    parsed_lines = ''
    srcuris_file = ''
    if os.path.exists(recipename):
        with open(recipename, 'r') as file_data:
            lines = file_data.readlines()
        start = False
        for line in lines:
            line_s = line.replace('\\', '').strip()
            if line_s.startswith(bbvar):
                srcuris_file += ' ' + line_s.split('"')[1]
                start = True
                continue
            elif start and line_s.endswith('"'):
                srcuris_file += ' ' + line_s.split('"')[0]
                start = False
                continue
            parsed_lines += line
    if append:
        srcuris_file += ' ' + value
    else:
        srcuris_file = ' ' + value
    srcuris_file = re.sub(r"\s+", ' \\\n\t', srcuris_file)
    parsed_lines += '\n%s = "%s"\n' % (bbvar, srcuris_file)
    with open(recipename, 'w') as file_data:
        file_data.write(parsed_lines)


def validate_pn(pn):
    '''Validate the package name at creation time'''
    reserved_names = ['forcevariable', 'append', 'prepend', 'remove']
    if not re.match('^[0-9a-z-.+]+$', pn):
        return 'Recipe name "%s" is invalid: only characters 0-9, a-z, -, + and . are allowed' % pn
    elif pn in reserved_names:
        return 'Recipe name "%s" is invalid: is a reserved keyword' % pn
    elif pn.startswith('pn-'):
        return 'Recipe name "%s" is invalid: names starting with "pn-" are reserved' % pn
    elif pn.endswith(('.bb', '.bbappend', '.bbclass', '.inc', '.conf')):
        return 'Recipe name "%s" is invalid: should be just a name, not a file name' % pn
    return ''


def validate_srcuri(srcuris=[]):
    '''Validate srcuri and differentiate the local and network uri's and return'''
    localfiles = []
    networkfiles = []
    for srcuri in srcuris:
        if srcuri.startswith(('gitsm://', 'git://', 'hg://', 'svn://', 'https:', 'http://')):
            networkfiles.append(srcuri)
        else:
            localfiles.append(srcuri)
            if not os.path.exists(srcuri):
                logger.error('Specified SRCURI: "%s" Doesnot exists' % srcuri)
                sys.exit(255)
    return localfiles, networkfiles


def run_bitbakecmd(cmd, builddir, extraenv=None):
    '''Source the env script and Run bitbake commands'''
    env = os.environ.copy()
    if extraenv:
        for k in extraenv:
            env[k] = extraenv[k]
            env["BB_ENV_PASSTHROUGH_ADDITIONS"] = env["BB_ENV_PASSTHROUGH_ADDITIONS"] + " " + k
            try:
                output = subprocess.check_call(cmd, env=env, cwd=builddir)
                logger.debug(output)
            except subprocess.CalledProcessError as e:
                logger.error("Command %s failed with %s" % (cmd, e.output))
