#!/usr/bin/env python3
#
# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import os
import sys

''' Project Configurations'''
ProotSub = '{0:s}'
ImagesDir = os.path.join('images', 'linux')
BuildImagesDir = os.path.join(ProotSub, ImagesDir)
PreBuildsDir = os.path.join(ProotSub, 'pre-built', 'linux', 'images')
BuildDir = os.path.join(ProotSub, 'build')
ConfDir = os.path.join(BuildDir, 'conf')
DevtoolConfFile = os.path.join(ConfDir, 'devtool.conf')
BBLayersConf = os.path.join(ConfDir, 'bblayers.conf')
LocalConf = os.path.join(ConfDir, 'local.conf')
PlnxToolConf = os.path.join(ConfDir, 'plnxtool.conf')
SdtAutoConf = os.path.join(ConfDir, 'sdt-auto.conf')
SdtSystemConfDtsi = os.path.join(ConfDir, 'dts', '{1:s}', 'system-conf.dtsi')
EsdkInstalledDir = os.path.join(ProotSub, 'components', 'yocto')
PlnxWorkspace = os.path.join(ProotSub, 'components', 'plnx_workspace')
GitIgnoreFile = os.path.join(ProotSub, '.gitignore')
ProjectSpec = os.path.join(ProotSub, 'project-spec')
MetaDataDir = os.path.join(ProotSub, '.petalinux')
MetaDataFile = os.path.join(MetaDataDir, 'metadata')
SDTSetupDir = os.path.join(EsdkInstalledDir, 'decoupling', 'setup')
SDTSetupFile = os.path.join(SDTSetupDir, 'dt-processor.sh')
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
ConfigLogFile = os.path.join(BuildDir, 'config.log')
PkgFileName = 'package.log'
PackageLogFile = os.path.join(BuildDir, PkgFileName)
CfgMemDir = os.path.join(BuildDir, 'package-boot')
GenMachLogFile = os.path.join(SysConfDir, 'gen-machineconf.log')
LockedSigsFile = os.path.join(EsdkInstalledDir, 'conf', 'locked-sigs.inc')
DevtoolFile = os.path.join(EsdkInstalledDir, '.devtoolbase')
OeInitEnv = os.path.join(EsdkInstalledDir, 'layers',
                         'poky', 'oe-init-build-env')
EsdkConfDir = os.path.join(EsdkInstalledDir, 'conf')
EsdkBBLayerconf = os.path.join(EsdkConfDir, 'bblayers.conf')

'''Project Out Files'''
BootBINFile = os.path.join(BuildImagesDir, 'BOOT.BIN')
BootMCSFile = os.path.join(BuildImagesDir, 'boot.mcs')
BootMBMCSFile = os.path.join(BuildImagesDir, 'system.mcs')
BootDOWNLOADBITFile = os.path.join(BuildImagesDir, 'download.bit')
BifFile = os.path.join(BuildImagesDir, 'bootgen.bif')
HsmOutFile = os.path.join(SysConfDir, 'flash_parts.txt')

'''Tool Configurations'''
PetaLinux = os.environ.get('PETALINUX', '')
PetaLinux_Ver_Str = 'PETALINUX_VER'
PetaLinux_Ver = os.environ.get(PetaLinux_Ver_Str, '')
YoctoSrcPath = os.path.join(PetaLinux, 'components', 'yocto')
EsdkSrcPath = os.path.join(YoctoSrcPath, 'source')
SDTPrestepFile = os.path.join(
    YoctoSrcPath, 'decoupling', 'decouple-prestep.sh')
XsctPath = os.path.join(PetaLinux, 'tools', 'xsct')
XsctBinPath = os.path.join(PetaLinux, 'tools', 'xsct', 'bin')
TemplateDir = os.path.join(PetaLinux, 'etc', 'template')
TemplateCommon = os.path.join(TemplateDir, '{0:s}', 'common')
TemplateDir_C = os.path.join(TemplateDir, '{0:s}', 'template-{1:s}')

'''PATH variables'''
ospath = os.environ['PATH']
os.environ['PATH'] = XsctBinPath + ":" + ospath


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
    'BOOTSCRIPT': 'boot.scr',
    'RFS_FILE': 'rootfs.cpio.gz.u-boot',
    'TINY_RFS_FILE': 'ramdisk.cpio.gz.u-boot',
    'BOOTBIN': 'BOOT.BIN'
}

FPGA_Templates = [
    'fpgamanager', 'fpgamanager_dtg',
    'fpgamanager_dtg_dfx', 'fpgamanager_dtg_csoc'
]

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
BspFilesExcludeStr = '''
RCS\nSCCS\nCVS\nCVS.adm\nRCSLOG\ncvslog.*\ntags\nTAGS\n.make.state\n.nse_depinfo
*~\n.#*\n,*\n_\$*\n*\$\n*.old\n*.bak\n*.BAK\n*.orig\n*.rej\n.del-*\n*.olb\n*.o
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
    'Prefix': 'CONFIG_SUBSYSTEM_FLASH_QSPI_BANKLESS_PART',
    'Name': '_NAME',  'Size': '_SIZE'
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

'''XSCT commands'''
OpenHWCmd = 'openhw {0}'
HdfDataMacro = '@#%HDF_DATA@#%'
GetHWFilesCmd = 'set lu_data [hsi get_hw_files -filter {{TYPE == {0}}}];\
        puts "{1}${{lu_data}}"; exit;'
XsctFileIn = 'xsct -sdx -nodisp {0}'
