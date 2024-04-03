#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import sys
import plnx_utils
import plnx_vars
import boot_common


logger = logging.getLogger('PetaLinux')

'''Jtag BootFiles Sequence per platform'''
JtagBootFilesSeq = {
    'microblaze': ['FPGA', 'UBOOT', 'KERNEL',
                   'DTB', 'ROOTFS', 'BOOTSCRIPT'],
    'zynq': ['FPGA', 'FSBL', 'DTB',
             'UBOOT', 'KERNEL', 'ROOTFS', 'BOOTSCRIPT'],
    'zynqmp': ['FPGA', 'PMUFW', 'FSBL',
               'DTB', 'UBOOT', 'KERNEL', 'ROOTFS',
               'BOOTSCRIPT', 'TFA'],
    'versal': ['FPGA', 'UBOOT', 'KERNEL', 'ROOTFS',
               'BOOTSCRIPT'],
    'versal-net': ['FPGA', 'UBOOT', 'KERNEL', 'ROOTFS',
                   'BOOTSCRIPT']
}


def JtagConnect(args):
    '''Connect to the hw_server'''
    ConStr = ''
    if args.before_connect:
        ConStr += '%s\n' % '\n'.join(args.before_connect)
    if args.xsdb_connect:
        ConStr += '%s\n' % args.xsdb_connect
    else:
        ConStr += 'connect -url %s\n' % args.hw_server_url \
            if args.hw_server_url else 'connect\n'
        if args.xilinx_arch not in ('versal', 'versal-net'):
            ConStr += 'for {set i 0} {$i < 20} {incr i} {\n'
            ConStr += '\tif { [ta] != "" } break;\n'
            ConStr += '\tafter 50\n'
            ConStr += '}\n'
    if args.after_connect:
        ConStr += '%s\n' % '\n'.join(args.after_connect)

    return ConStr


def LaunchXsdb(TmpTclFile):
    ''' Source the tcl on xsdb'''
    logger.info('Launching XSDB for file download and boot.')
    logger.info(
        'This may take a few minutes, depending on the size of your image.')
    plnx_utils.runCmd('xsdb %s' % (TmpTclFile),
                      os.getcwd(), shell=True, checkcall=True)


def GenerateTcl(args, BootParams):
    '''Generate the tcl file for the Dictionary data'''
    TclStr = JtagConnect(args)
    for BootParam in JtagBootFilesSeq[args.xilinx_arch]:
        if BootParam in BootParams.keys() and BootParams[BootParam].get('Path'):
            if BootParams[BootParam].get('BeforeLoad'):
                TclStr += BootParams[BootParam].get('BeforeLoad')
            if BootParam == 'FPGA':
                if args.xilinx_arch in ('versal', 'versal-net'):
                    TclStr += 'puts stderr "INFO: Downloading BIN file: %s to the target."\n' % (
                        BootParams[BootParam].get('Path'))
                    fpga_cmd = 'device program'
                else:
                    TclStr += 'puts stderr "INFO: Configuring the FPGA..."\n'
                    TclStr += 'puts stderr "INFO: Downloading bitstream: %s to the target."\n' % (
                        BootParams[BootParam].get('Path'))
                    fpga_cmd = 'fpga'
                TclStr += '%s "%s"\n' % (fpga_cmd,
                                         BootParams[BootParam].get('Path'))

            elif plnx_utils.IsElfFile(BootParams[BootParam].get('Path')):
                TclStr += 'puts stderr "INFO: Downloading ELF file: %s to the target."\n' % (
                    BootParams[BootParam].get('Path'))
                TclStr += 'dow "%s"\n' % BootParams[BootParam].get('Path')

            else:
                if not BootParams[BootParam].get('LoadAddr'):
                    logger.error('No load address provided for non-ELF file: %s' %
                                 BootParams[BootParam].get('Path'))
                    sys.exit(255)
                TclStr += 'puts stderr "INFO: Loading image: %s at %s."\n' % (
                    BootParams[BootParam].get('Path'),
                    BootParams[BootParam].get('LoadAddr'))
                TclStr += 'dow -data %s"%s" %s\n' % (
                                    '-force ' if args.xilinx_arch in ('versal', 'versal-net') else '',
                                    BootParams[BootParam].get('Path'),
                                    BootParams[BootParam].get('LoadAddr'))
            if BootParams[BootParam].get('AfterLoad'):
                TclStr += BootParams[BootParam].get('AfterLoad')
            TclStr += '\n'

    # If --kernel and no ROOTFS given display boot command
    if BootParams.get('KERNEL') and not BootParams.get('ROOTFS'):
        TclStr += 'puts stderr "INFO: Enter booti %s - %s in uboot terminal if auto boot fails"\n' % (
            BootParams['KERNEL'].get('LoadAddr', '0x200000'),
            BootParams['DTB'].get('LoadAddr') if BootParams.get('DTB') else '0x1000')
    TclStr += 'exit\n'

    if args.tcl:
        TclStr += 'puts stderr "INFO: Saving XSDB commands to %s."\n' % args.tcl
        TclStr += 'puts stderr "INFO: You can run \'xsdb %s\' to execute."' % args.tcl
        plnx_utils.add_str_to_file(args.tcl, TclStr)
        logger.plain(TclStr)
    else:
        if args.debug:
            logger.plain(TclStr)
        import tempfile
        filehandle = tempfile.NamedTemporaryFile()
        TmpTclFile = filehandle.name
        plnx_utils.add_str_to_file(TmpTclFile, TclStr)
        LaunchXsdb(TmpTclFile)


