#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import argparse
import glob
import logging
import os
import re
import sys
import bitbake_utils
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')

# Default Part sizes
BootPartSize = '2G'
RootPartSize = '4G'

# Pseudo command
PseudoCmd = 'PSEUDO_LOCALSTATEDIR={0}/pseudo PSEUDO_NOSYMLINKEXP=1 \
        PSEUDO_IGNORE_PATHS="/usr/,/etc/,/lib,/dev/" PSEUDO_UNLOAD=1 PSEUDO_PREFIX={1} {2}'

# wks file
WksFileStr = '''
# Description: Creates a partitioned SD card image. Boot files
# are located in the first vfat partition. Rootfs will be in second ext4 partition.
part /boot --source bootimg-partition --use-label --fstype=vfat --label boot --active --align 4 --fixed-size {0}
part /     --source rootfs            --use-label --fstype=ext4 --label root          --align 4 --fixed-size {1}
'''


def ValidateUserPartSize():
    ''' Validating the User given size int or not'''
    def p(arg):
        size_ = arg.split(',')
        global BootPartSize, RootPartSize
        # If , separator given split and assign.
        # If no separator assign that value to boot part
        if size_[0]:
            BootPartSize = size_[0]
        if len(size_) >= 2 and size_[1]:
            RootPartSize = size_[1]
        # Check if given size value is integer if not give error
        for Size in BootPartSize, RootPartSize:
            if Size[-1].isalpha():
                if not Size[:-1].isnumeric():
                    raise argparse.ArgumentTypeError(
                        'Invalide size: %s' % (Size))
        return arg
    return p


def ReplaceColonWithSemiColon(arg):
    ''' Replace colon with semicolon'''
    return arg.replace(':', ';')


def GetDefaultWicFiles(args, proot):
    ''' Assigning the Default boot files list if user not provided'''
    WicDefaultFiles = plnx_vars.BootFileNames.get('BOOTBIN', '')
    WicDefaultFiles += ' %s' % plnx_vars.BootFileNames.get('BOOTSCRIPT', '')
    WicDefaultFiles += ' %s' % plnx_vars.BootFileNames.get(
        'KIMAGE_%s' % args.arch.upper(), '')
    # Add ramdisk image if switch_root enabled
    initramfs_image = plnx_utils.get_config_value(
        'CONFIG_SUBSYSTEM_INITRAMFS_IMAGE_NAME',
        plnx_vars.SysConfFile.format(proot))
    if initramfs_image.find('initramfs') != -1:
        WicDefaultFiles += ' %s ' % plnx_vars.BootFileNames.get(
            'TINY_RFS_FILE', '')

    # Check each file exists or not and give error
    for Image in WicDefaultFiles.split():
        if not os.path.exists(os.path.join(args.images_dir, Image)):
            logger.error('%s was not found in %s Directory' %
                         (Image, args.images_dir))
            logger.error('This is required to create the wic image')
            sys.exit(255)
    # Add openamp dtbo to wic if openamp enabled
    IsOpenampEnabled = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_ENABLE_OPENAMP_DTSI',
                                                   plnx_vars.SysConfFile.format(proot))
    IsPkgGrpOpenamp = plnx_utils.get_config_value('CONFIG_packagegroup-petalinux-openamp',
                                                  plnx_vars.RfsConfig.format(proot))
    if os.path.exists(os.path.join(args.images_dir, plnx_vars.BootFileNames.get('OPENAMP'))) and \
            not IsOpenampEnabled and IsPkgGrpOpenamp:
        WicDefaultFiles += ' %s;devicetree' % plnx_vars.BootFileNames.get(
            'OPENAMP')
    return WicDefaultFiles


