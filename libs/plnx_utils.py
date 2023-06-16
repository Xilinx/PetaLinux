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
from common_utils import *
import bitbake_utils


def is_hwflow_sdt(proot):
    '''Determine if the project configured with SDT or XSA'''
    metadata_file = os.path.join(proot, '.petalinux', 'metadata')
    hdf_ext = get_config_value('HDF_EXT', metadata_file)
    if hdf_ext == 'dts':
        hdf_ext = 'sdt'
    return hdf_ext


def get_plnx_projects_from_bsp(source):
    '''Get the Projects from BSP tar ball'''
    contents_cmd = 'tar --exclude="*/*/*" -tzf "%s"' % (source)
    contents, stderr = runCmd(contents_cmd, os.getcwd(), shell=True)
    projects = []
    for content in contents.split():
        project_name = content.split('/')[0]
        projects.append(project_name) if project_name not in projects else ''

    real_proj = []
    for p in projects:
        if os.path.join(p, '.petalinux') in contents:
            real_proj.append(p)

    return real_proj


def exit_not_plnx_project(proot):
    '''Check the proot is valide or not by checking .petalinux directory'''
    workingdir = os.getcwd()
    parentdir = ''
    if proot:
        proot = os.path.realpath(proot)
    else:
        while True:
            if os.path.exists(os.path.join(workingdir, '.petalinux')):
                proot = workingdir
                if bool(re.search(r"\s", proot)):
                    logger.error('Your project directory %s includes space.'
                                 'PetaLinux project directory should not include space.' % (proot))
                    sys.exit(255)
                return proot
            parentdir = os.path.dirname(workingdir)
            if parentdir == workingdir:
                break
            workingdir = parentdir
        logger.error(
            'You are not inside a PetaLinux project. Please specify a PetaLinux project!')
        sys.exit(255)

    if not os.path.exists(os.path.join(proot, '.petalinux')):
        logger.error('"%s" is not a valid PetaLinux project.'
                     'Please create a project with petalinux-create -t project first!' % (proot))
        sys.exit(255)

    if bool(re.search(r"\s", proot)):
        logger.error('Your project directory %s includes space.'
                     'PetaLinux project directory should not include space.' % (proot))
        sys.exit(255)
    return proot


def petalinux_version_check(proot):
    '''PetaLinux version check'''
    metadata_file = os.path.join(proot, '.petalinux', 'metadata')
    CreateFile(metadata_file)
    proj_version = get_config_value('PETALINUX_VER', metadata_file)
    petalinux_ver = os.environ.get('PETALINUX_VER', '')
    if not proj_version:
        update_config_value('PETALINUX_VER', petalinux_ver, metadata_file)
    elif petalinux_ver != proj_version:
        logger.warning(
            'Your PetaLinux project was last modified by PetaLinux SDK version: "%s"' % (proj_version))
        logger.warning(
            'however, you are using PetaLinux SDK version: "%s"' % (petalinux_ver))
        if os.environ.get('PLNX_IGNORE_VER_CHK', ''):
            logger.warning('PLNX_IGNORE_VER_CHK is set, skip version checking')
            return True
        userchoice = input(
            'Please input "y/Y" to continue. Otherwise it will exit![n]')
        if userchoice in ['y', 'Y', 'yes', 'Yes', 'YEs', 'YES']:
            update_config_value('PETALINUX_VER', petalinux_ver, metadata_file)
            return True
        else:
            return False
    return True


def get_soc_variant(proot):
    '''Read SOC_VARIANT from config'''
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    variant = get_config_value('CONFIG_SUBSYSTEM_VARIANT_',
                               sysconf, 'choice', '=y').lower()
    return variant


def get_system_arch(proot):
    '''Read arch from config'''
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    arch = get_config_value('CONFIG_SUBSYSTEM_ARCH_',
                            sysconf, 'choice', '=y').lower()
    return arch


