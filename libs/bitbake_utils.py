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

logger = logging.getLogger('PetaLinux')

scripts_path = os.path.dirname(os.path.realpath(__file__))
libs_path = scripts_path + '/libs'
sys.path = sys.path + [libs_path]
import plnx_utils


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


def env_source_scriptname(arch):
    '''Return the yocto envronment file name'''
    env_prefix = 'environment-setup'
    env_arch = {
        'aarch64': 'cortexa72-cortexa53-xilinx-linux',
        'arm': 'cortexa9t2hf-neon-xilinx-linux-gnueabi',
        'microblaze': 'microblazeel-v11.0-bs-cmp-re-mh-div-xilinx-linux'
    }
    return '%s-%s' % (env_prefix, env_arch[arch])


def get_bitbake_env(proot, logfile):
    '''Get the bitbake environment setup command to'''
    '''run before bitbake command'''
    esdk_installdir = os.path.join(proot, 'components', 'yocto')
    sysconfig_file = os.path.join(proot, 'project-spec', 'configs', 'config')
    arch = plnx_utils.get_system_arch(proot)
    env_scirpt = env_source_scriptname(arch)
    buildtools_ext = plnx_utils.get_config_value(
        'CONFIG_YOCTO_BUILDTOOLS_EXTENDED', sysconfig_file)
    source_cmd = 'unset LD_LIBRARY_PATH;'
    source_cmd += 'source %s &>> %s;' % (
        os.path.join(esdk_installdir, env_scirpt), logfile)
    if buildtools_ext == 'y':
        source_cmd += 'source %s;' % plnx_utils.get_buildtools_path('extended')
    else:
        source_cmd += 'source %s;' % plnx_utils.get_buildtools_path()
    source_cmd += 'source %s &>> %s;' % (os.path.join(
        esdk_installdir, 'layers', 'poky', 'oe-init-build-env'), logfile)
    return source_cmd


def setup_bitbake_env(proot, logfile):
    '''Copy esdk conf files into build directory and remove'''
    '''EXTRA_IMAGE_FEATURES from local.conf file and pre env '''
    '''setup for PetaLinux'''
    esdk_installdir = os.path.join(proot, 'components', 'yocto')
    conf_dir = os.path.join(proot, 'build', 'conf')
    bblayers_conf = os.path.join(conf_dir, 'bblayers.conf')
    local_conf = os.path.join(conf_dir, 'local.conf')

    conf_generated = False
    if os.path.exists(bblayers_conf) and os.path.exists(local_conf):
        conf_generated = True

    source_cmd = get_bitbake_env(proot, logfile)
    plnx_utils.runCmd(source_cmd, proot, shell=True)
    if not conf_generated:
        plnx_utils.CopyDir(os.path.join(esdk_installdir, 'conf'), conf_dir)
        plnx_utils.RemoveFile(os.path.join(conf_dir, 'devtool.conf'))
        plnx_utils.remove_str_from_file(
            local_conf, '^EXTRA_IMAGE_FEATURES(.*)')
        plnx_utils.remove_str_from_file(local_conf, '^SSTATE_MIRRORS(.*)')
        plnx_utils.remove_str_from_file(
            local_conf, '^include conf\/plnxbuild.conf')
        plnx_utils.remove_str_from_file(
            local_conf, '^require conf\/locked-sigs.inc')
        plnx_utils.remove_str_from_file(
            local_conf, '^require conf\/unlocked-sigs.inc')
    plnx_utils.replace_str_fromdir(
        conf_dir, 'SDKBASEMETAPATH = "${TOPDIR}"', 'SDKBASEMETAPATH = "%s"' % (esdk_installdir))
    plnx_utils.add_str_to_file(
        local_conf, 'require conf/locked-sigs.inc\n', ignore_if_exists=True, mode='a+')
    plnx_utils.add_str_to_file(
        local_conf, 'require conf/unlocked-sigs.inc\n', ignore_if_exists=True, mode='a+')


