#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Varalaxmi Bingi <varalaxmi.bingi@amd.com>
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

scripts_path = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('PetaLinux')

ProjectEssentials = 'pre-built project-spec components .petalinux user .gitignore README README.hw'

# Global variables
# machine path
MachineDir = tempfile.mkdtemp()
# default endian
DEFAULT_ENDIAN = 'little'
# default gdb args
QemuGdbArgs = ' -gdb tcp::9000 '

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

MbQemuSerialArgs = {
    'zynqmp': ' -serial mon:stdio -serial /dev/null -display none ',
    'versal': ' -serial mon:stdio -display none ',
    'versal-net': ' -serial mon:stdio -display none '
}

ArchQemuSerialArgs = {
    'microblaze': ' -serial mon:stdio -display none ',
    'zynq': ' -serial /dev/null -serial mon:stdio -display none ',
    'zynqmp': ' -serial mon:stdio -serial /dev/null -display none ',
    'versal': ' -serial null -serial null  -serial mon:stdio -serial /dev/null -display none ',
    'versal-net': ' -serial null -serial null  -serial mon:stdio -serial /dev/null -display none '
}

QemuEthArgs = {
    'microblaze': ' -net nic,netdev=eth0 -netdev user,id=eth0,',
    'zynq': ' -net nic,netdev=eth0 -netdev user,id=eth0,',
    'zynqmp': ' -net nic -net nic -net nic -net nic,netdev=eth3 -netdev user,id=eth3,',
    'versal': ' -net nic,netdev=eth0 -netdev user,id=eth0,tftp=/tftpboot -net nic,netdev=eth1 -netdev user,id=eth1,',
    'versal-net': ' -net nic -net nic,netdev=eth1 -netdev user,id=eth1,'
}

QemuMemArgs = {
    'microblaze': '',
    'zynq': '',
    'zynqmp': ' -m 4G ',
    'versal': ' -m 8G ',
    'versal-net': '-m 8G '
}


def AddPmuConf(args, proot, arch, prebuilt):
    '''Add pmc-conf.bin file to bootparam dict'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    before_load = ''
    after_load = ''
    PmuConf = os.path.join(images_dir, plnx_vars.BootFileNames['PMUCONF'])
    key = 'RFS_FILE_%s_%s' % (args.command.upper(), arch.upper())
    ExtRootfs = os.path.join(images_dir, plnx_vars.BootFileNames[key])
    plnx_utils.add_dictkey(boot_common.BootParams, 'PMUCONF', 'Path', PmuConf)
    before_load = ' -global xlnx,zynqmp-boot.cpu-num=0 -global xlnx,zynqmp-boot.use-pmufw=true  -global xlnx,zynqmp-boot.drive=pmu-cfg -blockdev node-name=pmu-cfg,filename='
    plnx_utils.add_dictkey(boot_common.BootParams, 'PMUCONF',
                           'BeforeLoad', before_load)
    after_load += ',driver=file'
    if prebuilt == 3 or args.kernel:
        after_load += ' -drive if=sd,format=raw,index=1,file='
        after_load += ExtRootfs
    plnx_utils.add_dictkey(boot_common.BootParams,
                           'PMUCONF', 'AfterLoad', after_load)


def AddBootHeader(proot, arch, prebuilt):
    '''Add Bootbh.bin file to bootparam dict'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    if arch in ['versal', 'versal-net']:
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


def AddQemuBootBin(proot, arch, prebuilt):
    '''Add qemu bootbin file to bootparam dict'''
    images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if prebuilt \
        else plnx_vars.BuildImagesDir.format(proot)
    bootfile = os.path.join(images_dir, plnx_vars.BootFileNames['QEMUIMG'])
    plnx_utils.add_dictkey(boot_common.BootParams,
                           'QemuBootBin', 'Path', bootfile)
    if arch == 'versal':
        before_load = ' -boot mode=5 -drive if=sd,index=1,file='
    elif arch == 'versal-net':
        before_load = ' -boot mode=6 -drive if=sd,index=1,file='
    plnx_utils.add_dictkey(boot_common.BootParams, 'QemuBootBin',
                           'BeforeLoad', before_load)
    after_load = ',format=raw'
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


