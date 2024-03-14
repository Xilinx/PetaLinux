#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Varalaxmi Bingi <varalaxmi.bingi>
#
# SPDX-License-Identifier: MIT

import bitbake_utils
import plnx_utils
import plnx_vars
import boot_common
import argparse
import logging
import os
import sys
import getpass
import tempfile
import re

logger = logging.getLogger('PetaLinux')


# Global variables
# machine path
MachineDir = tempfile.mkdtemp()
plnx_vars.AutoCleanupFiles.append(MachineDir)

# default endian
DEFAULT_ENDIAN = 'little'
HOST_NET_DEV = "eth"
SkipAddWic = False
ExtraArgs = ''

QemuHwDtb = {
    'no_multi_arch': 'zynqmp-qemu-arm.dtb',
    'arm': 'zynqmp-qemu-multiarch-arm.dtb',
    'pmu': 'zynqmp-qemu-multiarch-pmu.dtb',
    'ps': 'versal-qemu-multiarch-ps.dtb',
    'pmc': 'versal-qemu-multiarch-pmc.dtb',
    'pmx': 'versal-net-qemu-multiarch-pmx.dtb',
    'psx': 'versal-net-qemu-multiarch-psx.dtb'
}

HwDtbMap = {
    'zynqmp': 'arm',
    'versal': 'ps',
    'versal-net': 'psx'
}

MbHwDtbMap = {
    'zynqmp': 'pmu',
    'versal': 'pmc',
    'versal-net': 'pmx'
}

QemuMemArgs = {
    'zynqmp': ' -m 4G ',
    'versal': ' -m 8G ',
    'versal-net': '-m 8G '
}

QemuAarchBootFiles = {
    'microblaze': ['UBOOT', 'KERNEL',
                   'DTB', 'ROOTFS'],
    'zynq': ['ZynqDTB', 'DTB',
             'UBOOT', 'KERNEL', 'ROOTFS'],
    'zynqmp': ['DTB', 'UBOOT', 'KERNEL', 'ROOTFS',
               'TFA', 'EXTROOTFS', 'PMUCONF', 'HWDTB', 'BOOTSCRIPT'],
    'versal': ['QemuBootBin', 'UBOOT', 'KERNEL', 'ROOTFS',
               'TFA', 'DTB', 'EXTROOTFS', 'HWDTB', 'BOOTSCRIPT'],
    'versal-net': ['QemuBootBin', 'UBOOT', 'KERNEL', 'ROOTFS',
                   'TFA', 'DTB', 'EXTROOTFS', 'HWDTB', 'BOOTSCRIPT']
}

QemuMbBootFiles = {
    'zynqmp': ['FSBL', 'PMUFW', 'HWDTB'],
    'versal': ['FSBL', 'BOOTBH', 'PLM', 'HWDTB'],
    'versal-net': ['FSBL', 'BOOTBH', 'PLM', 'HWDTB']
}

def AutoMmc(Mmc, args, QemuCmd):
    BootModeVersal = ''
    SdIndex = ''
    if args.xilinx_arch in ('versal', 'versal-net'):
        if QemuCmd == 'qemu-system-aarch64':
            for i in range(0, len(Mmc)):
                if Mmc[i] == '0':
                    BootModeVersal = 3
                    SdIndex = 0
                elif Mmc[i] == '1':
                    BootModeVersal = 5
                    SdIndex = 1
                elif Mmc[i] == '6':
                    BootModeVersal = 6
                    SdIndex = 3
        if args.xilinx_arch == 'versal-net':
            SdIndex = 0
        if args.xilinx_arch == 'versal-net' and BootModeVersal == 6:
            SdIndex = 1
    return BootModeVersal, SdIndex


