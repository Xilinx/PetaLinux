#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#       Varalaxmi Bingi <varalaxmi.bingi>
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')

# Dict variable to store command line args of petalinux boot
# Each key variable should be unique and should not
# have start with same name
BootParams = {}


def add_bootfile(dict_key, sub_key='Path'):
    ''' Add bootfile param into Dict '''
    def f(arg):
        if arg:
            arg = plnx_utils.argreadlink(arg)
        if arg and dict_key:
            if arg in ('no', 'none'):
                arg = None
            plnx_utils.add_dictkey(BootParams, dict_key, sub_key, arg)
        return arg
    return f


def add_property_to_bootfile(bootparamkey='Path',
                             sub_key='Props', append=False):
    ''' Add the the property to datafile into Dict if argument specified
    if no data files found in dict raise argparse error '''
    def p(arg):
        last_datakey = ''
        for param in BootParams.keys():
            if bootparamkey in BootParams[param].keys():
                last_datakey = param
        if last_datakey:
            if not append:
                BootParams[last_datakey][sub_key] = arg
            else:
                try:
                    BootParams[last_datakey][sub_key] += ', ' + arg
                except KeyError:
                    BootParams[last_datakey][sub_key] = ''
                    BootParams[last_datakey][sub_key] += arg
        else:
            raise argparse.ArgumentTypeError(
                'No data file found to add property: %s' % (arg))
    return p


def AddFpgaBootFile(fpga_arg, proot, xilinx_arch, bootmode, targetcpu=0, prebuilt=''):
    ''' Get the default bit/BIN file path and add it to BootParams dict'''
    sysconf = plnx_vars.SysConfFile.format(proot)
    # Use Prebuilt conf if exists
    if prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
        sysconf = plnx_vars.PreBuildsSysConf.format(proot)
    if_fpga_manager = plnx_utils.get_config_value(
        'CONFIG_SUBSYSTEM_FPGA_MANAGER', sysconf)
    bootfile = ''
    # Skip adding Bit/BIN file if fpgamanager enabled
    if if_fpga_manager == 'y' and xilinx_arch not in ('versal', 'versal-net'):
        logger.info(
            'FPGA manager enabled, skipping bitstream to load in jtag...')
        bootfile = None
    elif not fpga_arg:
        if xilinx_arch not in ('versal', 'versal-net'):
            if prebuilt:
                bootfile = os.path.join(plnx_vars.ImpPreBuildsDir.format(proot),
                                        'download.bit')
                if not os.path.exists(bootfile):
                    bootfile = os.path.join(plnx_vars.PreBuildsImagesDir.format(proot),
                                            'system.bit')
            else:
                bootfile = os.path.join(plnx_vars.BuildImagesDir.format(proot),
                                        'system.bit')
            # FPGA is optional for non versal{-net} devices so give warning and proceed
            if not os.path.exists(bootfile):
                bootfile = None
                logger.warning('Will not program bitstream on the target. '
                        'If you want to program bitstream,')
                logger.warning('Use --fpga <BITSTREAM> option to specify a bitstream.')
            else:
                logger.info('Use Bitstream: %s' % bootfile)
                logger.info('Please use --fpga <BITSTREAM> to specify a bitstream '
                            'if you want to use other bitstream.')
        else:
            bootfile = os.path.join(plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt
                                    else plnx_vars.BuildImagesDir.format(proot),
                                    plnx_vars.BootFileNames['BOOTBIN'])
    if bootfile:
        bootfile = os.path.realpath(bootfile)
        plnx_utils.add_dictkey(BootParams, 'FPGA', 'Path', bootfile)
        # Jtag settings for FPGA
        if bootmode == 'jtag' and xilinx_arch in ('versal', 'versal-net'):
            before_load = 'targets -set -nocase -filter {name =~ "*PMC*"}\n'
            plnx_utils.add_dictkey(
                BootParams, 'FPGA', 'BeforeLoad', before_load)
            if BootParams.get('KERNEL') or prebuilt == 3:
                after_load = 'targets -set -nocase -filter {name =~ "*%s*#%s"}\n' % (
                    'A72' if xilinx_arch == 'versal' else 'A78', targetcpu)
                after_load += 'stop\n'
                plnx_utils.add_dictkey(
                    BootParams, 'FPGA', 'AfterLoad', after_load)