def JtagBootSetup(args, proot):
    '''JTAG BootFiles setup.
    Add Each BootFile to the Dictionary based on the platform'''
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)

    if args.targetcluster != '' and args.xilinx_arch == 'versal-net':
        args.targetcpu = '%s.%s' % (args.targetcpu, args.targetcluster)

    # Check directories exists or not
    if args.prebuilt and not os.path.exists(
            plnx_vars.PreBuildsImagesDir.format(proot)):
        logger.error('Failed to Boot --prebuilt %s, %s Directory not found'
                     % (args.prebuilt, plnx_vars.PreBuildsImagesDir.format(proot)))
        sys.exit(255)
    if (args.u_boot or args.kernel) and not args.prebuilt and not os.path.exists(
            plnx_vars.BuildImagesDir.format(proot)):
        logger.error('Failed to Boot, %s Directory not found'
                     % (plnx_vars.BuildImagesDir.format(proot)))
        sys.exit(255)

    # Add Boot Files per platform
    boot_common.AddFpgaBootFile(args.fpga, proot, args.xilinx_arch,
                                args.command, args.targetcpu, args.prebuilt)
    if args.xilinx_arch == 'zynqmp':
        boot_common.AddPmuFile(proot, args.xilinx_arch, args.command,
                               args.targetcpu, args.prebuilt)
        boot_common.AddTfaFile(proot, args.xilinx_arch,
                               args.command, args.prebuilt)
    if args.xilinx_arch in ('zynq', 'zynqmp'):
        boot_common.AddFsblFile(proot, args.xilinx_arch,
                                args.command, args.targetcpu, args.prebuilt)

    if not args.prebuilt == 1:
        AddDTB = False
        if args.xilinx_arch not in ('microblaze', 'versal', 'versal-net'):
            AddDTB = True
        elif args.xilinx_arch == 'microblaze' and (args.prebuilt == 3 or args.kernel):
            AddDTB = True
        if AddDTB:
            boot_common.AddDtbFile(proot, args.dtb, args.command,
                                   args.xilinx_arch, args.prebuilt)
        if args.xilinx_arch not in ('versal', 'versal-net'):
            boot_common.AddUbootFile(
                proot, args.u_boot, args.xilinx_arch, args.targetcpu,
                args.command, args.prebuilt)

    if args.prebuilt == 3 or args.kernel:
        boot_common.AddKernelFile(proot, args.kernel, args.arch, args.xilinx_arch,
                                  args.command, args.prebuilt)
        sysconf = plnx_vars.SysConfFile.format(proot)
        # Use Prebuilt conf if exists
        if args.prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
            sysconf = plnx_vars.PreBuildsSysConf.format(proot)
        rootfs_type = plnx_utils.get_config_value(
            'CONFIG_SUBSYSTEM_ROOTFS_', sysconf, 'choice')
        if rootfs_type == 'INITRD':
            boot_common.AddRootfsFile(
                proot, args.rootfs, args.arch, args.xilinx_arch, args.command, args.prebuilt)
        boot_common.AddBootScriptFile(
            proot, args.xilinx_arch, args.boot_script,
            args.command, args.targetcpu, args.prebuilt)

    # Validate Files
    boot_common.ValidateFiles(args.command)
    # Generate Tcl and load via xsdb
    GenerateTcl(args, boot_common.BootParams)