def get_xilinx_arch(proot):
    '''Read xilinx_arch from config'''
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    xilinx_arch = get_config_value('CONFIG_SYSTEM_',
                                   sysconf, 'choice', '=y').lower()
    if xilinx_arch == 'versal':
        soc_variant = get_soc_variant(proot)
        if soc_variant == 'versalnet':
            xilinx_arch = 'versal-net'
    return xilinx_arch


def get_buildtools_path(Type=''):
    '''Return buildtools path from tool'''
    petalinux = os.environ.get('PETALINUX', '')
    yocto_path = os.path.join(petalinux, 'components', 'yocto')
    if Type == 'extended':
        return os.path.join(yocto_path, 'buildtools_extended',
                            'environment-setup-x86_64-petalinux-linux')
    else:
        return os.path.join(yocto_path, 'buildtools',
                            'environment-setup-x86_64-petalinux-linux')


def get_yocto_path(proot, arch):
    '''Return yocto sdk path and arch'''
    petalinux = os.environ.get('PETALINUX', '')
    yocto_esdkpath = os.path.join(petalinux, 'components', 'yocto', 'source')
    if is_hwflow_sdt(proot) == 'sdt':
        arch = 'aarch64_dt'
    yocto_path = os.path.join(yocto_esdkpath, arch)
    return yocto_path, arch


def get_workspace_path(proot):
    '''Return workspace path'''
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    workspace_path = get_config_value(
        'CONFIG_DEVTOOL_WORKSPACE_LOCATION', sysconf)
    workspace_path = workspace_path.replace('${PROOT}', proot)
    workspace_path = workspace_path.replace('$PROOT', proot)
    return workspace_path


def config_initscripts(proot, sysconf):
    '''Generate the configs for busyboxt, interfaces, wired.network'''
    '''files as per the user defined config values'''
    sysconf_dir = os.path.dirname(sysconf)
    esdk_installdir = os.path.join(proot, 'components', 'yocto')
    poky_core = os.path.join(esdk_installdir, 'layers',
                             'poky', 'meta', 'recipes-core')
    t_interfaces = os.path.join(
        poky_core, 'init-ifupdown', 'init-ifupdown-1.0', 'interfaces')
    t_systemwired = os.path.join(
        poky_core, 'systemd', 'systemd-conf', 'wired.network')
    act_interfaces = os.path.join(sysconf_dir, 'init-ifupdown', 'interfaces')
    act_systemdwired = os.path.join(
        sysconf_dir, 'systemd-conf', 'wired.network')

    ip_addr = get_config_value('CONFIG_SUBSYSTEM_ETHERNET_',
                               sysconf, 'asterisk', '_IP_ADDRESS')
    ip_netmask = get_config_value('CONFIG_SUBSYSTEM_ETHERNET_',
                                  sysconf, 'asterisk', '_IP_NETMASK')
    ip_gateway = get_config_value('CONFIG_SUBSYSTEM_ETHERNET_',
                                  sysconf, 'asterisk', '_IP_GATEWAY')
    ip_dynamic = get_config_value('CONFIG_SUBSYSTEM_ETHERNET_',
                                  sysconf, 'asterisk', '_USE_DHCP')
    eth_manual = get_config_value(
        'CONFIG_SUBSYSTEM_ETHERNET_MANUAL_SELECT', sysconf)
    if ip_dynamic == 'y' or eth_manual == 'y':
        CreateDir(os.path.dirname(act_interfaces))
        CopyFile(t_interfaces, act_interfaces)
        CreateDir(os.path.dirname(act_systemdwired))
        CopyFile(t_systemwired, act_systemdwired)
    else:
        act_interface_str = '''
# /etc/network/interfaces -- configuration file for ifup(8), ifdown(8)
# The loopback interface
auto lo
iface lo inet loopback
#
auto eth0
iface eth0 inet static
	address {0}
	netmask {1}
	gateway {2}
'''
        add_str_to_file(act_interfaces, act_interface_str.format(
            ip_addr, ip_netmask, ip_gateway))
        act_wired_str = '''
[Match]
Type=ether
Name=!veth*
KernelCommandLine=!nfsroot
KernelCommandLine=!ip
[Network]
Address={0}/{1}
Gateway={2}
'''
        cidr_netmask = sum(bin(int(x)).count('1')
                           for x in ip_netmask.split('.'))
        add_str_to_file(act_systemdwired, act_wired_str.format(
            ip_addr, cidr_netmask, ip_gateway))
    busybox_dir = os.path.join(sysconf_dir, 'busybox')
    proot_inetdconf = os.path.join(busybox_dir, 'inetd.conf')
    inetd_conf = os.path.join(esdk_installdir, 'layers', 'meta-petalinux',
                              'recipes-core', 'busybox', 'files', 'inetd.conf')
    if not os.path.exists(proot_inetdconf):
        CreateDir(busybox_dir)
        CopyFile(inetd_conf, proot_inetdconf)
        replace_str_fromdir(busybox_dir, '#telnet', 'telnet')
        replace_str_fromdir(busybox_dir, '#ftp', 'ftp')
        replace_str_fromdir(busybox_dir, '-w /var/ftp/', '-w')