def AutoSerial(dtb_file_path, args, QemuCmd):
    QemuSerialArgs = ''
    dts_file = dtb_file_path.replace('.dtb', '.dts')
    # Run the dtc command to convert DTB to DTS
    DtbCmd = 'dtc -I dtb -O dts -o %s %s' % (dts_file, dtb_file_path)
    stdout = plnx_utils.runCmd(DtbCmd, os.getcwd(),
                               failed_msg='Fail to convert dtb cmd', shell=True)
    with open(dts_file, 'r') as file:
        content = file.read()
        SerialRegexp = ['serial@[0-9a-zA-Z]+']
        SerialAliases = re.search(
            'stdout-path.*', content).group(0).split('=')[1].split(':')[0].replace('"', '')
        if not SerialAliases:
            SerialAliases = 'serial0'
        aliases_match = re.search(r'aliases\s*{([^}]*)}', content)
        aliases_node = aliases_match.group(1) if aliases_match else None
        exp = SerialAliases.strip(' ') + '\s*=\s*([^;]+);'
        SerialInstance = re.search(exp, aliases_node).group(
            1).split('/')[2].strip(';').strip('"')
        for lablekey in SerialRegexp:
            serial_matches = re.findall(lablekey + r'\s*{', content)
        SerialNum = serial_matches.index(SerialInstance + ' {')
        SerialCnt = len(serial_matches)
    for i in range(0, SerialCnt):
        if i == SerialNum:
            QemuSerialArgs += ' -serial mon:stdio'
        else:
            QemuSerialArgs += ' -serial /dev/null'
    if args.xilinx_arch in ('versal', 'versal-net'):
        if QemuCmd == 'qemu-system-aarch64':
            QemuSerialArgs = ' -serial null -serial null' + QemuSerialArgs
        else:
            QemuSerialArgs = ' -serial mon:stdio'
    QemuSerialArgs += ' -display none '
    return QemuSerialArgs


def AutoEth(GemCnt, TftpDir):
    QemuEthArgs = ''
    for Gem in GemCnt:
        if Gem.isdigit():
            j = int(Gem)
            for i in range(0, j+1):
                if i < j:
                    QemuEthArgs += ' -net nic'
                elif j == i:
                    QemuEthArgs += ' -net nic,netdev=%s%d -netdev user,id=%s%d,' % (
                        HOST_NET_DEV, i, HOST_NET_DEV, i)
                    if TftpDir:
                        QemuEthArgs += 'tftp=%s' % TftpDir
    return QemuEthArgs


def FindMmcAndGemStatus(dtb_file_path):
    dts_file = dtb_file_path.replace('.dtb', '.dts')
    # Run the dtc command to convert DTB to DTS
    DtbCmd = 'dtc -I dtb -O dts -o %s %s' % (dts_file, dtb_file_path)
    counter = []
    stdout = plnx_utils.runCmd(DtbCmd, os.getcwd(),
                               failed_msg='Fail to convert dtb cmd', shell=True)
    with open(dts_file, 'r') as file:
        content = file.read()
        sdhci_regexp = ['sdhci[0-9]+']
        gem_regexp = ['gem[0-9]+', 'ethernet.*[0-9]+']
        mmc_counter = []
        gem_counter = []
        symbol_match = re.search(r'__symbols__\s*{([^}]*)}', content)
        symbol_node = symbol_match.group(1) if symbol_match else None
        if symbol_node:
            sdhci_labels = []
            gem_labels = []
            for lablekey in sdhci_regexp:
                sdhci_matches = re.findall(
                    lablekey + r'\s*=\s*([^;]+);', symbol_node)
                sdhci_labels += [match.strip() for match in sdhci_matches]
            for lablekey in gem_regexp:
                gem_matches = re.findall(
                    lablekey + r'\s*=\s*([^;]+);', symbol_node)
                gem_labels += [match.strip() for match in gem_matches]
            mmc_counter = FindMmcEthNode(sdhci_labels, content)
            counter.append(mmc_counter)
            gem_counter = FindMmcEthNode(gem_labels, content)
            counter.append(gem_counter)
    return counter