def AddPmuFile(proot, xilinx_arch, bootmode, targetcpu=0, prebuilt=''):
    ''' Add the Default PMU or PLM FW files'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if xilinx_arch in ('versal', 'versal-net'):
        ElfFile = os.path.join(images_dir, plnx_vars.BootFileNames['PLM'])
        plnx_utils.add_dictkey(BootParams, 'PLM', 'Path', ElfFile)
    else:
        ElfFile = os.path.join(images_dir, plnx_vars.BootFileNames['PMUFW'])
        plnx_utils.add_dictkey(BootParams, 'PMUFW', 'Path', ElfFile)
    # Jtag settings for PMUFW
    if bootmode == 'jtag':
        before_load = 'targets -set -nocase -filter {name =~ "*PSU*"}\n'
        before_load += 'mask_write 0xFFCA0038 0x1C0 0x1C0\n'
        before_load += 'targets -set -nocase -filter {name =~ "*MicroBlaze PMU*"}\n'
        before_load += '\nif { [string first "Stopped" [state]] != 0 } {\n'
        before_load += '\tstop\n'
        before_load += '}\n'
        after_load = 'con\n'
        after_load += 'targets -set -nocase -filter {name =~ "*A53*#%s"}\n' % targetcpu
        after_load += 'rst -processor -clear-registers\n'
        plnx_utils.add_dictkey(BootParams, 'PMUFW', 'BeforeLoad', before_load)
        plnx_utils.add_dictkey(BootParams, 'PMUFW', 'AfterLoad', after_load)
    # QEMU settings for PMUFW
    if bootmode == 'qemu':
        before_load = ' -device loader,file='
        if xilinx_arch in ('versal', 'versal-net'):
            plnx_utils.add_dictkey(
                BootParams, 'PLM', 'BeforeLoad', before_load)
        else:
            plnx_utils.add_dictkey(BootParams, 'PMUFW',
                                   'BeforeLoad', before_load)


def AddFsblFile(proot, xilinx_arch, bootmode, targetcpu=0, prebuilt=''):
    ''' Add the FSBL file'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if xilinx_arch in ('zynq', 'zynqmp') and bootmode == 'jtag':
        key = 'FSBL_%s' % xilinx_arch.upper()
        FsblFile = os.path.join(images_dir, plnx_vars.BootFileNames[key])
    elif xilinx_arch == 'zynqmp' and bootmode == 'qemu':
        FsblFile = os.path.join(images_dir, plnx_vars.BootFileNames['PMUROM'])
    elif xilinx_arch in ('versal', 'versal-net') and bootmode == 'qemu':
        FsblFile = os.path.join(images_dir, plnx_vars.BootFileNames['PMCCDO'])
    plnx_utils.add_dictkey(BootParams, 'FSBL', 'Path', FsblFile)
    # JTAG settings for FSBL
    if bootmode == 'jtag':
        before_load = ''
        after_load = 'con\n'
        if xilinx_arch == 'zynq':
            before_load += 'targets -set -nocase -filter {name =~ "arm*#%s"}\n' % targetcpu
            before_load += 'source %s\n' % os.path.join(
                plnx_vars.HWDescDir.format(proot), 'ps7_init.tcl')
            before_load += 'ps7_post_config\n'
            before_load += '\nif { [string first "Stopped" [state]] != 0 } {\n'
            before_load += '\tstop\n'
            before_load += '}\n'
        elif xilinx_arch == 'zynqmp':
            before_load += 'source %s\n' % os.path.join(
                plnx_vars.HWDescDir.format(proot), 'psu_init.tcl')
            after_load += 'after 3000\n'
            after_load += 'stop\n'
            after_load += 'psu_ps_pl_isolation_removal; psu_ps_pl_reset_config\n'
    # QEMU settings for FSBL
    if bootmode == 'qemu':
        before_load = ''
        after_load = ''
        if xilinx_arch == 'zynqmp':
            before_load += ' -kernel '
        elif xilinx_arch in ('versal', 'versal-net'):
            before_load += ' -device loader,addr=0xf0000000,data=0xba020004,data-len=4 -device loader,addr=0xf0000004,data=0xb800fffc,data-len=4 -device loader,file='
            after_load += ',addr=0xf2000000'
    plnx_utils.add_dictkey(BootParams, 'FSBL', 'BeforeLoad', before_load)
    plnx_utils.add_dictkey(BootParams, 'FSBL', 'AfterLoad', after_load)