def JtagBootArgs(jtag_parser):
    jtag_parser.add_argument('--prebuilt', metavar='<BOOT_LEVEL>', type=int, choices=range(1, 4),
                             help='Boot prebuilt images (override all settings).'
                             '\nSupported boot levels 1 to 3'
                             '\n1 - Download FPGA bitstream and FSBL for Zynq, FSBL and PMUFW for ZynqMP'
                             '\n2 - Boot U-Boot only\n3 - Boot Linux Kernel only'
                             )
    jtag_parser.add_argument('--u-boot', '--uboot', type=boot_common.add_bootfile('UBOOT'),
                             nargs='?', default='', const='Default',
                             help='Boot images/linux/u-boot.elf image'
                             '\nif --kernel is specified, --u-boot will not take effect.',
                             )
    jtag_parser.add_argument('--kernel', type=boot_common.add_bootfile('KERNEL'),
                             nargs='?', default='', const='Default',
                             help='Boot images/linux/zImage for Zynq'
                             '\nBoot images/linux/Image for ZynqMP, versal and versal-net.'
                             '\nBoot images/linux/image.elf for MicroBlaze'
                             )
    jtag_parser.add_argument('--fpga', '--bitstream', type=boot_common.add_bootfile('FPGA'),
                             nargs='?', default='', const='',
                             help='Programs the hardware with the specified bitstream.'
                             '\nIf not specified, it will use the bitstream found in images/linux/.'
                             )
    jtag_parser.add_argument('--rootfs', metavar='ROOTFS_CPIO_FILE',
                             type=boot_common.add_bootfile('ROOTFS'), nargs='?',
                             default='', const='Default',
                             help='Specify the cpio rootfile system needs to be used for boot.'
                             '\nSupports for: zynq,zynqMP,versal,versal-net and microblaze.'
                             )
    jtag_parser.add_argument('--dtb', type=boot_common.add_bootfile('DTB'),
                             nargs='?', default='', const='Default',
                             help='Specify the DTB path')
    jtag_parser.add_argument('--boot-script', type=boot_common.add_bootfile('BOOTSCRIPT'),
                             nargs='?', default='', const='Default',
                             help='Specify the boot.scr path')
    jtag_parser.add_argument('--hw_server-url', help='Specify the URL of the hw_server to connect to.'
                             '\nThis argument is optional and defaults to blank (local).'
                             '\nAn example URL is: "TCP:localhost:3121"'
                             )
    jtag_parser.add_argument('--load-addr', action='append',
                             type=boot_common.add_property_to_bootfile(
                                 sub_key='LoadAddr'),
                             help='Address to load the image', default=[])
    jtag_parser.add_argument('--before-connect', metavar='CMD', action='append', default=[],
                             help='Extra commands to run before XSDB connect '
                             'command. Can be used multiple times')
    jtag_parser.add_argument('--after-connect', metavar='CMD', action='append', default=[],
                             help='Extra commands to run after XSDB connect '
                             'command. Can be used multiple times')
    jtag_parser.add_argument('--xsdb-connect', metavar='CONNECT_CMD',
                             help='customised XSDB connect command')
    jtag_parser.add_argument('--tcl', metavar='TCL_OUTPUT', type=os.path.realpath,
                             help='Dump XSDB commands to the specified file')
    jtag_parser.add_argument('--targetcpu', metavar='TARGET_CPU', default=0,
                             type=int, help='Specify target CPUID (0 to N-1)')
    jtag_parser.add_argument('--targetcluster', metavar='TARGET_CLUSTER', default=0,
                             type=int, help='Specify target cluster (0 to N-1)')

    jtag_parser.set_defaults(func=JtagBootSetup)

    return