def get_yocto_source(proot):
    '''Install esdk file into components/yocto for the first time'''
    ''' and ask user input if checksum changed from tool to project'''
    arch = plnx_utils.get_system_arch(proot)
    esdk_installdir = os.path.join(proot, 'components', 'yocto')
    yocto_esdkpath, arch = plnx_utils.get_yocto_path(proot, arch)
    if not os.path.exists(yocto_esdkpath):
        logger.error('"%s" is missing in petalinux-tools.'
                     'Installed Petalinux tools are broken. Please reinstall' % yocto_esdkpath)
        sys.exit(255)

    metadata_file = os.path.join(proot, '.petalinux', 'metadata')
    esdk_metadata_file = os.path.join(os.path.dirname(yocto_esdkpath),
                                      '.statistics', arch)
    sysconfig_file = os.path.join(proot, 'project-spec', 'configs', 'config')
    buildtools_ext = plnx_utils.get_config_value(
        'CONFIG_YOCTO_BUILDTOOLS_EXTENDED', sysconfig_file)
    sdk_command = ''
    if buildtools_ext == 'y':
        sdk_command += 'unset LD_LIBRARY_PATH;'
        sdk_command += 'source %s;' % plnx_utils.get_buildtools_path(
            'extended')
    else:
        plnx_utils.check_gcc_version()
    locked_signs = {
        'aarch64': 't-aarch64 t-allarch t-x86-64-aarch64 t-x86-64 t-x86-64-x86-64-nativesdk',
        'arm': 't-allarch t-x86-64-x86-64-nativesdk t-x86-64 t-cortexa9t2hf-neon t-x86-64-arm',
        'microblaze': 't-x86-64 t-allarch t-x86-64-x86-64-nativesdk t-microblazeel-v11.0-bs-cmp-mh-div t-x86-64-microblazeel'
    }
    sdk_cksumproj = plnx_utils.get_config_value('YOCTO_SDK', metadata_file)
    sdk_cksumtool = plnx_utils.get_config_value('BASE_SDK', esdk_metadata_file)
    if sdk_cksumproj and sdk_cksumproj != sdk_cksumtool:
        logger.warning('Your yocto SDK was changed in tool')
        if os.environ.get('PLNX_IGNORE_SRC_CHK', ''):
            logger.warning(
                'PLNX_IGNORE_SRC_CHK is set, skip yocto SDK checking')
            return True
        while True:
            userchoice = input(
                'Please input "y" to proceed the installing SDK into project, "n" to exit:')
            if userchoice in ['y', 'Y', 'yes', 'Yes', 'YEs', 'YES']:
                plnx_utils.RemoveDir(esdk_installdir)
                break
            if userchoice in ['n', 'N', 'no', 'NO', 'No', 'nO']:
                return False
    plnx_utils.CreateDir(esdk_installdir)
    locked_file = os.path.join(esdk_installdir, 'conf', 'locked-sigs.inc')
    bblayers_conf = os.path.join(esdk_installdir, 'conf', 'bblayers.conf')
    if not os.path.exists(bblayers_conf):
        logger.info(
            'Extracting yocto SDK to components/yocto. This may take time!')
        sdk_command += '%s -p -y -d "%s"' % (yocto_esdkpath, esdk_installdir)
        plnx_utils.runCmd(sdk_command, proot, shell=True)

        plnx_utils.remove_str_from_file(
            locked_file, '^SIGGEN_LOCKEDSIGS_TYPES(.*)')
        locked_string = 'SIGGEN_LOCKEDSIGS_TYPES = "%s"' % (locked_signs[arch])
        plnx_utils.add_str_to_file(locked_file, locked_string, mode='a+')
        plnx_utils.remove_str_from_file(
            bblayers_conf, '\${SDKBASEMETAPATH}/workspace')
        plnx_utils.RemoveFile(os.path.join(esdk_installdir, '.devtoolbase'))

    plnx_utils.update_config_value('YOCTO_SDK', sdk_cksumtool, metadata_file)


def append_bitbake_log(proot, logfile):
    '''Append console-latest.log and genmachineconf.log into config/build.log'''
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    gmc_log = os.path.join(proot, 'project-spec',
                           'configs', 'gen-machineconf.log')
    plnxconf = os.path.join(proot, 'build', 'conf', 'plnxtool.conf')
    arch = plnx_utils.get_system_arch(proot)
    tmp_dir = plnx_utils.get_config_value('CONFIG_TMP_DIR_LOCATION', sysconf)
    tmp_dir = tmp_dir.replace('${PROOT}', proot).replace('$PROOT', proot)
    machine_name = plnx_utils.get_config_value('MACHINE ', plnxconf).strip()
    log_dir = os.path.join(tmp_dir, 'log', 'cooker', machine_name)
    if os.path.isfile(gmc_log) and logfile:
        plnx_utils.concate_files(gmc_log, logfile)
    if os.path.exists(log_dir):
        bb_file = os.path.join(log_dir, 'console-latest.log')
        if os.path.isfile(bb_file) and logfile:
            plnx_utils.concate_files(bb_file, logfile)
        return bb_file
    return ''