def RunGenQemuCmd(QemuCmd, QemuMach, args, BootParams, TftpDir, prebuilt):
    '''Run arch specific qemu command'''
    QemuGenCmd = ''
    QemuGenCmd += '%s %s %s' % (QemuCmd, QemuMach,
                                ArchQemuSerialArgs[args.xilinx_arch])
    for BootParam in BootParams:
        if BootParams[BootParam].get('BeforeLoad'):
            QemuGenCmd += BootParams[BootParam].get('BeforeLoad')
        if BootParams[BootParam].get('Path'):
            QemuGenCmd += BootParams[BootParam].get('Path')
        if BootParams[BootParam].get('AfterLoad'):
            QemuGenCmd += BootParams[BootParam].get('AfterLoad')
    QemuGenCmd += "%s %stftp=%s %s" % (QemuGdbArgs, QemuEthArgs[args.xilinx_arch], TftpDir,
                                       QemuMemArgs[args.xilinx_arch])
    if args.xilinx_arch in ['zynqmp', 'versal', 'versal-net']:
        QemuGenCmd += ' -machine-path %s' % MachineDir
    if args.xilinx_arch == 'zynq':
        ExtraArgs = '-device loader,addr=0xf8000008,data=0xDF0D,data-len=4 -device loader,addr=0xf8000140,data=0x00500801,data-len=4 -device loader,addr=0xf800012c,data=0x1ed044d,data-len=4 -device loader,addr=0xf8000108,data=0x0001e008,data-len=4 -device loader,addr=0xF8000910,data=0xF,data-len=0x4'
        QemuGenCmd += ExtraArgs
    logger.info(QemuGenCmd)
    stdout = plnx_utils.runCmd(QemuGenCmd, os.getcwd(),
                               failed_msg='Fail to launch qemu cmd', shell=True, checkcall=True)


def RunMbQemuCmd(QemuCmd, QemuMach, args, BootParams):
    '''Run multi arch microblaze qemu command'''
    QemuMbCmd = ''
    QemuMbCmd += '%s %s %s' % (QemuCmd, QemuMach,
                               MbQemuSerialArgs[args.xilinx_arch])
    for BootParam in BootParams:
        if BootParams[BootParam].get('BeforeLoad'):
            QemuMbCmd += BootParams[BootParam].get('BeforeLoad')
        if BootParams[BootParam].get('Path'):
            QemuMbCmd += BootParams[BootParam].get('Path')
        if BootParams[BootParam].get('AfterLoad'):
            QemuMbCmd += BootParams[BootParam].get('AfterLoad')
    QemuMbCmd += ' -machine-path %s' % MachineDir
    if args.xilinx_arch == 'zynqmp':
        QemuMbCmd += ' -device loader,addr=0xfd1a0074,data=0x1011003,data-len=4 -device loader,addr=0xfd1a007C,data=0x1010f03,data-len=4 &'
    elif args.xilinx_arch in ['versal', 'versal-net']:
        QemuMbCmd += ' -device loader,addr=0xF1110624,data=0x0,data-len=4 -device loader,addr=0xF1110620,data=0x1,data-len=4 &'
    logger.info(QemuMbCmd)
    stdout = plnx_utils.runCmd(QemuMbCmd, os.getcwd(),
                               failed_msg='Fail to launch qemu cmd', shell=True, checkcall=True)