def PackageWic(args, proot):
    ''' Generate the WIC image'''
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)
    if os.path.isabs(args.images_dir):
        args.images_dir = os.path.join(proot, args.images_dir)
    logger.info('Sourcing build environment')

    WicDefaultFiles = args.bootfiles
    if not WicDefaultFiles:
        WicDefaultFiles = GetDefaultWicFiles(args, proot)

    WicTmpRootfs = os.path.join(
        plnx_vars.WicTmpWorkDir.format(proot), 'rootfs')

    WicRfsFile = args.rootfs_file
    if not WicRfsFile:
        WicRfsFile = os.path.join(args.images_dir, 'rootfs.tar.gz')

    if not args.outdir:
        args.outdir = plnx_vars.BuildImagesDir.format(proot)

    # Add extra bootfiles if user provided
    if args.extra_bootfiles:
        WicDefaultFiles += ' %s' % args.extra_bootfiles

    ConfigTmpDir = plnx_utils.get_config_value('CONFIG_TMP_DIR_LOCATION',
                                               plnx_vars.SysConfFile.format(proot))
    ConfigTmpDir = ConfigTmpDir.replace(
        '${PROOT}', proot).replace('$PROOT', proot)
    ConfigTmpDir = os.path.expandvars(ConfigTmpDir)

    # Check Yocto SDK env script exists or not
    if not os.path.exists(plnx_vars.EsdkInstalledDir.format(proot)) or \
            not glob.glob(os.path.join(plnx_vars.EsdkInstalledDir.format(proot),
                          'environment-setup*')):
        logger.error(
            'Failed to get yocto SDK environment file, This is required to create wic image.')
        logger.error('Run petalinux-config to install yocto SDK')
        sys.exit(255)

    # Check if TMPDIR is NFS
    if not os.path.exists(ConfigTmpDir) or plnx_utils.get_filesystem_id(ConfigTmpDir) == '6969':
        logger.error(
            'TMPDIR directory is on NFS or Empty. Please run petalinux-config to set the TMPDIR location')
        sys.exit(255)

    # Check pseudo(fakeroot) if not build it
    PseudoPrefix = os.path.join(
        ConfigTmpDir, 'sysroots-components', 'x86_64', 'pseudo-native', 'usr')
    Pseudo = os.path.join(PseudoPrefix, 'bin', 'pseudo')
    if not os.path.isfile(Pseudo):
        logger.info('bitbake pseudo-native')
        bitbake_utils.run_bitbakecmd('bitbake pseudo-native',
                                     proot, shell=True, logfile=args.logfile)
    # Check wictool dir if not build it
    WicToolsDir = os.path.join(ConfigTmpDir, 'work', plnx_vars.YoctoEnvFile[args.arch],
                               'wic-tools', '1.0-r0', 'recipe-sysroot-native')
    if not os.path.isdir(WicToolsDir):
        logger.info('bitbake wic-tools')
        bitbake_utils.run_bitbakecmd('bitbake wic-tools',
                                     proot, shell=True, logfile=args.logfile)

    # Remove if Old build/wic directory found
    plnx_utils.RemoveDir(plnx_vars.WicTmpWorkDir.format(proot))
    plnx_utils.CreateDir(plnx_vars.WicTmpWorkDir.format(proot))
    # Tmp dir to create .wic image
    WicTmpBuildDir = os.path.join(plnx_vars.WicTmpWorkDir.format(proot),
                                  'wic-tmp')
    plnx_utils.CreateDir(WicTmpBuildDir)
    # Extract the rootfs if not exists in given path
    if not os.path.exists(WicTmpRootfs):
        plnx_utils.CreateDir(WicTmpRootfs)
        plnx_utils.CreateDir(os.path.join(
            plnx_vars.WicTmpWorkDir.format(proot), 'pseudo'))
        logger.info('Extracting rootfs, This may take time!')
        if not os.path.exists(WicRfsFile):
            logger.error('%s File doesnot exists' % WicRfsFile)
            sys.exit(255)
        if os.path.exists(os.path.join(PseudoPrefix, 'var')):
            plnx_utils.RemoveDir(os.path.join(PseudoPrefix, 'var'))

        TarCmd = PseudoCmd.format(plnx_vars.WicTmpWorkDir.format(proot),
                                  PseudoPrefix, Pseudo)
        TarCmd += ' tar -xf "%s" -C "%s"' % (WicRfsFile, WicTmpRootfs)
        plnx_utils.runCmd(TarCmd, out_dir=os.getcwd(), shell=True)

    logger.info('Creating wic image')
    # Generate the wks file if user not given
    WksFile = args.wks
    if not WksFile:
        WksFile = os.path.join(plnx_vars.BuildDir.format(proot), 'rootfs.wks')
        plnx_utils.CreateFile(WksFile)
        plnx_utils.add_str_to_file(WksFile,
                                   WksFileStr.format(BootPartSize, RootPartSize))
    # Update petalinux-bsp.conf file with boot files given
    plnx_utils.update_config_value('IMAGE_BOOT_FILES:%s ' % args.xilinx_arch,
                                   ' "%s"' % WicDefaultFiles,
                                   plnx_vars.PlnxBspConfig.format(proot))
    # wic create command to create sd image
    WicCmd = 'wic create %s --rootfs-dir %s --bootimg-dir %s \
--kernel-dir %s --outdir  %s -n %s %s' % (
        WksFile, WicTmpRootfs, args.images_dir,
        args.images_dir, WicTmpBuildDir, WicToolsDir,
        args.wic_extra_args)
    logger.info(WicCmd)
    bitbake_utils.run_bitbakecmd(WicCmd,
                                 proot, shell=True, logfile=args.logfile)
    # Get the exact output file from wic tmp dir
    WicOutFile = [f for f in glob.glob(
        os.path.join(WicTmpBuildDir, 'rootfs-*.direct*'))
        if not re.search('.+.direct.p.+', f)][0]
    # Get the output file extention
    WicOutExt = os.path.basename(
        WicOutFile).split('.', 1)[1].replace(
        'direct', 'wic')
    # Copy final image to outdir
    plnx_utils.CreateDir(args.outdir)
    plnx_utils.RenameFile(WicOutFile, os.path.join(args.outdir,
                                                   'petalinux-sdimage.%s' % WicOutExt))
    # Remove wic tmp dir
    plnx_utils.RemoveDir(plnx_vars.WicTmpWorkDir.format(proot))
    logger.info('Successfully Generated image: %s' % os.path.join(args.outdir,
                                                                  'petalinux-sdimage.%s' % WicOutExt))