def FindMmcEthNode(labels, content):
    generic_address = None
    generic_status = None
    counter = []
    gem_num = 0
    emmc_mode = 6

    for label in labels:
        generic_match = label.replace('"', '').split('/')[2]
        if generic_match:
            generic_node_match = re.search(
                r'{}(\s*{{\s*[^}}]+}})'.format(re.escape(generic_match)), content)
            gem_num += 1
            if generic_node_match:
                generic_node_content = generic_node_match.group(1)
                non_removable_match = re.search(
                    r'non-removable(\s*;)?', generic_node_content)
                generic_status_match = re.search(
                    r'status\s*=\s*"([^"]+)"', generic_node_content)
                if generic_status_match:
                    generic_status = generic_status_match.group(1)

        if (generic_node_match and non_removable_match) and (generic_status == "okay" or not generic_status_match):
            return emmc_mode
        elif generic_node_match and (generic_status == "okay" or not generic_status_match):
            counter.append(gem_num-1)

    return counter

def AddPmuConf(args, proot, arch, prebuilt, rootfs_type):
    '''Add pmc-conf.bin file to bootparam dict'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    before_load = ''
    after_load = ''
    ExtRootfs = ''
    global SkipAddWic
    global ExtraArgs
    PmuConf = os.path.join(images_dir, plnx_vars.BootFileNames['PMUCONF'])
    key = 'RFS_FILE_%s_%s' % (args.command.upper(), arch.upper())
    YoctoMachine = plnx_utils.get_config_value(plnx_vars.YoctoMachineConf, plnx_vars.SysConfFile.format(proot))
    # using wic for SOM in pivot rootfs enabled cases
    if YoctoMachine in ('xilinx-k26-som', 'xilinx-k26-kv', 'xilinx-k24-som', 'xilinx-k24-kd'):
        WicImage = os.path.join(images_dir, 'petalinux-sdimage.wic')
        # Looping through given qemu-args
        for qargs in args.qemu_args:
            # Splitting Qemu args with space
            for qarg in qargs.split():
                if  re.search('if=sd', qarg) or re.search('if=none', qarg):
                    SkipAddWic = True
                    # Splitting the sd args with ,
                    for SdArgs in qarg.split(','):
                        if 'file=' in SdArgs:
                            SdImage = SdArgs.replace('file=', '')
                            if os.path.exists(SdImage):
                                plnx_utils.MakePowerof2(SdImage)
                            else:
                                logger.error('Provided SdImage:%s does not exists' % SdImage)
        if SkipAddWic == False:
            ExtRootfs = WicImage
    else:
        ExtRootfs = os.path.join(images_dir, plnx_vars.BootFileNames[key])
    if os.path.exists(PmuConf):
        plnx_utils.add_dictkey(boot_common.BootParams, 'PMUCONF', 'Path', PmuConf)
        before_load = ' -global xlnx,zynqmp-boot.cpu-num=0 -global xlnx,zynqmp-boot.use-pmufw=true  -global xlnx,zynqmp-boot.drive=pmu-cfg -blockdev node-name=pmu-cfg,filename='
        plnx_utils.add_dictkey(boot_common.BootParams, 'PMUCONF',
                               'BeforeLoad', before_load)
        after_load += ',driver=file'
        plnx_utils.add_dictkey(boot_common.BootParams,
                               'PMUCONF', 'AfterLoad', after_load)
    else:
        # If pmu-conf does not exists
        ExtraArgs += ' -global xlnx,zynqmp-boot.cpu-num=0 -global xlnx,zynqmp-boot.use-pmufw=true'
    if ExtRootfs and (prebuilt == 3 or args.kernel):
        before_load = ''
        if rootfs_type == 'INITRD' or rootfs_type == 'INITRAMFS':
            # Add ramdisk image if switch_root enabled
            initramfs_image = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_INITRAMFS_IMAGE_NAME',
                                                          plnx_vars.SysConfFile.format(proot))
            if initramfs_image.find('initramfs') != -1:
                plnx_utils.MakePowerof2(ExtRootfs)
                plnx_utils.add_dictkey(boot_common.BootParams, 'EXTROOTFS', 'Path', ExtRootfs)
                before_load += ' -drive if=sd,format=raw,index=1,file='
                plnx_utils.add_dictkey(boot_common.BootParams,
                                       'EXTROOTFS', 'BeforeLoad', before_load)


def AddBootHeader(proot, arch, prebuilt):
    '''Add Bootbh.bin file to bootparam dict'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if arch in ('versal', 'versal-net'):
        BootBh = os.path.join(images_dir, plnx_vars.BootFileNames['BOOTBH'])
        plnx_utils.add_dictkey(boot_common.BootParams,
                               'BOOTBH', 'Path', BootBh)
        before_load = ' -device loader,file='
        after_load = ',addr=0xf201e000,force-raw=on '
        plnx_utils.add_dictkey(boot_common.BootParams,
                               'BOOTBH', 'BeforeLoad', before_load)
        plnx_utils.add_dictkey(boot_common.BootParams,
                               'BOOTBH', 'AfterLoad', after_load)