def QemuBootSetup(args, proot):
    '''QEMU BootFiles setup.
    Add Each BootFile to the Dictionary based on the platform'''
    user = getpass.getuser()
    boot_path = os.path.join(scripts_path + '/../bash/' + 'petalinux-boot')
    stdout = plnx_utils.runCmd('%s --qemu %s' % (boot_path, (' '.join(sys.argv[2:]))), os.getcwd(),
                               failed_msg='Fail to launch qemu cmd', shell=True, checkcall=True)
    sys.exit(255)
    pmufw = 'n'
    ExtraArgs = ''
    if user == 'root':
        logger.warn('root user')
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)
    if args.arch == ' ' or args.xilinx_arch == ' ':
        logger.error('Unable to get system architecture.')

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

    if not '-tftp' in args.qemu_args:
        if args.tftp:
            tftp_dir = args.tftp
        else:
            tftp_dir = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_TFTPBOOT_DIR',
                                                   plnx_vars.SysConfFile.format(proot))
            tftp_dir_disable = plnx_utils.get_config_value('CONFIG_SUBSYSTEM_COPY_TO_TFTPBOOT',
                                                           plnx_vars.SysConfFile.format(proot))
        if tftp_dir and tftp_dir_disable == 'n':
            ImagesDir = plnx_vars.BuildImagesDir.format(proot)
            if os.path.isdir(ImagesDir):
                numoffiles = os.listdir(ImagesDir)
                if len(numoffiles) > 3:
                    tftp_dir = ImagesDir
                else:
                    tftp_dir = plnx_vars.PreBuildsImagesDir.format(proot)
            else:
                tftp_dir = plnx_vars.PreBuildsImagesDir.format(proot)
            logger.info('Set QEMU tftp to "%s"' % tftp_dir)
        else:
            if args.tftp:
                logger.info(
                    'tftp command passed to petalinux-boot will be ignored as -tftp is mentioned in qemu-args')

    if imgarch == 'microblaze' and pmufw == 'y':
        QemuMbCmd = ''
        boot_common.BootParams = dict()
        QemuCmd, QemuMach = QemuArchSetup(imgarch, args.endian, pmufw)
        if QemuCmd == '' or QemuMach == '':
            logger.error('Failed to detect QEMU ARCH for image')
        boot_common.AddPmuFile(proot, args.xilinx_arch, args.command,
                               args.targetcpu, args.prebuilt)
        AddHwDtb(proot, 'y', MbHwDtbMap[args.xilinx_arch], args.prebuilt)
        # to add pmu rom elf and pmc cdo
        boot_common.AddFsblFile(proot, args.xilinx_arch,
                                args.command, args.targetcpu, args.prebuilt)
        if args.xilinx_arch in ['versal', 'versal-net']:
            # to add boot header
            AddBootHeader(proot, args.xilinx_arch, args.prebuilt)
        # running qemu-microblazeel
        RunMbQemuCmd(QemuCmd, QemuMach, args, boot_common.BootParams)
    boot_common.BootParams = dict()
    if args.xilinx_arch in ['versal', 'versal-net']:
        AddQemuBootBin(proot, args.xilinx_arch, args.prebuilt)
    if args.xilinx_arch == 'zynqmp':
        boot_common.AddTfaFile(proot, args.xilinx_arch,
                               args.command, args.prebuilt)
        AddPmuConf(args, proot, args.arch, args.prebuilt)
    if args.xilinx_arch in ['zynqmp', 'versal', 'versal-net']:
        AddHwDtb(proot, 'y', HwDtbMap[args.xilinx_arch], args.prebuilt)
    if args.prebuilt == 2 or args.u_boot:
        if args.xilinx_arch in ['microblaze', 'zynq', 'zynqmp']:
            boot_common.AddUbootFile(
                proot, args.u_boot, args.xilinx_arch, args.targetcpu,
                args.command, args.prebuilt)
            boot_common.AddDtbFile(proot, args.dtb, args.command,
                                   args.xilinx_arch, args.prebuilt)
        if args.xilinx_arch == 'zynq':
            images_dir = plnx_vars.PreBuildsImagesDir.format(proot) if args.prebuilt \
                else plnx_vars.BuildImagesDir.format(proot)
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
        if args.xilinx_arch in ['microblaze', 'zynq', 'zynqmp']:
            boot_common.AddDtbFile(proot, args.dtb, args.command,
                                   args.xilinx_arch, args.prebuilt)
        if args.xilinx_arch == 'zynqmp':
            boot_common.AddUbootFile(
                proot, args.u_boot, args.xilinx_arch, args.targetcpu,
                args.command, args.prebuilt)
            boot_common.AddBootScriptFile(
                proot, args.xilinx_arch, args.boot_script,
                args.command, args.targetcpu, args.prebuilt)
        sysconf = plnx_vars.SysConfFile.format(proot)
        # Use Prebuilt conf if exists
        if args.prebuilt and os.path.exists(plnx_vars.PreBuildsSysConf.format(proot)):
            sysconf = plnx_vars.PreBuildsSysConf.format(proot)
        rootfs_type = plnx_utils.get_config_value(
            'CONFIG_SUBSYSTEM_ROOTFS_', sysconf, 'choice')
        if rootfs_type == 'INITRD':
            boot_common.AddRootfsFile(
                proot, args.rootfs, args.arch, args.xilinx_arch, args.command, args.prebuilt)
    # Validate Files
    boot_common.ValidateFiles(args.command)
    QemuCmd, QemuMach = QemuArchSetup(args.arch, args.endian, pmufw)
    if QemuCmd == '' or QemuMach == '':
        logger.error('Failed to detect QEMU ARCH for image')
    # running arch qemu
    RunGenQemuCmd(QemuCmd, QemuMach, args,
                  boot_common.BootParams, tftp_dir, args.prebuilt)


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
                             help='force use of a particular device tree file.'
                             '\nif not specified, QEMU uses'
                             '\n<PROJECT>/images/linux/system.dtb')
    qemu_parser.add_argument('--dhcpd', choices=['enable', 'disable'],
                             help='enable or disable dhcpd. This option applies'
                             '\nfor ROOT MODE ONLY.'
                             '\ndefault is to enable dhcpd.')
    qemu_parser.add_argument('--iptables-allowed', help='whether to allow to implement iptables commands.'
                             '\nThis option applies for ROOT MODE ONLY'
                             '\nDefault is not allowed.')
    qemu_parser.add_argument('--net-intf', metavar='NET_INTERFACE',
                             help='network interface on the host to bridge with'
                             '\nthe QEMU subnet. This option applies for ROOT'
                             '\nMODE ONLY. Default is eth0.')
    qemu_parser.add_argument('--subnet', metavar='SUBNET',
                             help='subnet_gateway_ip/num_bits_of_subnet_mask'
                             '\nsubnet gateway IP and the number of valid bits'
                             '\nof network mask. This option applies for ROOT'
                             '\nMODE ONLY. Default is 192.168.10.1/24')
    qemu_parser.add_argument('--tftp', help='Path to tftp folder')
    qemu_parser.add_argument('--qemu-args', metavar='QEMU_ARGUMENTS', action='append', default=[],
                             help='extra arguments to QEMU command')
    qemu_parser.add_argument(
        '--pmu-qemu-args', help='extra arguments for pmu instance of qemu <ZynqMP>')
    qemu_parser.add_argument('--rootfs', metavar='ROOTFS_CPIO_FILE',
                             help='Specify the cpio rootfile system needs to be used for boot.'
                             '\nSupports for: zynq,zynqMP and microblaze.')
    qemu_parser.add_argument(
        '--qemu-no-gdb', action='store_true', help='Specify this option to disable gdb via qemu boot.')
    qemu_parser.add_argument('--targetcpu', metavar='TARGET_CPU', default=0,
                             type=int, help='Specify target CPUID (0 to N-1)')
    qemu_parser.add_argument('--targetcluster', metavar='TARGET_CLUSTER', default=0,
                             type=int, help='Specify target cluster (0 to N-1)')
    qemu_parser.add_argument('--endian', metavar='ENDIAN', default='little',
                             help='Specify the image endian')
    qemu_parser.add_argument('--boot-script', type=boot_common.add_bootfile('BOOTSCRIPT'),
                             nargs='?', default='', const='Default',
                             help='Specify the boot.scr path')
    qemu_parser.set_defaults(func=QemuBootSetup)

    return