def gen_sysconf_dtsi_file(proot):
    '''Generate sysconf.dtsi file for SDT flow'''
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    sdt_autoconf = os.path.join(proot, 'build', 'conf', 'sdt-auto.conf')
    sdt_machine = get_config_value('MACHINE ', sdt_autoconf).strip()
    dtsi_file = os.path.join(proot, 'build', 'conf',
                             'dts', sdt_machine, 'system-conf.dtsi')
    bootargs = get_config_value('CONFIG_SUBSYSTEM_BOOTARGS_GENERATED', sysconf)
    if not bootargs:
        bootargs = get_config_value('CONFIG_SUBSYSTEM_USER_CMDLINE', sysconf)
    system_conf_bootargs = '''
/*
 * CAUTION: This file is automatically generated by PetaLinux SDK.
 * DO NOT modify this file
 */

/ {{
        chosen {{
                bootargs = "{0}";
                stdout-path = "serial0:115200n8";
        }};
}};
'''
    add_str_to_file(dtsi_file, system_conf_bootargs.format(bootargs))
    eth_ipname = get_config_value(
        'CONFIG_SUBSYSTEM_ETHERNET_', sysconf, 'choice', '_SELECT=y').lower()
    eth_mac = get_config_value(
        'CONFIG_SUBSYSTEM_ETHERNET_', sysconf, 'asterisk', '_MAC').replace(':', ' ')
    system_conf_eth = '''
&{0} {{
	local-mac-address = [{1}];
}};
'''
    if eth_ipname != 'manual':
        add_str_to_file(dtsi_file, system_conf_eth.format(
            eth_ipname, eth_mac), mode='a')
    flash_ipname = get_config_value('CONFIG_SUBSYSTEM_FLASH_IP_NAME', sysconf)
    system_conf_flash = '''
&{0} {{
	#address-cells = <1>;
	#size-cells = <0>;
	flash0: flash@0 {{
		/delete-node/ partition@0;
		/delete-node/ partition@100000;
		/delete-node/ partition@600000;
		/delete-node/ partition@620000;
		/delete-node/ partition@c00000;
'''
    flash_partnode = '''
        partition@{0} {{
			label = "{1}";
			reg = <${2} {3}>;
		}};
'''
    end_symbols = '''\t};\n};
    '''
    if flash_ipname:
        prev_part_offset = '0x0'
        prev_part_size = '0x0'
        add_str_to_file(dtsi_file, system_conf_flash.format(
            flash_ipname), mode='a')
        for num in range(0, 19):
            part_offset = add_offsets(prev_part_offset, prev_part_size)
            part_name = get_config_value(
                'CONFIG_SUBSYSTEM_FLASH_QSPI_BANKLESS_PART%s_NAME' % num, sysconf)
            part_size = get_config_value(
                'CONFIG_SUBSYSTEM_FLASH_QSPI_BANKLESS_PART%s_SIZE' % num, sysconf)
            prev_part_offset = part_offset
            prev_part_size = part_size
            if part_name:
                add_str_to_file(dtsi_file, flash_partnode.format(
                    num, part_name, part_offset, part_size), mode='a')
            else:
                break
        add_str_to_file(dtsi_file, end_symbols, mode='a')