def pkgwic_args(wic_parser):
    wic_parser.add_argument('-p', '--project', metavar='PROJECT_DIR', type=os.path.realpath,
                            help='Specify full path to a PetaLinux project.'
                            )
    wic_parser.add_argument('-w', '--wks', metavar='WKS_FILE', type=os.path.realpath,
                            help='Specify Kickstart File used to create partitions of SD Image.'
                            )
    wic_parser.add_argument('-o', '--outdir', metavar='OUTPUT_DIR', type=os.path.realpath,
                            help='Specify out directory the to place petalinux-sdimage.wic'
                            )
    wic_parser.add_argument('-i', '--images-dir', type=os.path.realpath, default=plnx_vars.ImagesDir,
                            help='Specify the images directory the bootfiles are located.'
                            '\nDefault will be <PROOT>/images/linux'
                            )
    wic_parser.add_argument('-c', '--rootfs-file', type=os.path.realpath,
                            help='Specify the compressed rootfs file that will be '
                            '\nextracted into the /rootfs dir.'
                            )
    wic_parser.add_argument('-b', '--bootfiles', type=ReplaceColonWithSemiColon,
                            help='Specify bootfiles which should be copied into /boot dir'
                            '\nDefault bootfiles:'
                                 '\n  zynq:   BOOT.BIN,uImage,boot.scr'
                                 '\n  zynqMP: BOOT.BIN,Image,boot.scr'
                                 '\n  versal: BOOT.BIN,Image,boot.scr'
                                 '\n  versal-net: BOOT.BIN,Image,boot.scr'
                            )
    wic_parser.add_argument('-e', '--extra-bootfiles', type=ReplaceColonWithSemiColon,
                            help='Specify extra bootfiles which should be copied into'
                            '\n /boot dir. Make sure these are present in images-dir'
                            )
    wic_parser.add_argument('-s', '--size', metavar='<BOOTSIZE,ROOTSIZE>', type=ValidateUserPartSize(),
                            help='Specify size for boot,root partitions with "," separator.'
                            '\nSpecify as an integer value optionally followed by'
                                 '\none of the unit K/M/G, default is M if none given.'
                                 '\nDefault size: boot - 2G, root - 4G.'
                                 '\nExample: --size 2G,2G -> boot - 2G, root - 2G.'
                            )
    wic_parser.add_argument('--wic-extra-args', default='',
                            help='Extra arguments to be passed while invoking wic command'
                            )

    wic_parser.set_defaults(func=PackageWic)

    return
