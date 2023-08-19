#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import logging
import os
import sys

scripts_path = os.path.dirname(os.path.realpath(__file__))
libs_path = scripts_path + '/libs'
sys.path = sys.path + [libs_path]
import plnx_utils
import plnx_vars
from package_common import (AddedLinuxId, AddedSubBootId, BootFilesSeq,
                            BootParams)

logger = logging.getLogger('PetaLinux')


def AddBifSubsystemId(Attribute, Value, xilinx_arch, notfile=False):
    ''' Bif format as per the xilinx arch
    For versal{-net} image file should be { attrs, file }
    For others image file should be [attrs] file'''
    string = ''
    if xilinx_arch in ['versal', 'versal-net']:
        string += ''
        if not notfile:
            Value = 'file=%s' % Value
        if Attribute and Value:
            string += '{ %s, %s }' % (Attribute, Value)
        elif Value:
            string += '{ %s }' % Value
    else:
        if Attribute and Value:
            string += '[%s] %s' % (Attribute, Value)
        elif Value:
            string += '%s' % Value
    return string


def GenQemuBootImage(args, proot):
    ''' Generate the qemu-boot.img file for versal{-net} qemu boot'''
    BootBinDir = os.path.dirname(args.output)
    Bootscript = os.path.join(plnx_vars.BuildImagesDir.format(proot),
                              plnx_vars.BootFileNames['BOOTSCRIPT']
                              )
    if not os.path.isfile(Bootscript):
        Bootscript = os.path.join(plnx_vars.PreBuildsImagesDir.format(proot),
                                  plnx_vars.BootFileNames['BOOTSCRIPT']
                                  )
    logger.info('Generating QEMU boot images...')
    BootBinTmpDir = os.path.join(plnx_vars.BuildDir.format(proot),
                                 'bootbin')
    plnx_utils.CreateDir(BootBinTmpDir)
    plnx_utils.CopyFile(args.output, os.path.join(BootBinTmpDir,
                                                  plnx_vars.BootFileNames['BOOTBIN']))
    logger.info('File in qemu_boot.img: %s' % args.output)
    plnx_utils.CopyFile(Bootscript, os.path.join(BootBinTmpDir,
                                                 os.path.basename(Bootscript)))
    logger.info('File in qemu_boot.img: %s' % Bootscript)
    QemuRootfs = args.qemu_rootfs
    initramfs_image = plnx_utils.get_config_value(
        'CONFIG_SUBSYSTEM_INITRAMFS_IMAGE_NAME',
        plnx_vars.SysConfFile.format(proot))
    if not QemuRootfs:
        if initramfs_image.find('initramfs') != -1 and not QemuRootfs:
            QemuRootfs = os.path.join(plnx_vars.BuildImagesDir.format(proot),
                                      plnx_vars.BootFileNames['TINY_RFS_FILE'])
        else:
            QemuRootfs = os.path.join(plnx_vars.BuildImagesDir.format(proot),
                                      plnx_vars.BootFileNames['RFS_FILE'])

    if QemuRootfs and QemuRootfs not in ['no', 'none']:
        if not os.path.isabs(QemuRootfs):
            QemuRootfs = os.path.join(proot, QemuRootfs)

        if not os.path.isfile(QemuRootfs):
            logger.warning('Missing file %s, Specify it using '
                           '--qemu-rootfs <rfs file>' % QemuRootfs)
        else:
            QemuRootfs = os.path.realpath(QemuRootfs)
            plnx_utils.CopyFile(QemuRootfs, os.path.join(BootBinTmpDir,
                                                         os.path.basename(QemuRootfs)))
            logger.info('File in qemu_boot.img: %s' % QemuRootfs)

    plnx_utils.check_tool('mkfatimg')
    MkFatCmd = 'mkfatimg %s %s %s' % (BootBinTmpDir,
                                      os.path.join(
                                          BootBinDir, 'qemu_boot.img'),
                                      '262144')
    plnx_utils.runCmd(MkFatCmd, os.getcwd(), shell=True)
    plnx_utils.RemoveDir(BootBinTmpDir)


def RunBootGen(biffile, args, proot):
    ''' Run bootgen command with given biffile path '''
    logger.info('Generating %s binary package %s...' % (
                args.xilinx_arch, os.path.basename(args.output))
                )
    extra_bootargs = ''
    bootgen_arch = args.xilinx_arch.replace('-', '')
    if args.xilinx_arch in ['versal', 'versal-net']:
        extra_bootargs = '-w -dump bh'
    if args.bootgen_extra_args:
        extra_bootargs += ' %s' % args.bootgen_extra_args
    BootGenCmd = 'bootgen -arch %s -image %s -o %s %s' % (
        bootgen_arch, plnx_vars.BifFile.format(proot),
        args.output, extra_bootargs)
    stdout = plnx_utils.runCmd(BootGenCmd, os.getcwd(),
                               failed_msg='Fail to create BOOT image', shell=True)
    logger.info(''.join(stdout))
    if args.xilinx_arch in ['versal', 'versal-net'] and \
            args.format == 'BIN':
        GenQemuBootImage(args, proot)
    logger.info('Binary is ready.')


