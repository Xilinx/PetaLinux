#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import plnx_vars
import plnx_utils
import logging
import os
import re
import signal
import subprocess
import sys

logger = logging.getLogger('PetaLinux')


def bb_updatevar(recipename, bbvar, value, append=False):
    ''' bb_updatevar will update the bbvar with given value
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
                if not line_s.endswith('"'):
                    start = True
                continue
            elif start:
                if line_s.endswith('"'):
                    start = False
                srcuris_file += ' ' + line_s.split('"')[0]
                continue
            parsed_lines += line
    if append:
        srcuris_file += ' ' + value
    else:
        srcuris_file = value
    srcuris_file = re.sub(r"\s+", ' \\\n\t', srcuris_file)
    parsed_lines += '\n%s = "%s"\n' % (bbvar, srcuris_file)
    with open(recipename, 'w') as file_data:
        file_data.write(parsed_lines)


def validate_pn(pn):
    '''Validate the package name at creation time'''
    reserved_names = ('forcevariable', 'append', 'prepend', 'remove')
    if not re.match('^[0-9a-z-.+]+$', pn):
        return 'Recipe name "%s" is invalid: only characters 0-9, a-z, -, + and . are allowed' % pn
    elif pn in reserved_names:
        return 'Recipe name "%s" is invalid: is a reserved keyword' % pn
    elif pn.startswith('pn-'):
        return 'Recipe name "%s" is invalid: names starting with "pn-" are reserved' % pn
    elif pn.endswith(('.bb', '.bbappend', '.bbclass', '.inc', '.conf')):
        return 'Recipe name "%s" is invalid: should be just a name, not a file name' % pn
    return ''


def validate_srcuri(srcuris):
    '''Validate srcuri and differentiate the local and network uri's and return'''
    localfiles = []
    networkfiles = []
    for srcuri in ' '.join(srcuris).split():
        if srcuri.startswith(('gitsm://', 'git://', 'hg://', 'svn://', 'https:', 'http://')):
            networkfiles.append(srcuri)
        else:
            localfiles.append(srcuri)
            if not os.path.exists(srcuri):
                logger.error('Specified SRCURI: "%s" Doesnot exists' % srcuri)
                sys.exit(255)
    return localfiles, networkfiles


def get_bitbake_env(proot, logfile):
    '''Get the bitbake environment setup command to'''
    '''run before bitbake command'''
    arch = plnx_utils.get_system_arch(proot)
    if plnx_utils.is_hwflow_sdt(proot) == 'sdt':
        if arch == 'arm' or arch == 'aarch64':
            arch = 'aarch64'
    env_scirpt = '%s-%s' % (
        plnx_vars.YoctoEnvPrefix, plnx_vars.YoctoEnvFile[arch]
    )
    source_cmd = 'unset LD_LIBRARY_PATH;'
    source_cmd += 'source %s &>> %s;' % (
        os.path.join(plnx_vars.EsdkInstalledDir.format(proot),
                     env_scirpt), logfile
    )
    source_cmd += 'source %s;' % plnx_vars.BuildToolsEnvPath
    source_cmd += 'source %s %s &>> %s;' % (
        os.path.join(plnx_vars.OeInitEnv.format(proot)),
        plnx_vars.BuildDir.format(proot), logfile)
    return source_cmd