def AddTfaFile(proot, xilinx_arch, bootmode, prebuilt=''):
    ''' Add TF-A File'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    TfaFile = os.path.join(images_dir, plnx_vars.BootFileNames['TFA'])
    plnx_utils.add_dictkey(BootParams, 'TFA', 'Path', TfaFile)
    before_load = ''
    after_load = ''
    # JTAG settings for TF-A
    if bootmode == 'jtag':
        after_load += 'con\n'
        plnx_utils.add_dictkey(BootParams, 'TFA', 'AfterLoad', after_load)
    # QEMU settings for TF-A
    elif bootmode == 'qemu':
        if xilinx_arch == 'zynqmp':
            before_load += ' -device loader,file='
            after_load += ',cpu-num=0'
            plnx_utils.add_dictkey(
                BootParams, 'TFA', 'BeforeLoad', before_load)
            plnx_utils.add_dictkey(
                BootParams, 'TFA', 'AfterLoad', after_load)


def AddDtbFile(proot, dtb_arg, bootmode, xilinx_arch, prebuilt=''):
    ''' Add DTB File'''
    sysconf = plnx_vars.SysConfFile.format(proot)
    # Use Prebuilt conf if exists
    if prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
        sysconf = plnx_vars.PreBuildsSysConf.format(proot)
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if not dtb_arg or dtb_arg == 'Default':
        DtbFile = os.path.join(images_dir, plnx_vars.BootFileNames['DTB'])
        plnx_utils.add_dictkey(BootParams, 'DTB', 'Path', DtbFile)
    dtb_offset = '0x1000' if xilinx_arch in ('versal', 'versal-net') \
        else '0x100000'
    if xilinx_arch == 'microblaze':
        dtb_offset = '0x1E00000'
    if not BootParams['DTB'].get('LoadAddr'):
        plnx_utils.add_dictkey(BootParams, 'DTB', 'LoadAddr',
                               plnx_utils.append_baseaddr(proot,
                                                          plnx_vars.UbootConfs['DtbOffset'],
                                                          dtb_offset, sysconf))
    # JTAG settings for DTB
    if bootmode == 'jtag':
        if xilinx_arch == 'zynq':
            before_load = 'after 3000\n'
            before_load += 'stop\n'
            plnx_utils.add_dictkey(
                BootParams, 'DTB', 'BeforeLoad', before_load)
    # QEMU settings for DTB
    if bootmode == 'qemu':
        if xilinx_arch in ('zynq', 'microblaze'):
            before_load = ' -dtb '
            plnx_utils.add_dictkey(
                BootParams, 'DTB', 'BeforeLoad', before_load)
        if xilinx_arch == 'zynqmp':
            before_load = ' -device loader,file='
            after_load = ',addr=%s,force-raw=on ' % (BootParams['DTB'].get('LoadAddr'))
            plnx_utils.add_dictkey(
                BootParams, 'DTB', 'BeforeLoad', before_load)
            plnx_utils.add_dictkey(
                BootParams, 'DTB', 'AfterLoad', after_load)


def AddUbootFile(proot, uboot_arg, xilinx_arch, targetcpu, bootmode, prebuilt=''):
    ''' Add UBOOT File'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if not uboot_arg or uboot_arg == 'Default':
        UbootFile = os.path.join(images_dir, plnx_vars.BootFileNames['UBOOT'])
        plnx_utils.add_dictkey(BootParams, 'UBOOT', 'Path', UbootFile)
    # JTAG settings for UBOOT
    if bootmode == 'jtag':
        after_load = ''
        before_load = ''
        if xilinx_arch in ('microblaze', 'zynq'):
            after_load += 'con\n'
            if BootParams.get('KERNEL') or prebuilt == 3:
                after_load += 'after 1000; stop\n'
        if xilinx_arch == 'microblaze':
            before_load += 'after 2000\n'
            before_load += 'targets -set -nocase -filter {name =~ "microblaze*#%s"}\n' % targetcpu
            before_load += 'if { [string first "Stopped" [state]] != 0 } {\n'
            before_load += '\tstop\n'
            before_load += '}\n'
        plnx_utils.add_dictkey(BootParams, 'UBOOT', 'BeforeLoad', before_load)
        plnx_utils.add_dictkey(BootParams, 'UBOOT', 'AfterLoad', after_load)
    # QEMU settings for UBOOT
    if bootmode == 'qemu':
        before_load = ''
        if xilinx_arch in ('zynq', 'microblaze'):
            before_load = ' -kernel '
        elif xilinx_arch == 'zynqmp':
            before_load = ' -device loader,file='
        plnx_utils.add_dictkey(BootParams, 'UBOOT', 'BeforeLoad', before_load)