def AddHwDtb(proot, multiarch, DtbArch, prebuilt):
    '''Add hwdtb file to bootparam dict'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if multiarch == 'n':
        HwDtbFile = os.path.join(
            images_dir, QemuHwDtb['no_multi_arch'])
    else:
        HwDtbFile = os.path.join(images_dir, QemuHwDtb[DtbArch])
    plnx_utils.add_dictkey(boot_common.BootParams, 'HWDTB', 'Path', HwDtbFile)
    before_load = ' -hw-dtb '
    plnx_utils.add_dictkey(boot_common.BootParams,
                           'HWDTB', 'BeforeLoad', before_load)


def AddQemuBootBin(proot, arch, args, QemuCmd):
    '''Add qemu bootbin file to bootparam dict'''
    global SkipAddWic
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if args.prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    bootfile = os.path.join(images_dir, plnx_vars.BootFileNames['QEMUIMG'])
    plnx_utils.add_dictkey(boot_common.BootParams,
                           'QemuBootBin', 'Path', bootfile)
    MmcEthValue = FindMmcAndGemStatus(os.path.join(images_dir, plnx_vars.BootFileNames['DTB']))
    Mmc = str(MmcEthValue[0]).strip('[]')
    Eth = str(MmcEthValue[1]).strip('[]').strip(',')
    BootMode, Index = AutoMmc(Mmc, args, QemuCmd)
    if arch in ['versal', 'versal-net']:
        if SkipAddWic == True:
            before_load = ' -boot mode=%s -drive if=sd,index=%s,file=' % (
                BootMode, Index)
            plnx_utils.add_dictkey(boot_common.BootParams, 'QemuBootBin',
                                   'BeforeLoad', before_load)
            after_load = ',format=raw '
            plnx_utils.add_dictkey(boot_common.BootParams,
                                   'QemuBootBin', 'AfterLoad', after_load)
    else:
        before_load = ' -device loader,file='
        plnx_utils.add_dictkey(boot_common.BootParams, 'QemuBootBin',
                               'BeforeLoad', before_load)
        after_load = ',cpu-num=%s ' % (args.targetcpu)
        plnx_utils.add_dictkey(boot_common.BootParams,
                               'QemuBootBin', 'AfterLoad', after_load)


def QemuArchSetup(imgarch, imgendian, pmufw):
    '''returning qemu cmd and qemu machine'''
    qemu = ''
    qemu_mach = ''
    if imgarch == 'microblaze':
        if imgendian == 'little':
            qemu = 'qemu-system-microblazeel'
        elif imgendian == 'big':
            qemu = 'qemu-system-microblaze'
        else:
            logger.error('Unable to detect target endianness')
        if pmufw == 'y':
            qemu_mach = '-M microblaze-fdt'
        else:
            qemu_mach = '-M microblaze-fdt-plnx -m 256'
    elif imgarch == 'arm':
        qemu = 'qemu-system-aarch64'
        qemu_mach = '-M arm-generic-fdt-7series -machine linux=on'
    elif imgarch == 'aarch64':
        qemu = 'qemu-system-aarch64'
        qemu_mach = '-M arm-generic-fdt'
    else:
        logger.error('Unable to detect CPU architecture')
    return qemu, qemu_mach


def RunGenQemuCmd(proot, QemuCmd, QemuMach, args, BootParams, TftpDir, rootfs_type):
    '''Run arch specific qemu command'''
    QemuGenCmd = ''
    global SkipAddWic
    global ExtraArgs
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if args.prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    DtbFile = os.path.join(images_dir, plnx_vars.BootFileNames['DTB'])
    QemuGenCmd += '%s %s %s' % (QemuCmd, QemuMach,
                                AutoSerial(DtbFile, args, QemuCmd))
    for BootParam in QemuAarchBootFiles[args.xilinx_arch]:
        if BootParam in BootParams.keys():
            QemuGenCmd += BootParams[BootParam].get('BeforeLoad', '')
            QemuGenCmd += BootParams[BootParam].get('Path', '')
            QemuGenCmd += BootParams[BootParam].get('AfterLoad', '')
    MmcEthValue = FindMmcAndGemStatus(DtbFile)
    Mmc = str(MmcEthValue[0]).strip('[]')
    Eth = str(MmcEthValue[1]).strip('[]').strip(',')
    if not args.qemu_no_gdb:
        QemuGenCmd += ' -gdb tcp:localhost:%s ' % plnx_utils.get_free_port()
    QemuGenCmd += AutoEth(Eth, TftpDir)
    if args.xilinx_arch in ('zynqmp', 'versal', 'versal-net'):
        QemuGenCmd += ' -machine-path %s ' % MachineDir
    if rootfs_type == 'EXT4' and SkipAddWic == False:
        sd_provided = False
        WicImage = os.path.join(images_dir, 'petalinux-sdimage.wic')
        if not os.path.exists(WicImage):
            logger.error('File: %s Not found, This is required to boot the EXT4 Root file system type' % WicImage)
        for qarg in args.qemu_args:
            if re.search('if=sd', qarg):
                sd_provided = True
        if sd_provided == False:
            plnx_utils.MakePowerof2(WicImage)
            if args.arch == 'aarch64' and QemuCmd == 'qemu-system-aarch64':
                QemuGenCmd +=" -boot mode=5 -drive if=sd,index=1,file=%s,format=raw" % WicImage
            elif args.xilinx_arch == 'zynq':
                QemuGenCmd +=" -boot mode=5 -drive if=sd,index=0,file=%s,format=raw" % WicImage
    if args.xilinx_arch == 'zynq':
        ExtraArgs = ' -device loader,addr=0xf8000008,data=0xDF0D,data-len=4 -device loader,addr=0xf8000140,data=0x00500801,data-len=4 -device loader,addr=0xf800012c,data=0x1ed044d,data-len=4 -device loader,addr=0xf8000108,data=0x0001e008,data-len=4 -device loader,addr=0xF8000910,data=0xF,data-len=0x4'
    QemuGenCmd += ExtraArgs
    if args.qemu_args:
        for qarg in args.qemu_args:
            if isinstance(qarg, str) and re.search('-tftp=', qarg):
                i = args.qemu_args.index(qarg)
                args.qemu_args = args.qemu_args[:i]+['']+args.qemu_args[i+1:]
        QemuGenCmd += ' %s' % '\n'.join(args.qemu_args)
	# if -m not passed in qemu extra args
        if not '-m' in args.qemu_args[0].split():
            QemuGenCmd += '%s ' % QemuMemArgs.get(args.xilinx_arch, '')
    else:
        QemuGenCmd += '%s ' % QemuMemArgs.get(args.xilinx_arch, '')
    logger.info(QemuGenCmd)
    stdout = plnx_utils.runCmd(QemuGenCmd, os.getcwd(),
                               failed_msg='Fail to launch qemu cmd', shell=True, checkcall=True)


def RunMbQemuCmd(proot, QemuCmd, QemuMach, args, BootParams):
    '''Run multi arch microblaze qemu command'''
    QemuMbCmd = ''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if args.prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    DtbFile = os.path.join(images_dir, plnx_vars.BootFileNames['DTB'])
    QemuMbCmd += '%s %s %s' % (QemuCmd, QemuMach,
                               AutoSerial(DtbFile, args, QemuCmd))
    for BootParam in QemuMbBootFiles[args.xilinx_arch]:
        if BootParam in BootParams.keys():
            QemuMbCmd += BootParams[BootParam].get('BeforeLoad', '')
            QemuMbCmd += BootParams[BootParam].get('Path', '')
            QemuMbCmd += BootParams[BootParam].get('AfterLoad', '')
    QemuMbCmd += ' -machine-path %s' % MachineDir
    if args.xilinx_arch == 'zynqmp':
        QemuMbCmd += ' -device loader,addr=0xfd1a0074,data=0x1011003,data-len=4 -device loader,addr=0xfd1a007C,data=0x1010f03,data-len=4 &'
    elif args.xilinx_arch in ('versal', 'versal-net'):
        QemuMbCmd += ' -device loader,addr=0xF1110624,data=0x0,data-len=4 -device loader,addr=0xF1110620,data=0x1,data-len=4 &'
    logger.info(QemuMbCmd)
    stdout = plnx_utils.runCmd(QemuMbCmd, os.getcwd(),
                               failed_msg='Fail to launch qemu cmd', shell=True, checkcall=True)


def QemuBootSetup(args, proot):
    '''QEMU BootFiles setup.
    Add Each BootFile to the Dictionary based on the platform'''
    user = getpass.getuser()
    pmufw = 'n'
    ExtraArgs = ''
    tftp_dir = ''
    tftp_dir_disable = ''
    global SkipAddWic
    if user == 'root':
        logger.warn('root user')
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)
    if args.arch == ' ' or args.xilinx_arch == ' ':
        logger.error('Unable to get system architecture.')

    sysconf = plnx_vars.SysConfFile.format(proot)
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if args.prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    # Use Prebuilt conf if exists
    if args.prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
        sysconf = plnx_vars.PreBuildsSysConf.format(proot)
    rootfs_type = plnx_utils.get_config_value(
        'CONFIG_SUBSYSTEM_ROOTFS_', sysconf, 'choice')
    # Check directories exists or not
    if args.prebuilt and not os.path.exists(
            plnx_vars.PreBuildsImagesDir.format(proot)):
        logger.error('Failed to Boot --prebuilt %s, %s Directory not found'
                     % (args.prebuilt, plnx_vars.PreBuildsImagesDir.format(proot)))
        sys.exit(255)
    if (args.u_boot or args.kernel) and not os.path.exists(
            plnx_vars.BuildImagesDir.format(proot)):
        logger.error('Failed to Boot, %s Directory not found'
                     % (plnx_vars.BuildImagesDir.format(proot)))
        sys.exit(255)
    if args.arch == 'aarch64':
        imgarch = 'microblaze'
        pmufw = 'y'
    else:
        imgarch = args.arch
        pmufw = 'n'

    for qarg in args.qemu_args:
        if isinstance(qarg, str) and re.search('-tftp=', qarg):
            tftp_dir = qarg.split('=')[1]
            if args.tftp:
                logger.info(
                    'tftp command passed to petalinux-boot will be ignored as -tftp is mentioned in qemu-args')
    if args.tftp:
        tftp_dir = args.tftp
    else:
        tftp_dir = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_TFTPBOOT_DIR',
                                               plnx_vars.SysConfFile.format(proot))
        tftp_dir_disable = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_COPY_TO_TFTPBOOT',
                                                       plnx_vars.SysConfFile.format(proot))
    if not tftp_dir and tftp_dir_disable == 'y':
        if args.prebuilt > 1:
            tftp_dir = plnx_vars.PreBuildsImagesDir.format(proot)
        else:
            tftp_dir = plnx_vars.BuildImagesDir.format(proot)
    logger.info('Set QEMU tftp to "%s"' % tftp_dir)
    # check whether wic image generation required or not
    if args.u_boot or args.prebuilt == '2':
        SkipAddWic = True
    if args.xilinx_arch in ('versal', 'versal-net'):
        SkipAddWic = True

    if imgarch == 'microblaze' and pmufw == 'y':
        QemuMbCmd = ''
        QemuCmd, QemuMach = QemuArchSetup(imgarch, DEFAULT_ENDIAN, pmufw)
        if QemuCmd == '' or QemuMach == '':
            logger.error('Failed to detect QEMU ARCH for image')
        boot_common.AddPmuFile(proot, args.xilinx_arch, args.command,
                               args.targetcpu, args.prebuilt)
        AddHwDtb(proot, 'y', MbHwDtbMap[args.xilinx_arch], args.prebuilt)
        # to add pmu rom elf and pmc cdo
        boot_common.AddFsblFile(proot, args.xilinx_arch,
                                args.command, args.targetcpu, args.prebuilt)
        if args.xilinx_arch in ('versal', 'versal-net'):
            # to add boot header
            AddBootHeader(proot, args.xilinx_arch, args.prebuilt)
        # running qemu-microblazeel
        RunMbQemuCmd(proot, QemuCmd, QemuMach, args, boot_common.BootParams)
    QemuCmd, QemuMach = QemuArchSetup(args.arch, DEFAULT_ENDIAN, pmufw)
    if QemuCmd == '' or QemuMach == '':
        logger.error('Failed to detect QEMU ARCH for image')
    if args.xilinx_arch in ('versal', 'versal-net'):
        AddQemuBootBin(proot, args.xilinx_arch, args, QemuCmd)
    if args.xilinx_arch == 'zynqmp':
        boot_common.AddTfaFile(proot, args.xilinx_arch,
                               args.command, args.prebuilt)
        AddPmuConf(args, proot, args.arch, args.prebuilt, rootfs_type)
    if args.xilinx_arch in ('zynqmp', 'versal', 'versal-net'):
        AddHwDtb(proot, 'y', HwDtbMap[args.xilinx_arch], args.prebuilt)
    if args.prebuilt == 2 or args.u_boot:
        if args.xilinx_arch in ('versal', 'versal-net'):
            if args.u_boot:
                plnx_utils.add_dictkey(boot_common.BootParams, 'UBOOT', 'Path', '')
            if args.dtb:
                plnx_utils.add_dictkey(boot_common.BootParams, 'DTB', 'Path', '')
        if args.xilinx_arch in ('microblaze', 'zynq', 'zynqmp'):
            boot_common.AddUbootFile(
                proot, args.u_boot, args.xilinx_arch, args.targetcpu,
                args.command, args.prebuilt)
            boot_common.AddDtbFile(proot, args.dtb, args.command,
                                   args.xilinx_arch, args.prebuilt)
        if args.xilinx_arch == 'zynq':
            ZynqDtbFile = os.path.join(
                images_dir, plnx_vars.BootFileNames['DTB'])
            plnx_utils.add_dictkey(
                boot_common.BootParams, 'ZynqDTB', 'Path', ZynqDtbFile)
            before_load = ' -device loader,file='
            after_load = ',addr=0x00100000 '
            plnx_utils.add_dictkey(
                boot_common.BootParams, 'ZynqDTB', 'BeforeLoad', before_load)
            plnx_utils.add_dictkey(
                boot_common.BootParams, 'ZynqDTB', 'AfterLoad', after_load)
    if args.prebuilt == 3 or args.kernel:
        boot_common.AddKernelFile(proot, args.kernel, args.arch, args.xilinx_arch,
                                  args.command, args.prebuilt)
        if args.xilinx_arch in ('microblaze', 'zynq', 'zynqmp'):
            boot_common.AddDtbFile(proot, args.dtb, args.command,
                                   args.xilinx_arch, args.prebuilt)
        if args.xilinx_arch == 'zynqmp':
            boot_common.AddUbootFile(
                proot, args.u_boot, args.xilinx_arch, args.targetcpu,
                args.command, args.prebuilt)
            boot_common.AddBootScriptFile(
                proot, args.xilinx_arch, args.boot_script,
                args.command, args.targetcpu, args.prebuilt)
        if rootfs_type == 'INITRD':
            boot_common.AddRootfsFile(
                proot, args.rootfs, args.arch, args.xilinx_arch, args.command, args.prebuilt)
    # Validate Files
    boot_common.ValidateFiles(args.command)
    # running arch qemu
    RunGenQemuCmd(proot, QemuCmd, QemuMach, args,
                  boot_common.BootParams, tftp_dir, rootfs_type)


def QemuBootArgs(qemu_parser):
    qemu_parser.add_argument('--prebuilt', metavar='<BOOT_LEVEL>', type=int, choices=range(2, 4),
                             help='Boot prebuilt images (override all settings).'
                             '\nSupported boot levels 2 to 3'
                             '\n2 - Boot U-Boot only\n3 - Boot Linux Kernel only'
                             )
    qemu_parser.add_argument('--u-boot', '--uboot', type=boot_common.add_bootfile('UBOOT'),
                             nargs='?', default='', const='Default',
                             help='Boot images/linux/u-boot.elf image'
                             '\nif --kernel is specified, --u-boot will not take effect.',
                             )
    qemu_parser.add_argument('--kernel', type=boot_common.add_bootfile('KERNEL'),
                             nargs='?', default='', const='Default',
                             help='Boot images/linux/zImage for Zynq'
                             '\nBoot images/linux/Image for ZynqMP, versal and versal-net.'
                             '\nBoot images/linux/image.elf for MicroBlaze'
                             )
    qemu_parser.add_argument('--dtb', metavar='DTB', type=boot_common.add_bootfile('DTB'),
                             nargs='?', default='', const='Default',
                             help='force use of a particular device tree file.'
                             '\nif not specified, QEMU uses'
                             '\n<PROJECT>/images/linux/system.dtb')
    qemu_parser.add_argument('--tftp', help='Path to tftp folder')
    qemu_parser.add_argument('--qemu-args', metavar='QEMU_ARGUMENTS', action='append', default=[],
                             help='extra arguments to QEMU command')
    qemu_parser.add_argument(
        '--pmu-qemu-args', help='extra arguments for pmu instance of qemu <ZynqMP>')
    qemu_parser.add_argument('--rootfs', metavar='ROOTFS_CPIO_FILE', type=boot_common.add_bootfile('ROOTFS'),
                             nargs='?', default='', const='Default',
                             help='Specify the cpio rootfile system needs to be used for boot.'
                             '\nSupports for: zynq, zynqMP, versal, versal-net and microblaze.')
    qemu_parser.add_argument(
        '--qemu-no-gdb', action='store_true', help='Specify this option to disable gdb via qemu boot.')
    qemu_parser.add_argument('--targetcpu', metavar='TARGET_CPU', default=0,
                             type=int, help='Specify target CPUID (0 to N-1)')
    qemu_parser.add_argument('--boot-script', type=boot_common.add_bootfile('BOOTSCRIPT'),
                             nargs='?', default='', const='Default',
                             help='Specify the boot.scr path')
    qemu_parser.set_defaults(func=QemuBootSetup)

    return