def setup_bitbake_env(proot, logfile):
    '''Copy esdk conf files into build directory and remove'''
    '''EXTRA_IMAGE_FEATURES from local.conf file and pre env '''
    '''setup for PetaLinux'''
    conf_generated = False
    if os.path.exists(plnx_vars.BBLayersConf.format(proot)) and \
            os.path.exists(plnx_vars.LocalConf.format(proot)):
        conf_generated = True

    source_cmd = get_bitbake_env(proot, logfile)
    plnx_utils.runCmd(source_cmd, proot, shell=True)
    if not conf_generated:
        plnx_utils.CopyDir(
            plnx_vars.EsdkConfDir.format(proot),
            plnx_vars.ConfDir.format(proot)
        )
        plnx_utils.RemoveFile(plnx_vars.DevtoolConfFile.format(proot))
        plnx_utils.remove_str_from_file(
            plnx_vars.LocalConf.format(proot),
            'EXTRA_IMAGE_FEATURES(.*)')
        plnx_utils.remove_str_from_file(
            plnx_vars.LocalConf.format(proot),
            'SSTATE_MIRRORS(.*)=(.*)"$')
        plnx_utils.remove_str_from_file(
            plnx_vars.LocalConf.format(proot),
            r'include conf\/plnxbuild.conf')
        plnx_utils.remove_str_from_file(
            plnx_vars.LocalConf.format(proot),
            r'require conf\/locked-sigs.inc')
        plnx_utils.remove_str_from_file(
            plnx_vars.LocalConf.format(proot),
            r'require conf\/unlocked-sigs.inc')
    plnx_utils.replace_str_fromdir(
        plnx_vars.ConfDir.format(proot),
        'SDKBASEMETAPATH = "${TOPDIR}"',
        'SDKBASEMETAPATH = "%s"' % (
            plnx_vars.EsdkInstalledDir.format(proot)))
    plnx_utils.add_str_to_file(
        plnx_vars.LocalConf.format(proot),
        'require conf/locked-sigs.inc\n', ignore_if_exists=True, mode='a+')
    plnx_utils.add_str_to_file(
        plnx_vars.LocalConf.format(proot),
        'require conf/unlocked-sigs.inc\n', ignore_if_exists=True, mode='a+')


def get_yocto_source(proot):
    '''Install esdk file into components/yocto for the first time'''
    ''' and ask user input if checksum changed from tool to project'''
    arch = plnx_utils.get_system_arch(proot)
    yocto_esdkpath, arch = plnx_utils.get_yocto_path(proot, arch)
    if not os.path.exists(yocto_esdkpath):
        logger.error('"%s" is missing in petalinux-tools.'
                     'Installed Petalinux tools are broken. Please reinstall' % yocto_esdkpath)
        sys.exit(255)

    esdk_metadata_file = os.path.join(os.path.dirname(yocto_esdkpath),
                                      '.statistics', arch)
    sdk_command = ''
    plnx_utils.check_gcc_version()
    sdk_cksumproj = plnx_utils.get_config_value(
        'YOCTO_SDK', plnx_vars.MetaDataFile.format(proot))
    sdk_cksumtool = plnx_utils.get_config_value('BASE_SDK', esdk_metadata_file)
    if sdk_cksumproj and sdk_cksumproj != sdk_cksumtool:
        logger.warning('Your yocto SDK was changed in tool')
        if os.environ.get('PLNX_IGNORE_SRC_CHK', ''):
            logger.warning(
                'PLNX_IGNORE_SRC_CHK is set, skip yocto SDK checking')
            return True
        while True:
            userchoice = input(
                'Please input "y" to proceed the installing SDK into project, "n" to use existing yocto SDK:')
            if userchoice in ('y', 'Y', 'yes', 'Yes', 'YEs', 'YES'):
                plnx_utils.RemoveDir(plnx_vars.EsdkInstalledDir.format(proot))
                break
            if userchoice in ('n', 'N', 'no', 'NO', 'No', 'nO'):
                if not os.path.exists(plnx_vars.EsdkInstalledDir.format(proot)):
                    logger.warning('SDK install directory missing in project.'
                                 ' Please input y to install the SDK into project')
                    continue
                else:
                    logger.warning('Not installing the newer yocto SDK as requested by the user, instead using the older yocto SDK')
                    return True
    plnx_utils.CreateDir(plnx_vars.EsdkInstalledDir.format(proot))
    if not os.path.exists(plnx_vars.EsdkBBLayerconf.format(proot)):
        logger.info(
            'Extracting yocto SDK to components/yocto. This may take time!')
        sdk_command += '%s -p -y -d "%s"' % (yocto_esdkpath,
                                             plnx_vars.EsdkInstalledDir.format(proot))
        plnx_utils.runCmd(sdk_command, proot, shell=True)

        plnx_utils.remove_str_from_file(
            plnx_vars.LockedSigsFile.format(
                proot), '^SIGGEN_LOCKEDSIGS_TYPES(.*)'
        )
        locked_string = 'SIGGEN_LOCKEDSIGS_TYPES = "%s"' % (
            plnx_vars.LockedSigns.get(arch, ''))
        plnx_utils.add_str_to_file(
            plnx_vars.LockedSigsFile.format(proot), locked_string, mode='a+')
        plnx_utils.remove_str_from_file(
            plnx_vars.EsdkBBLayerconf.format(proot), r'\${SDKBASEMETAPATH}/workspace')
        plnx_utils.RemoveFile(plnx_vars.DevtoolFile.format(proot))

    plnx_utils.update_config_value(
        'YOCTO_SDK', sdk_cksumtool, plnx_vars.MetaDataFile.format(proot))


