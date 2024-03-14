#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import logging
import os
import re
import sys
import bitbake_utils
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')


def config_handler(proot, fragment_path, component, logfile):
    '''Check if fragment.cfg exists and has contents'''
    '''then rename it as user-timestamp.cfg and add it into'''
    '''recipe file as SRC_URI'''
    import datetime
    timestamp = datetime.datetime.now().replace(second=0, microsecond=0)
    timestamp = str(timestamp)
    timestamp = timestamp.replace(' ', '-').replace(':', '-')
    user_fragmentcfg = 'user_%s.cfg' % timestamp

    if fragment_path and not fragment_path.isspace() and \
            os.path.getsize(fragment_path) > 0:
        user_fragmentcfg_path = os.path.join(
            os.path.dirname(fragment_path), str(user_fragmentcfg))
        plnx_utils.RenameFile(fragment_path, user_fragmentcfg_path)
        cmd = 'recipetool appendsrcfile -wW %s %s %s' % (
            plnx_vars.MetaUserDir.format(proot),
            component, user_fragmentcfg_path)
        logger.info(cmd)
        bitbake_utils.run_bitbakecmd(cmd, proot, shell=True, logfile=logfile)


def get_hw_file(hw_file, hw_ext, proot):
    '''Copy HW file into project and rename to system.xsa'''
    plnx_utils.RemoveDir(plnx_vars.HWDescDir.format(proot))
    plnx_utils.CreateDir(plnx_vars.HWDescDir.format(proot))
    plnx_utils.update_config_value('HARDWARE_PATH', hw_file,
                                   plnx_vars.MetaDataFile.format(proot))
    plnx_utils.update_config_value('HDF_EXT', hw_ext,
                                   plnx_vars.MetaDataFile.format(proot))
    if hw_ext == 'sdt':
        plnx_utils.CopyDir(os.path.dirname(hw_file),
                           plnx_vars.HWDescDir.format(proot),
                           exclude='*.xsa')
    else:
        plnx_utils.CopyFile(hw_file, plnx_vars.HWDescDir.format(proot))
        base_filename = os.path.basename(hw_file)
        dest_filename = 'system.xsa'
        if base_filename != dest_filename:
            logger.info('Renaming %s to %s' % (base_filename, dest_filename))
            plnx_utils.RenameFile(
                os.path.join(plnx_vars.HWDescDir.format(proot), base_filename),
                plnx_vars.DefXsaPath.format(proot))
    return True


def validate_hw_file(args, proot):
    '''Validated given HW file or directory and give error'''
    logger.info('Getting hardware description')
    if not os.path.exists(args.get_hw_description):
        logger.error('Unable to get "%s": No Such File or Directory' %
                     args.get_hw_description)
        sys.exit(255)
    hw_file = []
    hw_ext = ''
    if os.path.isfile(args.get_hw_description):
        hw_file.append(args.get_hw_description)
    elif os.path.isdir(args.get_hw_description):
        for _file in os.listdir(args.get_hw_description):
            if _file.endswith('.dts'):
                hw_file.append(os.path.join(args.get_hw_description, _file))
            if _file.endswith('.xsa'):
                hw_file.append(os.path.join(args.get_hw_description, _file))
    if hw_file:
        if len(hw_file) > 1:
            logger.error('More than one ".xsa/.dts" are found in %s'
                         '\nThere should be only one .xsa/.dts file to describe the hardware'
                         'in the Vivado export to SDK directory.' % (args.get_hw_description))
            logger.error('Please use --get-hw-description=<HARDWARE_FILE_PATH>'
                         'to specify the hardware file location.')
            sys.exit(255)
        import pathlib
        hw_file = ''.join(hw_file)
        hw_ext = pathlib.Path(hw_file).suffix
        hw_ext = ''.join(hw_ext.split('.'))
        if hw_ext == 'dts':
            hw_ext = 'sdt'
        old_hw_ext = plnx_utils.is_hwflow_sdt(proot)
        if old_hw_ext and hw_ext != old_hw_ext:
            logger.error('This Project was configured with "%s", you may see issues '
                         'if you use the same project for "%s" flow' % (
                             old_hw_ext, hw_ext))
            sys.exit(255)
        get_hw_file(hw_file, hw_ext, proot)
    else:
        logger.error('No XSA or DTS found in %s' % (args.get_hw_description))
        logger.error(
            'Please use --get-hw-description=<VIVADO_SDK_EXPORT_DIR> to specify \
                    the location of Vivado export to SDK directory.')
        sys.exit(255)
    return True


def config_yocto_component(proot, component, config_target, logfile):
    '''Config yocto components'''
    arch = plnx_utils.get_system_arch(proot)
    if component not in ('project', 'rootfs'):
        logger.info('Configuring: %s' % (component))
        if component in plnx_vars.GUI_Components.keys():
            component = plnx_vars.GUI_Components[component]
        if component in plnx_vars.CMD_Components.keys():
            component = plnx_vars.CMD_Components[component]
        if component == 'bootloader':
            if arch == 'microblaze':
                component = 'virtual/fsboot'
            else:
                component = 'virtual/fsbl'
        bitbake_task = 'menuconfig'
        if config_target == 'silentconfig' or \
                component in plnx_vars.CMD_Components.keys() or \
                component in plnx_vars.CMD_Components.values():
            bitbake_task = 'configure'
        bitbake_cmd = ''
        if component == 'virtual/kernel':
            bitbake_cmd = 'bitbake %s -c %s' % (component, 'cleansstate')
            logger.info(bitbake_cmd)
            bitbake_utils.run_bitbakecmd(
                bitbake_cmd, proot, shell=True, logfile=logfile)

        bitbake_cmd = 'bitbake %s -c %s' % (component, bitbake_task)
        logger.info(bitbake_cmd)
        bitbake_utils.run_bitbakecmd(
            bitbake_cmd, proot, shell=True, logfile=logfile)

        if bitbake_task == 'menuconfig':
            bitbake_cmd = 'bitbake %s -c %s' % (component, 'diffconfig')
            logger.info(bitbake_cmd)
            bb_tasklog = bitbake_utils.run_bitbakecmd(
                bitbake_cmd, proot, shell=True, logfile=logfile)
            lines = []
            fragment_path = ''
            with open(bb_tasklog, 'r') as log_data:
                lines = log_data.readlines()
            for line in lines:
                if re.search('fragment.cfg', line):
                    fragment_path = line.replace(' ', '').strip()
            config_handler(proot, fragment_path, component, logfile)
            if component == 'virtual/kernel':
                bitbake_cmd = 'bitbake %s -c %s' % (component, 'cleansstate')
                logger.info(bitbake_cmd)
                bitbake_utils.run_bitbakecmd(
                    bitbake_cmd, proot, shell=True, logfile=logfile)
            return fragment_path, component
