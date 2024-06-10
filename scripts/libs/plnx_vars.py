#!/usr/bin/env python3
#
# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import os
import sys

''' Project Configurations'''
ProotSub = '{0:s}'
ImagesDir = os.path.join('images', 'linux')
BuildImagesDir = os.path.join(ProotSub, ImagesDir)
PreBuildsDir = os.path.join(ProotSub, 'pre-built', 'linux')
ImpPreBuildsDir = os.path.join(
    ProotSub, 'pre-built', 'linux', 'implementation')
PreBuildsImagesDir = os.path.join(PreBuildsDir, 'images')
PreBuildsSysConf = os.path.join(PreBuildsImagesDir, 'config')
BuildDir = os.path.join(ProotSub, 'build')
ConfDir = os.path.join(BuildDir, 'conf')
ArchiverConfFile = os.path.join(ConfDir, 'archiver.conf')
DevtoolConfFile = os.path.join(ConfDir, 'devtool.conf')
BBLayersConf = os.path.join(ConfDir, 'bblayers.conf')
LocalConf = os.path.join(ConfDir, 'local.conf')
PlnxToolConf = os.path.join(ConfDir, 'plnxtool.conf')
SdtAutoConf = os.path.join(ConfDir, 'sdt-auto.conf')
EsdkInstalledDir = os.path.join(ProotSub, 'components', 'yocto')
PlnxWorkspace = os.path.join(ProotSub, 'components', 'plnx_workspace')
GitIgnoreFile = os.path.join(ProotSub, '.gitignore')
ProjectSpec = os.path.join(ProotSub, 'project-spec')
MetaDataDir = os.path.join(ProotSub, '.petalinux')
MetaDataFile = os.path.join(MetaDataDir, 'metadata')
SysConfDir = os.path.join(ProjectSpec, 'configs')
SysConfFile = os.path.join(SysConfDir, 'config')
RfsConfig = os.path.join(SysConfDir, 'rootfs_config')
P_Interfaces = os.path.join(SysConfDir, 'init-ifupdown', 'interfaces')
P_SystemdWired = os.path.join(SysConfDir, 'systemd-conf', 'wired.network')
P_BusyBoxDir = os.path.join(SysConfDir, 'busybox')
P_InetDConf = os.path.join(P_BusyBoxDir, 'inetd.conf')
RecipesCore = os.path.join(EsdkInstalledDir, 'layers',
                           'poky', 'meta', 'recipes-core')
T_Interfaces = os.path.join(
    RecipesCore, 'init-ifupdown', 'init-ifupdown-1.0', 'interfaces')
T_SystemdWired = os.path.join(
    RecipesCore, 'systemd', 'systemd-conf', 'wired.ntwork')
T_InetDFile = os.path.join(EsdkInstalledDir, 'layers', 'meta-petalinux',
                           'recipes-core', 'busybox', 'files', 'inetd.conf')
MetaUserDir = os.path.join(ProjectSpec, 'meta-user')
HWDescDir = os.path.join(ProjectSpec, 'hw-description')
DefXsaPath = os.path.join(HWDescDir, 'system.xsa')
UsrRfsConfig = os.path.join(MetaUserDir, 'conf', 'user-rootfsconfig')
PlnxBspConfig = os.path.join(MetaUserDir, 'conf', 'petalinuxbsp.conf')
ConfigLogFile = os.path.join(BuildDir, 'config.log')
BuildLogFile = os.path.join(BuildDir, 'build.log')
DevtoolLogFile = os.path.join(BuildDir, 'devtool.log')
PkgFileName = 'package.log'
PackageLogFile = os.path.join(BuildDir, PkgFileName)
CfgMemDir = os.path.join(BuildDir, 'package-boot')
WicTmpWorkDir = os.path.join(BuildDir, 'wic')
GenMachLogFile = os.path.join(SysConfDir, 'gen-machineconf.log')
LockedSigsFile = os.path.join(EsdkInstalledDir, 'conf', 'locked-sigs.inc')
DevtoolFile = os.path.join(EsdkInstalledDir, '.devtoolbase')
OeInitEnv = os.path.join(EsdkInstalledDir, 'layers',
                         'poky', 'oe-init-build-env')
EsdkConfDir = os.path.join(EsdkInstalledDir, 'conf')
EsdkBBLayerconf = os.path.join(EsdkConfDir, 'bblayers.conf')
EnablePlnxTraceback = False
AutoCleanupFiles = []

