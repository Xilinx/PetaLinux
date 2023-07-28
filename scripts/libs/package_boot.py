#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import os
import sys
import logging
import argparse
import random
import string

scripts_path = os.path.dirname(os.path.realpath(__file__))
libs_path = scripts_path + '/libs'
sys.path = sys.path + [libs_path]
import plnx_vars
import plnx_utils
import gen_mbbootbin
import gen_downloadbit
import gen_bootbin
from package_common import BootParams, BootParamDisable
import package_common

logger = logging.getLogger('PetaLinux')


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


def argreadlink(arg):
    ''' Read the realpath if path exists '''
    if os.path.exists(arg):
        arg = os.path.realpath(arg)
    return arg


def add_bootfile(dict_key, sub_key='Path'):
    ''' Add bootfile param into Dict '''
    ''' Append random key if data files and bif attaributes '''
    def f(arg):
        if arg in ['no', 'none']:
            BootParamDisable.append(dict_key)
            arg = None
        elif arg:
            arg = argreadlink(arg)
        if arg and dict_key:
            tmp_key = dict_key
            if dict_key in ['ADDFILE', 'ADDCDO', 'BIFATTR']:
                rmdstr = ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=5)
                )
                tmp_key = dict_key + '@' + rmdstr
            plnx_utils.add_dictkey(BootParams, tmp_key, sub_key, arg)
        return arg
    return f


def ValidateArgArch(args, arch):
    ''' Validate the Arguments specified v/s Arch and gives error '''
    if arch == 'aarch64':
        for arg in ['mmi', 'flash_size', 'flash_intf']:
            if getattr(args, arg):
                return arg
        if args.format == 'DOWNLOAD.BIT':
            return 'format DOWNLOAD.BIT'
        return ''
    elif arch == 'arm':
        for arg in ['tfa', 'mmi', 'flash_size', 'flash_intf', 'pmufw']:
            if getattr(args, arg):
                return arg
        if args.format == 'DOWNLOAD.BIT':
            return 'format DOWNLOAD.BIT'
        return ''
    elif arch == 'microblaze':
        for arg in ['tfa', 'file_attribute', 'bif_attribute',
                    'bif_attribute_value', 'fsblconfig', 'bif',
                    'pmufw', 'bootgen_extra_args']:
            if getattr(args, arg):
                return arg
        return ''
    else:
        logger.error('Failed to validate arguments, unknown sys ARCH: %s'
                     % arch)
        sys.exit(255)


def CreateBootBin(args, proot):
    ''' Creating boot.bin image with bootgen command '''
    if args.bif:
        ''' If User specified Bif File '''
        if not os.path.isfile(args.bif):
            logger.error('Specified BIF file: %s doesnot exist.' % args.bif)
            sys.exit(255)
        if BootParams:
            logger.warning('You have specified BIF file,'
                           'it will override all your other package boot settings.')
        ''' Run Bootgen Command '''
        gen_bootbin.RunBootGen(args.bif, args, proot)
    else:
        ''' Generate the Bif File with Build Images '''
        args.bif = plnx_vars.BifFile.format(proot)
        ''' Run Bootgen Command '''
        gen_bootbin.GenerateBif(args, proot)