def validate_hwchecksum(proot):
    '''Validate HW file checksum and info user if mismatched with the old one'''
    hw_export_dir = os.path.join(proot, 'project-spec', 'hw-description')
    hw_file = ''
    if os.path.exists(hw_export_dir):
        for _file in os.listdir(hw_export_dir):
            if _file.endswith('.xsa'):
                hw_file = os.path.join(hw_export_dir, _file)
                break
            if _file.endswith('.dts'):
                hw_file = os.path.join(hw_export_dir, _file)
                break
    if not hw_file:
        logger.error('No XSA is found in %s' % hw_export_dir)
        sys.exit(255)
    metadata = os.path.join(proot, '.petalinux', 'metadata')
    hw_checksum_old = get_config_value('HARDWARE_CHECKSUM', metadata)
    hw_path = get_config_value('HARDWARE_PATH', metadata)
    '''Checksum of get-hw-description path stored in metadata file'''
    hw_path_checksum = ''
    if os.path.isfile(hw_path):
        hw_path_checksum = get_filehashvalue(hw_path)
    '''Checksum of project-spec/hw-description'''
    hw_checksum = ''
    if os.path.isfile(hw_file):
        hw_checksum = get_filehashvalue(hw_file)
    validate_chksum = get_config_value('VALIDATE_HW_CHKSUM', metadata)

    if hw_path_checksum and hw_checksum != hw_path_checksum and validate_chksum != '0':
        logger.info('Seems like your hardware design:%s is changed,'
                    '\nplese run "petalinux-config --get-hw-description %s" for updating'
                    % (hw_path, hw_path))
        update_config_value('VALIDATE_HW_CHKSUM', '0', metadata)


def setup_plnwrapper(args, proot, config_target, gen_confargs):
    '''Setting up the PetaLinux wrapper to generate the configs'''
    validate_hwchecksum(proot)
    bitbake_utils.get_yocto_source(proot)
    sysconf = os.path.join(proot, 'project-spec', 'configs', 'config')
    if is_hwflow_sdt(proot) == 'sdt':
        bitbake_utils.get_sdt_setup(proot)
    bitbake_utils.setup_bitbake_env(proot, args.logfile)
    add_layers = False
    if args.command == 'petalinux-config' and args.component != 'rootfs':
        # Not run for petalinux-config -c rootfs
        add_layers = True
    elif args.command != 'petalinux-config':
        # Run for petalinux-!{config}
        add_layers = True

    xilinx_arch = get_xilinx_arch(proot)
    bitbake_utils.run_genmachineconf(
        proot, xilinx_arch, gen_confargs, add_layers, args.logfile)
    if add_layers:
        workspace_path = get_workspace_path(proot)
        logger.info('Generating workspace directory')
        workspace_cmd = 'devtool create-workspace "%s"' % workspace_path
        bitbake_utils.run_bitbakecmd(
            workspace_cmd, proot, logfile=args.logfile, shell=True)
        conf_dir = os.path.join(proot, 'build', 'conf')
        local_conf = os.path.join(conf_dir, 'local.conf')
        remove_str_from_file(local_conf, '^include conf\/petalinuxbsp.conf')
        add_str_to_file(local_conf, 'include conf/petalinuxbsp.conf\n',
                        ignore_if_exists=True, mode='a+')
    config_initscripts(proot, sysconf)

    if is_hwflow_sdt(proot) == 'sdt':
        gen_sysconf_dtsi_file(proot)