'''Project Out Files'''
BootBINFile = os.path.join(BuildImagesDir, 'BOOT.BIN')
BootMCSFile = os.path.join(BuildImagesDir, 'boot.mcs')
BootMBMCSFile = os.path.join(BuildImagesDir, 'system.mcs')
BootDOWNLOADBITFile = os.path.join(BuildImagesDir, 'download.bit')
BifFile = os.path.join(BuildImagesDir, 'bootgen.bif')
SdkFile = os.path.join(ImagesDir, 'sdk.sh')
ESdkFile = os.path.join(ImagesDir, 'esdk.sh')
SdkOutFile = os.path.join(ProotSub, SdkFile)
ESdkOutFile = os.path.join(ProotSub, ESdkFile)
SdkDir = os.path.join(ImagesDir, 'sdk')
SdkInstallDir = os.path.join(ProotSub, SdkDir)
HsmOutFile = os.path.join(SysConfDir, 'flash_parts.txt')

'''Tool Configurations'''
PetaLinux = os.environ.get('PETALINUX', '')
Petainux_Major_Ver = os.environ.get('PETALINUX_MAJOR_VER', '')
PetaLinux_Ver_Str = 'PETALINUX_VER'
PetaLinux_Ver = os.environ.get(PetaLinux_Ver_Str, '')
BuildToolsEnvPath = os.path.join(PetaLinux,
                                 '.environment-setup-x86_64-petalinux-linux')
PetaLinuxSysroot = os.path.join(PetaLinux, 'sysroots')
YoctoSrcPath = os.path.join(PetaLinux, 'components', 'yocto')
SDTPrestepFile = os.path.join(
    YoctoSrcPath, 'decoupling', 'decouple-prestep.sh')
XsctPath = os.path.join(PetaLinux, 'components', 'xsct')
XsctBinPath = os.path.join(XsctPath, 'bin')
TemplateDir = os.path.join(PetaLinux, 'templates')
TemplateCommon = os.path.join(TemplateDir, '{0:s}', 'common')
TemplateDir_C = os.path.join(TemplateDir, '{0:s}', 'template-{1:s}')
DfuUtilBin = os.path.join(XsctPath, 'tps', 'lnx64', 'dfu-util-0.9', 'bin', 'dfu-util')
UpgradeLog = os.path.join(PetaLinux, 'update.log')
VersionFile = os.path.join(PetaLinux, '.version-history')

'''PATH variables'''
ospath = os.environ['PATH']
extra_ospaths = os.environ.get('EXTERNAL_TOOLS_PATH', '') + ':'
extra_ospaths += XsctBinPath + ':'
os.environ['PATH'] = extra_ospaths + ospath

'''BB_ENV variables'''
bb_extraenv = os.environ.get('BB_ENV_PASSTHROUGH_ADDITIONS', '')
plnx_bbenv = 'PETALINUX PETALINUX_VER PETALINUX_MAJOR_VER'
os.environ['BB_ENV_PASSTHROUGH_ADDITIONS'] = bb_extraenv + ' ' + plnx_bbenv

YoctoEnvPrefix = 'environment-setup'
YoctoEnvFile = {
    'aarch64': 'cortexa72-cortexa53-xilinx-linux',
    'arm': 'cortexa9t2hf-neon-xilinx-linux-gnueabi',
    'microblaze': 'microblazeel-v11.0-*-xilinx-linux'
}

LockedSigns = {
    'aarch64': 't-aarch64 t-allarch t-x86-64-aarch64 t-x86-64 t-x86-64-x86-64-nativesdk',
    'aarch64_dt': 't-aarch64 t-allarch t-x86-64-aarch64 t-x86-64 t-x86-64-x86-64-nativesdk',
    'arm': 't-allarch t-x86-64-x86-64-nativesdk t-x86-64 t-cortexa9t2hf-neon t-x86-64-arm',
    'microblaze': 't-x86-64 t-allarch t-x86-64-x86-64-nativesdk t-microblazeel-v11.0-bs-cmp-mh-div t-x86-64-microblazeel'
}

GUI_Components = {
    'uboot': 'virtual/bootloader', 'u-boot': 'virtual/bootloader',
    'kernel': 'virtual/kernel', 'linux-xlnx': 'virtual/kernel'
}