def CopyImageToTftp(args, proot):
    ''' Copy Final Output Files to TFTP Directory '''
    copy_to_tftp = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_COPY_TO_TFTPBOOT',
                                               plnx_vars.SysConfFile.format(proot))
    tftp_dir = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_TFTPBOOT_DIR',
                                           plnx_vars.SysConfFile.format(proot))
    images_dir = plnx_vars.BuildImagesDir.format(proot)
    plnx_utils.CreateDir(images_dir)

    output_dir = os.path.dirname(args.output)
    output_file = os.path.basename(args.output)
    if images_dir != output_dir:
        plnx_utils.CopyFile(args.output, images_dir)
        if args.xilinx_arch in ['versal', 'versal-net']:
            bh_file = '%s_bh.bin' % output_file.split('.')[0]
            plnx_utils.CopyFile(os.path.join(output_dir, bh_file),
                                images_dir)
            plnx_utils.CopyFile(os.path.join(output_dir, 'qemu_boot.img'),
                                images_dir)

    try:
        fsbl_path = BootParams['FSBL'].get('Path')
    except KeyError:
        fsbl_path = ''
    if fsbl_path:
        def_fsbl = os.path.join(plnx_vars.BuildImagesDir.format(proot),
                                plnx_vars.BootFileNames.get('%s_%s' % (
                                    'FSBL', args.xilinx_arch.upper())))
        if def_fsbl and def_fsbl != fsbl_path:
            plnx_utils.CopyFile(fsbl_path, def_fsbl)

    if copy_to_tftp != 'y':
        return 0
    if not tftp_dir:
        logger.warning(
            'No TFTPBOOT folder defined, Skip file copy to TFTPBOOT folder!!!')
        return 0
    elif not os.access(tftp_dir, os.W_OK):
        logger.warning('Unable to access the TFTPBOOT folder %s!!!' % tftp_dir)
        logger.warning('Skip file copy to TFTPBOOT folder!!!')
        return 0

    if os.environ.get('TFTPDIR_DISABLE') in ['True', 'TRUE']:
        logger.warning(
            'TFTPDIR_DISABLE env set to TRUE, skip images copy to TFTPBOOT folder!!!')
        return 0
    plnx_utils.CopyFile(args.output, tftp_dir)
    if fsbl_path:
        plnx_utils.CopyFile(fsbl_path, tftp_dir)


def PackageBootImage(args, proot):
    ''' Packaging different type of Boot Images '''
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)
    arg = ValidateArgArch(args, args.arch)
    if arg:
        logger.error('Invalid arg "--%s" for system arch %s.' % (
            arg, args.arch))
        sys.exit(255)
    package_common.AddFpgaBootFile(args.fpga, proot, args.xilinx_arch)

    # Set Default Format name
    if not args.format:
        args.format = 'BIN'
        if args.xilinx_arch == 'microblaze':
            args.format = 'MCS'

    # Get Default Output file name
    if not args.output:
        formate = args.format.replace('.', '')
        if args.format == 'MCS' and args.xilinx_arch == 'microblaze':
            ''' Get output file name variable BootMBMCSFile value '''
            args.output = eval(
                'plnx_vars.BootMB%sFile.format("%s")' % (formate, proot))
        else:
            ''' Get output file name variable BootBINFile '''
            args.output = eval(
                'plnx_vars.Boot%sFile.format("%s")' % (formate, proot))
    package_common.CheckOutFile(args.output, args.force)
    # Add Default Boot Files to Dictionary
    package_common.AddDefaultBootFile(args, proot)
    # Create outputdir directory
    plnx_utils.CreateDir(os.path.dirname(args.output))
    # Run Respective funtion per arch and format type
    if args.format in ['BIN', 'MCS']:
        FailedMsg = 'Please source Xilinx Tools settings first.'
        if args.arch in ['arm', 'aarch64']:
            plnx_utils.check_tool('bootgen', FailedMsg)
            CreateBootBin(args, proot)
        else:
            plnx_utils.check_tool('vivado', FailedMsg)
            gen_mbbootbin.CreateMBBootBin(args, proot)
    elif args.format == 'DOWNLOAD.BIT':
        gen_downloadbit.CreateDownloadbit(args, proot, args.output)
    
    logger.info('Successfully Generated %s File' % args.format)
    # Copy Output files to TFTP directory
    CopyImageToTftp(args, proot)