def AddKernelFile(proot, kernel_arg, sys_arch, xilinx_arch, bootmode, prebuilt=''):
    ''' Add KERNEL File'''
    sysconf = plnx_vars.SysConfFile.format(proot)
    # Use Prebuilt conf if exists
    if prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
        sysconf = plnx_vars.PreBuildsSysConf.format(proot)
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if not kernel_arg or kernel_arg == 'Default':
        key = 'KIMAGE_%s' % sys_arch.upper()
        if xilinx_arch in ('microblaze', 'zynq') and bootmode == 'qemu':
            key = 'KIMAGE_%s_%s' % (bootmode.upper(), sys_arch.upper())
        KernelFile = os.path.join(images_dir, plnx_vars.BootFileNames[key])
        plnx_utils.add_dictkey(BootParams, 'KERNEL', 'Path', KernelFile)
    if not BootParams['KERNEL'].get('LoadAddr'):
        kernel_offset = '0x0' if sys_arch == 'microblaze' else '0x200000'
        plnx_utils.add_dictkey(BootParams, 'KERNEL', 'LoadAddr',
                               plnx_utils.append_baseaddr(proot,
                                                          plnx_vars.UbootConfs['KernelOffset'],
                                                          kernel_offset, sysconf))
    # JTAG settings for KERNEL
    if bootmode == 'jtag':
        if xilinx_arch in ('versal', 'versal-net'):
            before_load = 'targets -set -nocase -filter {name =~ "*%s*"}\n' % (
                'Versal' if xilinx_arch == 'versal' else 'Versal xcvn3716')
            plnx_utils.add_dictkey(BootParams, 'KERNEL',
                                   'BeforeLoad', before_load)
    # QEMU settings for KERNEL
    if bootmode == 'qemu':
        before_load = ''
        after_load = ''
        if xilinx_arch in ('microblaze', 'zynq'):
            before_load = ' -kernel '
        if xilinx_arch in ('zynqmp', 'versal', 'versal-net'):
            before_load = ' -device loader,file='
            after_load = ',addr=%s,force-raw=on ' % (BootParams['KERNEL'].get('LoadAddr'))
        plnx_utils.add_dictkey(BootParams, 'KERNEL',
                               'BeforeLoad', before_load)
        plnx_utils.add_dictkey(BootParams, 'KERNEL',
                               'AfterLoad', after_load)