def append_bitbake_log(proot, logfile):
    '''Append console-latest.log and genmachineconf.log into config/build.log'''
    tmp_dir = plnx_utils.get_config_value(
        plnx_vars.TmpDirConf, plnx_vars.SysConfFile.format(proot))
    tmp_dir = tmp_dir.replace('${PROOT}', proot).replace('$PROOT', proot)
    machine_name = plnx_utils.get_config_value(
        'MACHINE ', plnx_vars.PlnxToolConf.format(proot)).strip()
    log_dir = os.path.join(tmp_dir, 'log', 'cooker', machine_name)
    if os.path.isfile(plnx_vars.GenMachLogFile.format(proot)) and logfile:
        plnx_utils.concate_files(
            plnx_vars.GenMachLogFile.format(proot), logfile)
    if os.path.exists(log_dir):
        bb_file = os.path.join(log_dir, 'console-latest.log')
        if os.path.isfile(bb_file) and logfile:
            plnx_utils.concate_files(bb_file, logfile)
        return bb_file
    return ''


def run_genmachineconf(proot, xilinx_arch, config_args, add_layers=False, logfile=None):
    '''Run genmachineconf command to configure the project'''
    if xilinx_arch == 'versal-net':
        xilinx_arch = 'versal'
    extraenv = {'PYTHONDONTWRITEBYTECODE': '1',
                'SKIP_BBPATH_SEARCH': '1'}
    if add_layers:
        extraenv['UPDATE_USER_LAYERS'] = '1'
    hw_args = ''
    if plnx_utils.is_hwflow_sdt(proot) == 'sdt':
        hw_args = '--hw-description %s' % (
            plnx_vars.HWDescDir.format(proot))
        hw_args += ' --localconf %s' % (
                plnx_vars.SdtAutoConf.format(proot))
    else:
        hw_args = '--hw-description %s' % (
            plnx_vars.DefXsaPath.format(proot))
        hw_args += ' --xsct-tool %s' % (plnx_vars.XsctPath)

    genconf_cmd = 'gen-machineconf --soc-family %s %s --output %s \
            --add-rootfsconfig %s --petalinux %s' % (
        xilinx_arch, hw_args, plnx_vars.SysConfDir.format(proot),
        plnx_vars.UsrRfsConfig.format(proot),
        config_args)
    plnx_utils.RemoveFile(plnx_vars.SdtAutoConf.format(proot))
    run_bitbakecmd(genconf_cmd, proot, builddir=proot,
                   logfile=logfile, extraenv=extraenv, shell=True)


def run_bitbakecmd(command, proot, builddir=None, logfile='/dev/null',
                   extraenv=None, shell=False, checkcall=True):
    '''Source the env script and Run bitbake commands'''
    cmd = command
    command = command.split() if not shell else command
    if not builddir:
        builddir = os.path.join(proot, 'build')
    source_cmd = get_bitbake_env(proot, logfile)
    command = '%s%s' % (source_cmd, command)
    logger.debug(command)
    env = os.environ.copy()
    if proot and not extraenv:
        extraenv = {'PROOT': proot}
    if extraenv:
        extraenv['PROOT'] = proot
        for k in extraenv:
            env[k] = extraenv[k]
            env['BB_ENV_PASSTHROUGH_ADDITIONS'] = env.get(
                'BB_ENV_PASSTHROUGH_ADDITIONS', '') + ' ' + k
    try:
        if checkcall:
            output = subprocess.check_call(
                command, env=env, cwd=builddir, shell=shell,
                executable='/bin/bash')
            bb_tasklog = append_bitbake_log(proot, logfile)
            return bb_tasklog
        else:
            output, error = plnx_utils.runCmd(command, out_dir=builddir,
                                              extraenv=env, shell=shell)
            bb_tasklog = append_bitbake_log(proot, logfile)
            return output, error
    except (SystemExit, KeyboardInterrupt):
        append_bitbake_log(proot, logfile)
        os.killpg(0, signal.SIGTERM)
    except subprocess.CalledProcessError as e:
        append_bitbake_log(proot, logfile)
        logger.error("Command %s failed" % (cmd))
        sys.exit(255)