def pkgboot_args(boot_parser):
    boot_parser.add_argument('-o', '--output',
                             help='Generated boot image name', type=os.path.realpath)
    boot_parser.add_argument('-f', '--fpga', nargs='?', default='',
                             const='Default', metavar='BIT/PDI_FILE',
                             help='Path to FPGA bitstream/pdi file location'
                             '\nDefault : images/linux/*.bit (The one copied from the XSA)'
                             '\nFor MicroBlaze,Zynq and ZynqMP'
                             '\nDefault : project-spec/hw-description/*.pdi'
                             '\nFor Versal and Versal-Net'
                             )
    boot_parser.add_argument('--tfa', '--atf', type=add_bootfile('TFA'), nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['TFA']),
                             help='ZynqMP and Versal only. Path to TF-A'
                             '\nTo skip packing atf|tfa use --atf|--tfa no/none'
                             )
    boot_parser.add_argument('--dtb', type=add_bootfile('DTB'), nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['DTB']),
                             help='Path to DTB image location'
                             '\nTo skip packing DTB use --dtb no/none'
                             )
    boot_parser.add_argument('--fsbl', type=add_bootfile('FSBL'), nargs='?', default='',
                             help='Path to FSBL ELF image location.'
                             '\nFor Zynq: images/linux/zynq_fsbl.elf'
                             '\nFor ZynqMP: images/linux/zynqmp_fsbl.elf'
                             '\nFor MicroBlaze: images/linux/fs-boot.elf'
                             '\nFor versal and versal-Net: Not supported.'
                             '\nTo skip packing fsbl use --fsbl no or --fsbl none'
                             )
    boot_parser.add_argument('--pmufw', type=add_bootfile('PMUFW'), nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['PMUFW']),
                             help='Path to the PMUFW ELF location.'
                             '\nApplicable only for ZynqMP.'
                             '\nDefault: images/linux/pmufw.elf'
                             '\nTo skip packing pmufw use --pmufw no or --pmufw none'
                             )
    boot_parser.add_argument('--psmfw', type=add_bootfile('PSMFW'), nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['PSMFW']),
                             help='Path to the PSMFW ELF location.'
                             '\nApplicable only for Versal and Versal-Net.'
                             '\nDefault: images/linux/psmfw.elf'
                             '\nTo skip packing pmufw use --psmfw no or --psmfw none'
                             )
    boot_parser.add_argument('--plm', type=add_bootfile('PLM'), nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['PLM']),
                             help='Path to the PLM ELF location.'
                             '\nApplicable only for Versal and Versal-Net.'
                             '\nDefault: images/linux/plm.elf'
                             '\nTo skip packing pmufw use --plm no or --plm none'
                             )
    boot_parser.add_argument('--boot-script', type=add_bootfile('BOOTSCRIPT'),
                             metavar='<BOOT_SCRIPT>', nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['BOOTSCRIPT']),
                             help='Path to the boot.scr file location'
                             '\nDefault: images/linux/boot.scr'
                             '\nTo skip packing boot.scr use --boot-script no or --boot-script none'
                             )
    boot_parser.add_argument('-u', '--u-boot', '--uboot', type=add_bootfile('UBOOT'),
                             nargs='?', default='',
                             const='Default',
                             help='Path to the u-boot image location.'
                             '\nNot valid for DOWNLOAD.BIT'
                             '\nu-boot.elf For Zynq, ZynqMP, Versal and Versal-Net'
                             '\nu-boot-s.bin For Microblaze'
                             )
    boot_parser.add_argument('--kernel', type=add_bootfile('KERNEL'), nargs='?', default='',
                             const=os.path.join(
                                 plnx_vars.ImagesDir, plnx_vars.BootFileNames['KERNEL']),
                             help='Path to the kernel image location(fitImage)'
                             '\nNot valid for DOWNLOAD.BIT. Default: images/linux/image.ub'
                             )
    boot_parser.add_argument('--qemu-rootfs', nargs='?', type=argreadlink,
                             help='Path to the rootfs file location to create qemu_boot.img(cpio.gz.uboot)'
                             '\nDefault: images/linux/rootfs.cpio.gz.uboot'
                             '\nTo skip packing rootfs use --qemu-rootfs no or --qemu-rootfs none'
                             )
    boot_parser.add_argument('--add', type=add_bootfile('ADDFILE'), action='append',
                             default=[], metavar='<DATA_FILE>', help='Path to the data file to add'
                             )
    boot_parser.add_argument('--add-cdo', type=add_bootfile('ADDCDO'), action='append',
                             default=[], metavar='<CDO_FILE>',
                             help='Path to the cdo bin file for Versal and Versal-Net'
                             )
    boot_parser.add_argument('--bif', type=os.path.realpath, metavar='<BIF_FILE>',
                             help='Custom BIF File. It overrides all other settings'
                             )
    boot_parser.add_argument('--mmi', type=os.path.realpath, metavar='<MMI_FILE>',
                             help='Bitstream MMI file. Valid for MicroBlaze only.'
                             '\nIt will be used to generate the download.bit with'
                             '\nbootloader in the bram. Default will be the MMI'
                             '\nfile in the same directory as the FPGA bitstream.'
                             )
    boot_parser.add_argument('--format', default='',
                             nargs='?', const='BIN', type=plnx_utils.ToUpper,
                             choices=['BIN', 'DOWNLOAD.BIT', 'MCS'], help='Avaiable formats:'
                             '\n* BIN (default): generate BIN file to be put to Flash or SD to boot from it.'
                             '\n* MCS: generate MCS file Flash boot'
                             '\n* DOWNLOAD.BIT: Merges the fs-boot into the FPGA'
                             '\n   bitstream by mapping the ELF data'
                             '\n   onto the memory map information (MMI)'
                             '\n   for the block RAMs in the design'
                             )
    boot_parser.add_argument('--flash-size', default='',
                             help='Flash size in MBytes of the PROM device is targeted.'
                             '\nIt must be power of 2. Only valid for MicroBlaze MCS format.'
                             '\nIf this value is not specified. It will auto detect'
                             '\nthe system flash configured from system config.'
                             '\nIf it is parallel flash, it will auto detect flash size'
                             '\nIf it is SPI flash, the default is 16 Mbytes.'
                             )
    boot_parser.add_argument('--flash-intf', default='',
                             help='Flash interface. Available options:'
                             '\nOnly valid for MicroBlaze MCS'
                             '\n * SERIALx1'
                             '\n * SPIx1'
                             '\n * SPIx2'
                             '\n * SPIx4'
                             '\n * BPIx8'
                             '\n * BPIx16'
                             '\n * SMAPx8'
                             '\n * SMAPx16'
                             '\n * SMAPx32'
                             '\nIf not specified, it will auto detect the system'
                             '\nflash configured from system config.'
                             '\nIf it is parallel flash, it will auto detect flash'
                             '\nwidth. If it is SPI flash, the default will be SPIx1.'
                             )
    boot_parser.add_argument('--boot-device', default='', choices=['sd', 'flash'],
                             help='valid only for generating BIN file.'
                             )
    boot_parser.add_argument('--cpu', metavar='<TARGETCPU>', action='append',
                             type=add_property_to_bootfile(sub_key='Cpu'),
                             default=[], help='Destination CPU of the data file'
                             )
    boot_parser.add_argument('--offset', action='append', default=[],
                             type=add_property_to_bootfile(sub_key='Offset'),
                             help='Partition offset of previously specified data file'
                             )
    boot_parser.add_argument('--load', action='append', default=[], metavar='<LOADADDR>',
                             type=add_property_to_bootfile(sub_key='Load'),
                             help='Load address for specified data file.'
                             '\nThe Ram address where to load the specified data file.'
                             '\nEx: [ partition_type=raw, load=0x01000 ] <image>'
                             )
    boot_parser.add_argument('--file-attribute', action='append', default=[],
                             type=add_property_to_bootfile(
                                 sub_key='FileAttribute', append=True),
                             metavar='<DATA_FILE_ATTR>', help='Data file file-attribute'
                             )
    boot_parser.add_argument('--bif-attribute', type=add_bootfile('BIFATTR', 'BifAttr'), action='append',
                             default=[], metavar='<BIF_ATTRIBUTE>', help='Name of BIF attribute'
                             )
    boot_parser.add_argument('--bif-attribute-value', action='append',
                             type=add_property_to_bootfile('BifAttr', 'Value'),
                             default=[], metavar='<BIF_ATTRIBUTE_VALUE>',
                             help='Value of the attribute specified by --bif-attribute argument'
                             )
    boot_parser.add_argument('--fsblconfig', default='',
                             metavar='<BIF_FSBL_CONFIG>', help='ZynqMP only.'
                             'BIF fsbl config value')
    boot_parser.add_argument('--bootgen-extra-args', default='',
                             help='Extra arguments to be passed while invoking bootgen command'
                             )
    boot_parser.add_argument('--updatemem-extra-args', default='',
                             help='Microblaze only. Extra arguments to be passed while invoking updatemem command'
                             )

    boot_parser.set_defaults(func=PackageBootImage)
    return