def get_sdt_setup(proot):
    '''Install SDT SDL file into project'''
    proj_sdt_dir = os.path.join(
        proot, 'components', 'yocto', 'decoupling', 'setup')
    sdt_sdk_file = os.path.join(os.environ.get(
        'PETALINUX', ''), 'components', 'yocto', 'decoupling', 'decouple-prestep.sh')
    dt_proc_script = os.path.join(proj_sdt_dir, 'dt-processor.sh')
    if not os.path.exists(sdt_sdk_file):
        logger.error(
            'No Decouple-preset.sh file found in PetaLinxu installation area')
        sys.exit(255)

    if not os.path.exists(dt_proc_script):
        logger.info('Extracting the decoupling setup sdk into %s' %
                    proj_sdt_dir)
        dt_proc_cmd = 'unset LD_LIBRARY_PATH;'
        dt_proc_cmd += '%s -d %s -p -y' % dt_proc_script
        plnx_utils.runCmd(dt_proc_cmd, proot, shell=True)


def run_genmachineconf(proot, xilinx_arch, config_args, add_layers=False, logfile=None):
    '''Run genmachineconf command to configure the project'''
    if xilinx_arch == 'versal-net':
        xilinx_arch = 'versal'
    extraenv = {'PYTHONDONTWRITEBYTECODE': '1'}
    if add_layers:
        extraenv['UPDATE_USER_LAYERS'] = '1'
    user_rfsconfig = os.path.join(
        proot, 'project-spec', 'meta-user', 'conf', 'user-rootfsconfig')
    hw_args = ''
    if plnx_utils.is_hwflow_sdt(proot) == 'sdt':
        hw_args = '--hw-description %s' % (
            os.path.join(proot, 'project-spec', 'hw-description'))
        hw_args += ' --sdt-sysroot %s' % (os.path.join(
            proot, 'components', 'yocto', 'decoupling', 'setup'))
    else:
        hw_args = '--hw-description %s' % (os.path.join(
            proot, 'project-spec', 'hw-description', 'system.xsa'))
        hw_args += ' --xsct-tool %s' % (os.path.join(
            os.environ.get('PETALINUX', ''), 'tools', 'xsct'))

    genconf_cmd = 'gen-machineconf --soc-family %s %s --output %s \
            --add-rootfsconfig %s --petalinux %s' % (
        xilinx_arch, hw_args, os.path.join(
            proot, 'project-spec', 'configs'), user_rfsconfig,
        config_args)
    run_bitbakecmd(genconf_cmd, proot, builddir=proot,
                   logfile=logfile, extraenv=extraenv, shell=True)


def run_bitbakecmd(command, proot, builddir=None, logfile='/dev/null', extraenv=None, shell=False):
    '''Source the env script and Run bitbake commands'''
    cmd = command
    command = command.split() if not shell else command
    if not builddir:
        os.path.join(proot, 'build')
    source_cmd = get_bitbake_env(proot, logfile)
    command = '%s%s' % (source_cmd, command)
    logger.debug(command)
    env = os.environ.copy()
    if proot and not extraenv:
        extraenv = {'PROOT':  proot}
    if extraenv:
        extraenv['PROOT'] = proot
        for k in extraenv:
            env[k] = extraenv[k]
            env['BB_ENV_PASSTHROUGH_ADDITIONS'] = env.get(
                'BB_ENV_PASSTHROUGH_ADDITIONS', '') + ' ' + k
    try:
        output = subprocess.check_call(
            command, env=env, cwd=builddir, shell=shell)
        bb_tasklog = append_bitbake_log(proot, logfile)
        return bb_tasklog
    except (SystemExit, KeyboardInterrupt):
        append_bitbake_log(proot, logfile)
        sys.exit(255)
    except subprocess.CalledProcessError as e:
        append_bitbake_log(proot, logfile)
        logger.error("Command %s failed with %s" % (cmd, e.output))
        sys.exit(255)