CMD_Components = {
    'pmufw': 'virtual/pmu-firmware', 'pmu-firmware': 'virtual/pmu-firmware',
    'fsbl': 'virtual/fsbl', 'fsbl-firmware': 'virtual/fsbl',
    'plm': 'virtual/plm', 'plm-firmware': 'virtual/plm',
    'psmfw': 'virtual/psm-firmware', 'psm-firmware': 'virtual/psm-firmware',
    'dtb': 'virtual/dtb', 'devicetree': 'virtual/dtb', 'device-tree': 'virtual/dtb',
    'fsboot': 'virtual/fsboot'
}

BootFileNames = {
    'TFA': 'bl31.elf',
    'FSBL_ZYNQ': 'zynq_fsbl.elf',
    'FSBL_ZYNQMP': 'zynqmp_fsbl.elf',
    'FSBL_MICROBLAZE': 'fs-boot.elf',
    'PMUFW': 'pmufw.elf',
    'PSMFW': 'psmfw.elf',
    'PLM': 'plm.elf',
    'DTB': 'system.dtb',
    'UBOOT': 'u-boot.elf',
    'UBOOT_MICROBLAZE': 'u-boot-s.bin',
    'KERNEL': 'image.ub',
    'KIMAGE_AARCH64': 'Image',
    'KIMAGE_ARM': 'uImage',
    'KIMAGE_QEMU_ARM': 'zImage',
    'KIMAGE_MICROBLAZE': 'linux.bin.ub',
    'KIMAGE_QEMU_MICROBLAZE': 'image.elf',
    'BOOTSCRIPT': 'boot.scr',
    'RFS_FILE': 'rootfs.cpio.gz.u-boot',
    'RFS_FILE_QEMU_AARCH64': 'rootfs.ext4',
    'TINY_RFS_FILE': 'ramdisk.cpio.gz.u-boot',
    'BOOTBIN': 'BOOT.BIN',
    'BOOTBH': 'BOOT_bh.bin',
    'OPENAMP': 'dtbos/openamp.dtbo',
    'QEMUIMG': 'qemu_boot.img',
    'PMCCDO': 'pmc_cdo.bin',
    'PMUROM': 'pmu_rom_qemu_sha3.elf',
    'PMUCONF': 'pmu-conf.bin'
}

DFX_Templates = {
    'dfx_user_dts': 'Generates PL application with the user specified dtsi and with .pdi/.bit files.'
                    '\nPack the .dtbo, .bin/.pdi, shell.json/accel.json and .xclbin into rootfs.'
                    '\nNote: Supports for versal, zynqmp and zynq.',
    'dfx_dtg_zynq_full': 'Generates the full PL application for zynq with specified flat xsa file.'
                         '\nPack the .dtbo, and bit.bin files into rootfs.',
    'dfx_dtg_zynqmp_full': 'Generates the full pl application for zynqmp with given flat xsa file.'
                           '\nPack the .dtbo,.bin and shell.json files into rootfs.',
    'dfx_dtg_versal_full': 'Generates the full pl application for versal with given flat xsa file.'
                           '\nPack the .dtbo,pl.pdi and shell.json files into rootfs.',
    'dfx_dtg_zynqmp_static': 'Generates the static pl application for zynqmp with given dfx static xsa file.'
                             '\nPack the .dtbo,.bin and shell.json files into rootfs.',
    'dfx_dtg_zynqmp_partial': 'Generates the partial pl application for zynqmp with given dfx partial xsa file.'
                              '\nPack the .dtbo, .bin and accel.json files into rootfs.'
                              '\nNote: This has dependency on dfx_dtg_zynqmp_static template app',
    'dfx_dtg_versal_static': 'Generates the static pl application for versal with given dfx static xsa file.'
                             '\nPack the .dtbo,.pdi and shell.json files into rootfs.',
    'dfx_dtg_versal_partial': 'Generates the partial pl application for versal with given dfx partial xsa file.'
                              '\nPack the .dtbo, .pdi and accel.json files into rootfs'
                              '\nNote: This has dependency on dfx_dtg_versal_static template app.'
}

GitIgnoreStr = '''
*/*/config.old
*/*/rootfs_config.old
build/
images/linux/
pre-built/linux/
.petalinux/*
!.petalinux/metadata
*.o
*.jou
*.log
components/plnx_workspace
components/yocto
'''

ArchiverStr = '''
INHERIT += "archiver"
ARCHIVER_MODE[src] = "original"
COPYLEFT_LICENSE_INCLUDE = ""
COPYLEFT_LICENSE_EXCLUDE = ""
'''

ArchiverconfStr = '''
do_populate_sdk[recrdeptask] += "do_populate_lic"
do_populate_sdk[recrdeptask] += "do_populate_lic"
'''