def GenerateBif(args, proot):
    ''' Generate the Bif file fir Build Images '''
    global AddedSubBootId
    global AddedLinuxId
    # Parse BootParams to create Bif file
    bif_content = '%s:\n{\n' % plnx_vars.BifImagePrefix
    for File in BootFilesSeq[args.xilinx_arch]:
        FilteredFiles = [key for key in BootParams.keys()
                         if key.startswith(File)]
        for File in FilteredFiles:
            File_Attr_ = ''
            File_content = ''
            if BootParams[File].get('FileAttribute'):
                File_Attr_ += BootParams[File].get('FileAttribute')
                if args.xilinx_arch == 'zynqmp' and \
                        File_Attr_.find('bootloader') == '-1':
                    File_Attr_ = '%s, destination_cpu=a53-0' % File_Attr_
            else:
                if args.xilinx_arch == 'zynqmp' and \
                        File_Attr_.find('bootloader') == '-1':
                    File_Attr_ += 'destination_cpu=a53-0'
            if BootParams[File].get('Cpu'):
                DestCpu = 'destination_cpu=%s' % BootParams[File].get(
                    'Cpu')
                if args.xilinx_arch in ['versal', 'versal-net']:
                    DestCpu = 'core=%s' % BootParams[File].get('Cpu')
                Tmp_Attr_ = ''
                if File_Attr_.find('destination_cpu=') != -1 or \
                        File_Attr_.find('core=') != -1:
                    for _Attr in File_Attr_.split(','):
                        if _Attr.find('destination_cpu=') != -1 or \
                                _Attr.find('core=') != -1:
                            Tmp_Attr_ += ', %s' % DestCpu
                        else:
                            Tmp_Attr_ += ', %s' % _Attr
                    File_Attr_ = ' '.join(Tmp_Attr_.split())
                else:
                    File_Attr_ += ', %s' % DestCpu
            if BootParams[File].get('Offset'):
                offset = BootParams[File].get('Offset')
                if File_Attr_:
                    File_Attr_ += ', offset=%s' % offset
                else:
                    File_Attr_ += 'offset=%s' % offset
            if BootParams[File].get('Load'):
                load = BootParams[File].get('Load')
                if File_Attr_:
                    File_Attr_ += ', load=%s' % load
                else:
                    File_Attr_ += 'load=%s' % load
            if args.xilinx_arch in ['versal', 'versal-net'] and \
                    BootParams[File].get('AddBootId'):
                if not AddedSubBootId:
                    AddedSubBootId = True
                    bif_content += 'image {\n'
            elif args.xilinx_arch in ['versal', 'versal-net']:
                if not AddedLinuxId:
                    AddedLinuxId = True
                    if AddedSubBootId:
                        bif_content += '\n}'
                    bif_content += '\nimage {\n'
                    bif_content += '\tid = 0x1c000000, name=apu_subsystem\n'

            if BootParams[File].get('Path'):
                FilePath = BootParams[File].get('Path')
                if not os.path.isabs(FilePath):
                    FilePath = os.path.join(proot, FilePath)
                plnx_utils.CheckFileExists(
                    FilePath, 'Failed to generate BIF file, ')
                File_content = AddBifSubsystemId(
                    File_Attr_.strip(',').strip(),
                    FilePath, args.xilinx_arch)
                logger.info('File in BOOT BIN: "%s"' % FilePath)
            if BootParams[File].get('BifAttr'):
                File_Attr_ += BootParams[File].get('BifAttr')
            if BootParams[File].get('Value'):
                logger.info('Adding Bif Attribute %s' % File_Attr_)
                File_content = AddBifSubsystemId(
                    File_Attr_,
                    BootParams[File].get('Value'),
                    args.xilinx_arch, notfile=True
                )

            bif_content += '\t%s\n' % File_content
    if args.fsblconfig:
        logger.info('Adding fsbl_config %s' % args.fsblconfig)
        bif_content += '\t[fsbl_config] %s\n' % args.fsblconfig
    bif_content += '}\n'
    if AddedLinuxId:
        bif_content += '}\n'
    logger.debug(bif_content)
    plnx_utils.RemoveFile(plnx_vars.BifFile.format(proot))
    plnx_utils.CreateFile(plnx_vars.BifFile.format(proot))
    plnx_utils.add_str_to_file(plnx_vars.BifFile.format(proot),
                               bif_content)
    RunBootGen(plnx_vars.BifFile.format(proot), args, proot)