def AddRootfsFile(proot, rootfs_file, sys_arch, xilinx_arch, bootmode, prebuilt=''):
    '''Add Rootfs file '''
    sysconf = plnx_vars.SysConfFile.format(proot)
    # Use Prebuilt conf if exists
    if prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
        sysconf = plnx_vars.PreBuildsSysConf.format(proot)
    initramfs_image = plnx_utils.get_config_value(
        'CONFIG_SUBSYSTEM_INITRAMFS_IMAGE_NAME', sysconf)
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if not rootfs_file or rootfs_file == 'Default':
        if initramfs_image.find('initramfs') != -1:
            Rootfs = os.path.join(
                images_dir, plnx_vars.BootFileNames['TINY_RFS_FILE'])
        else:
            Rootfs = os.path.join(
                images_dir, plnx_vars.BootFileNames['RFS_FILE'])
    else:
        Rootfs = rootfs_file
    plnx_utils.add_dictkey(BootParams, 'ROOTFS', 'Path', Rootfs)
    rfs_offset = '0x2E00000' if sys_arch == 'microblaze' else '0x04000000'
    if not BootParams['ROOTFS'].get('LoadAddr'):
        plnx_utils.add_dictkey(BootParams, 'ROOTFS', 'LoadAddr',
                               plnx_utils.append_baseaddr(proot,
                                                          plnx_vars.UbootConfs['RootfsOffset'],
                                                          rfs_offset, sysconf))
    # QEMU settings for ROOTFS
    if bootmode == 'qemu':
        before_load = ''
        after_load = ''
        if xilinx_arch in ('microblaze', 'zynq'):
            before_load = ' -initrd '
        elif xilinx_arch in ('zynqmp', 'versal', 'versal-net'):
            before_load = ' -device loader,file='
            after_load = ',addr=%s,force-raw=on ' % (BootParams['ROOTFS'].get('LoadAddr'))
        plnx_utils.add_dictkey(BootParams, 'ROOTFS',
                               'BeforeLoad', before_load)
        plnx_utils.add_dictkey(BootParams, 'ROOTFS',
                               'AfterLoad', after_load)


def AddBootScriptFile(proot, xilinx_arch, bootscr_arg, bootmode, targetcpu, prebuilt=''):
    '''Add Boot.scr file'''
    sysconf = plnx_vars.SysConfFile.format(proot)
    # Use Prebuilt conf if exists
    if prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
        sysconf = plnx_vars.PreBuildsSysConf.format(proot)
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    BootScrFile = os.path.join(
        images_dir, plnx_vars.BootFileNames['BOOTSCRIPT'])
    if not bootscr_arg or bootscr_arg == 'Default':
        plnx_utils.add_dictkey(BootParams, 'BOOTSCRIPT', 'Path', BootScrFile)
    bootscr_offset = '0x3000000' if xilinx_arch == 'zynq' else '0x20000000'
    if xilinx_arch == 'microblaze':
        memory_size = plnx_utils.get_config_value(
            'CONFIG_SUBSYSTEM_MEMORY_', sysconf,
            'asterisk', '_SIZE=')
        bootscr_offset = hex(int(memory_size, base=16) - 0xE00000)
    if not BootParams['BOOTSCRIPT'].get('LoadAddr'):
        plnx_utils.add_dictkey(BootParams, 'BOOTSCRIPT', 'LoadAddr',
                               plnx_utils.append_baseaddr(proot,
                                                          plnx_vars.UbootConfs['BootScrOffset'],
                                                          bootscr_offset, sysconf))
    # JTAG settings for BOOT.SCR
    if bootmode == 'jtag':
        if xilinx_arch != 'zynqmp':
            after_load = ''
            if xilinx_arch in ('versal', 'versal-net'):
                after_load += 'targets -set -nocase -filter {name =~ "*%s*#%s"}\n' % (
                    'A72' if xilinx_arch == 'versal' else 'A78', targetcpu)
            after_load += 'con'
            plnx_utils.add_dictkey(
                BootParams, 'BOOTSCRIPT', 'AfterLoad', after_load)
    # QEMU settings for BOOT.SCR
    if bootmode == 'qemu':
        before_load = ''
        after_load = ''
        before_load += ' -device loader,file='
        after_load += ',addr=%s,force-raw=on ' % (BootParams['BOOTSCRIPT'].get('LoadAddr'))
        plnx_utils.add_dictkey(BootParams, 'BOOTSCRIPT',
                               'BeforeLoad', before_load)
        plnx_utils.add_dictkey(BootParams, 'BOOTSCRIPT',
                               'AfterLoad', after_load)


def ValidateFiles(bootmode):
    '''Error out if file doesnot exists'''
    for ParamKey in BootParams.keys():
        KeyPath = BootParams[ParamKey].get('Path')
        if KeyPath == 'Default':
            plnx_utils.add_dictkey(BootParams, ParamKey, 'Path', None)
            continue
        if KeyPath and not os.path.exists(KeyPath):
            plnx_utils.CheckFileExists(
                KeyPath, 'Failed to boot %s, ' % bootmode)