LocalConfStr = '''
include conf/archiver.conf
'''

BspFilesExcludeStr = '''
RCS\nSCCS\nCVS\nCVS.adm\nRCSLOG\ncvslog.*\ntags\nTAGS\n.make.state\n.nse_depinfo
*~\n.#*\n,*\n_$*\n*$\n*.old\n*.bak\n*.BAK\n*.orig\n*.rej\n.del-*\n*.olb\n*.o
*.obj\n*.exe\n*.Z\n*.elc\n*.ln\n.svn/\n.git/\n.bzr/\n:C\nyocto/
project-spec/configs/*.conf\nproject-spec/configs/configs/
project-spec/configs/rootfsconfigs/
'''
ActInterfaceStr = '''
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
ActWiredStr = '''
[Match]
Type=ether
Name=!veth*
KernelCommandLine=!nfsroot
KernelCommandLine=!ip
[Network]
Address={0}/{1}
Gateway={2}
'''
SystemconfBootargs = '''
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
SystemconfEth = '''
&{0} {{
    local-mac-address = [{1}];
}};
'''
SystemconfFlash = '''
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
FlashPartNode = '''
        partition@{0} {{
            label = "{1}";
            reg = <{2} {3}>;
            }};
'''
FlashendSymbols = '''\t};\n};\n'''

BifImagePrefix = 'the_ROM_image'


'''Config Variables'''
BuildToolsExtConf = 'CONFIG_YOCTO_BUILDTOOLS_EXTENDED'
YoctoMachineConf = 'CONFIG_YOCTO_MACHINE_NAME'
TmpDirConf = 'CONFIG_TMP_DIR_LOCATION'
DevtoolConf = 'CONFIG_DEVTOOL_WORKSPACE_LOCATION'
SOC_VariantConf = 'CONFIG_SUBSYSTEM_VARIANT_'
ARCH_Conf = 'CONFIG_SUBSYSTEM_ARCH_'
Xilinx_Arch_Conf = 'CONFIG_SYSTEM_'
AutoBootArgsConf = 'CONFIG_SUBSYSTEM_BOOTARGS_GENERATED'
BootArgsCmdLineConf = 'CONFIG_SUBSYSTEM_USER_CMDLINE'
FlashIpConf = 'CONFIG_SUBSYSTEM_FLASH_IP_NAME'
EthManualConf = 'CONFIG_SUBSYSTEM_ETHERNET_MANUAL_SELECT'
EthConfs = {
    'Prefix': 'CONFIG_SUBSYSTEM_ETHERNET_',
    'IPConf': '_IP_ADDRESS', 'IPNetMaskConf': '_IP_NETMASK',
    'IPGetWay': '_IP_GATEWAY', 'Dhcp': '_USE_DHCP',
    'Mac': '_MAC'
}
FlashConfs = {
    'Prefix': 'CONFIG_SUBSYSTEM_FLASH_',
    'Name': '_NAME', 'Size': '_SIZE'
}
MemoryConfs = {
    'Prefix': 'CONFIG_SUBSYSTEM_MEMORY_',
    'BaseAddr': '_BASEADDR='
}
ProcConfs = {
    'Prefix': 'CONFIG_SUBSYSTEM_PROCESSOR',
    'Select': '_SELECT=y', 'IpName': '_IP_NAME',
    'InstanceName': '_INSTANCE_PATH'
}
UbootConfs = {
    'AppendBase': 'CONFIG_SUBSYSTEM_UBOOT_APPEND_BASEADDR',
    'DtbOffset': 'CONFIG_SUBSYSTEM_UBOOT_DEVICETREE_OFFSET',
    'KernelOffset': 'CONFIG_SUBSYSTEM_UBOOT_KERNEL_OFFSET',
    'RootfsOffset': 'CONFIG_SUBSYSTEM_UBOOT_RAMDISK_IMAGE_OFFSET',
    'BootScrOffset': 'CONFIG_SUBSYSTEM_UBOOT_BOOTSCR_OFFSET'
}

'''XSCT commands'''
OpenHWCmd = 'openhw {0}'
HdfDataMacro = '@#%HDF_DATA@#%'
GetHWFilesCmd = 'set lu_data [hsi get_hw_files -filter {{TYPE == {0}}}];\
        puts "{1}${{lu_data}}"; exit;'
XsctFileIn = 'xsct -sdx -nodisp {0}'
XsdbConnectCmd = 'gdbremote connect {0}:{1} {2}'
