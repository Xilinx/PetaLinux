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

scripts_path = os.path.dirname(os.path.realpath(__file__))
libs_path = scripts_path + '/libs'
sys.path = sys.path + [libs_path]
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')

# Global vars to add bif Id for versal/versal-net
AddedSubBootId = False
AddedLinuxId = False
# Dict variable to store command line args
# Each key variable should be unique and should not
# have start with same name
BootParams = {}
# Dict variable to store command line
# args if no/none specified
BootParamDisable = []
# Dependency key values for Boot Params
ParamDepKeys = {
    'Default': {
        'microblaze': ['FSBL'],
        'zynq': ['FSBL'],
        'zynqmp': ['FSBL'],
        'versal': [],
        'versal-net': []
    },
    'KERNEL': {
        'common': ['UBOOT', 'BOOTSCRIPT'],
    },
    'UBOOT': {
        'common': ['DTB'],
        'microblaze': ['FSBL'],
        'zynq': ['FSBL'],
        'zynqmp': ['FSBL', 'TFA', 'PMUFW'],
        'versal': ['TFA', 'PLM', 'PSMFW'],
        'versal-net': ['TFA', 'PLM', 'PSMFW']
    }
}
# Bif File sequence or order
BootFilesSeq = {
    'zynq': ['FSBL', 'FPGA', 'TFA', 'UBOOT',
             'DTB', 'BOOTSCRIPT', 'KERNEL', 'ADDFILE',
             'BIFATTR'],
    'zynqmp': ['FSBL', 'PMUFW', 'FPGA', 'TFA',
               'DTB', 'UBOOT', 'KERNEL', 'BOOTSCRIPT',
               'ADDFILE', 'BIFATTR'],
    'versal': ['FPGA', 'PLM', 'PSMFW', 'ADDCDO',
               'DTB', 'TFA', 'UBOOT', 'KERNEL',
               'BOOTSCRIPT', 'ADDFILE', 'BIFATTR'],
    'versal-net': ['FPGA', 'PLM', 'PSMFW', 'ADDCDO',
                   'DTB', 'TFA', 'UBOOT', 'KERNEL',
                   'BOOTSCRIPT', 'ADDFILE', 'BIFATTR']
}
# Default Boot attributes for Boot Params
DefaultBootAttributes = {
    'KERNEL': {'FileAttribute': {
        'common': ['partition_owner=uboot'],
        'zynqmp': ['destination_cpu=a53-0']
    }
    },
    'UBOOT': {'FileAttribute': {
        'zynqmp': ['destination_cpu=a53-0', 'exception_level=el-2'],
        'versal': ['core=a72-0', 'exception_level=el-2'],
        'versal-net': ['core=a78-0', 'cluster=0', 'exception_level=el-2']
    }
    },
    'TFA': {'FileAttribute': {
        'zynqmp': ['destination_cpu=a53-0', 'exception_level=el-3', 'trustzone'],
        'versal': ['core=a72-0', 'exception_level=el-3', 'trustzone'],
        'versal-net': ['core=a78-0', 'cluster=0', 'exception_level=el-3', 'trustzone']
    }
    },
    'FSBL': {'FileAttribute': {
        'zynq': ['bootloader'],
        'zynqmp': ['bootloader', 'destination_cpu=a53-0']
    },
    },
    'PMUFW': {'FileAttribute': 'pmufw_image'},
    'FPGA': {'AddBootId': 'True',
             'FileAttribute': {
                 'zynqmp': ['destination_device=pl'],
                 'versal': ['type=bootimage'],
                 'versal-net': ['type=bootimage']
             }
             },
    'PLM': {'AddBootId': 'True',
            'FileAttribute': 'type=bootloader'},
    'PSMFW': {'AddBootId': 'True', 'FileAttribute': 'core=psm'},
    'ADDCDO': {'AddBootId': 'True', 'FileAttribute': 'type=cdo'},
    'ADDFILE': {'FileAttribute': {
        'zynqmp': ['destination_cpu=a53-0']
    }
    },
    'DTB': {'FileAttribute': {
        'zynqmp': ['destination_cpu=a53-0'],
        'versal': ['type=raw'],
        'versal-net': ['type=raw']
    },
        'Load': {
        'zynq': ['0x100000'], 'zynqmp': ['0x100000'],
        'versal': ['0x1000'], 'versal-net': ['0x1000']
    }
    },
    'BOOTSCRIPT': {
        'FileAttribute': {
            'common': ['partition_owner=uboot'],
            'zynqmp': ['destination_cpu=a53-0']
        },
        'Offset': {
            'microblaze': ['0x1F00000'], 'zynq': ['0x9C0000'], 'zynqmp': ['0x3E80000'],
            'versal': ['0x7F80000'], 'versal-net': ['0x7F80000']
        }
    }
}


def AddFpgaBootFile(fpga_arg, proot, xilinx_arch):
    ''' Get the default bit file path and add it to BootParams dict'''
    if_fpga_manager = plnx_utils.get_config_value(
        'CONFIG_SUBSYSTEM_FPGA_MANAGER',
        plnx_vars.SysConfFile.format(proot))
    if not fpga_arg and xilinx_arch in ['microblaze', 'versal', 'versal-net']:
        fpga_arg = 'Default'
    if fpga_arg == 'Default':
        bootfile_name = plnx_utils.GetFileFromXsa(proot)
        bootfile = os.path.join(
            plnx_vars.BuildImagesDir.format(proot),
            bootfile_name)
        if not os.path.isfile(bootfile):
            bootfile = os.path.join(plnx_vars.HWDescDir.format(proot),
                                    bootfile_name)
            if not os.path.isfile(bootfile):
                logger.error('Default bitsream(%s) is not found,'
                             'please specify a bitstream file path with --fpga <BITSTREAM>'
                             % (bootfile_name))
                sys.exit(255)
        fpga_arg = bootfile
    elif fpga_arg in ['no', 'none'] or if_fpga_manager == 'y':
        fpga_arg = None

    if fpga_arg:
        fpga_arg = os.path.realpath(fpga_arg)
        plnx_utils.add_dictkey(BootParams, 'FPGA', 'Path', fpga_arg)


def AddDefaultBootAttributes(proot, xilinx_arch):
    ''' Update BootParams Dict with Default Boot Attributes
    Read the values from DefaultBootAttributes and update BootParams'''
    for BootParam in BootParams.keys():
        BootParamPre = BootParam.split('@')[0]
        if DefaultBootAttributes.get(BootParamPre):
            for DefAttrKey in DefaultBootAttributes[BootParamPre].keys():
                DefAttr = DefaultBootAttributes[BootParamPre][DefAttrKey]
                append = True
                # Dont add default Offset and Load
                # if user specified
                if DefAttrKey in ['Offset', 'Load']:
                    if BootParams[BootParam].get(DefAttrKey):
                        continue
                    if DefAttrKey == 'Load':
                        # Add BaseAddress to load Offset
                        archload = DefAttr.get(xilinx_arch)
                        if archload:
                            Loadwithbase = plnx_utils.append_baseaddr(proot,
                                                                      ''.join(archload))
                            DefAttr[xilinx_arch] = [archload]
                    append = False
                if isinstance(DefAttr, dict):
                    # If Dict read the arch specific attributes
                    DefValueKeys = []
                    DefValueKeys += DefAttr.get(xilinx_arch, '')
                    DefValueKeys += DefAttr.get('common', '')
                    for ArchAttr in DefValueKeys:
                        AttrPrefix = ''.join(ArchAttr).split('=')[0] + '='
                        if AttrPrefix and BootParams[BootParam].get(DefAttrKey):
                            # Search the Default Attribute with user specified Attribute
                            # if match dont add Default one
                            if BootParams[BootParam].get(DefAttrKey).find(AttrPrefix) != -1:
                                continue
                        plnx_utils.add_dictkey(
                            BootParams, BootParam, DefAttrKey, ''.join(ArchAttr), append)
                elif isinstance(DefAttr, list):
                    # If List read the each key
                    for Attr in DefAttr:
                        AttrPrefix = Attr.split('=')[0] + '='
                        if AttrPrefix and BootParams[BootParam].get(DefAttrKey):
                            # Search the Default Attribute with user specified Attribute
                            # if match dont add Default one
                            if BootParams[BootParam].get(DefAttrKey).find(AttrPrefix) != -1:
                               continue
                        plnx_utils.add_dictkey(
                            BootParams, BootParam, DefAttrKey, Attr, append)

                else:
                    # If not List and Dict
                    AttrPrefix = DefAttr.split('=')[0] + '='
                    if AttrPrefix and BootParams[BootParam].get(DefAttrKey):
                        # Search the Default Attribute with user specified Attribute
                        # if match dont add Default one
                        if BootParams[BootParam].get(DefAttrKey).find(AttrPrefix) != -1:
                            continue
                    plnx_utils.add_dictkey(
                        BootParams, BootParam, DefAttrKey, DefAttr, append)


def AddDefaultBootFile(args, proot):
    ''' Adding Default Boot files into BootParmas dict'''
    keyfileslist = ParamDepKeys['Default'].get(args.xilinx_arch)
    # Get Kernel and uboot dependency files
    if BootParams.get('KERNEL', ''):
        keyfileslist += ['UBOOT', 'KERNEL']
        keyfileslist += ParamDepKeys['KERNEL'].get('common', '')
        keyfileslist += ParamDepKeys['UBOOT'].get('common', '')
        keyfileslist += ParamDepKeys['UBOOT'].get(args.xilinx_arch, '')
    if BootParams.get('UBOOT', ''):
        keyfileslist += ['UBOOT']
        keyfileslist += ParamDepKeys['UBOOT'].get('common', '')
        keyfileslist += ParamDepKeys['UBOOT'].get(args.xilinx_arch, '')
    keyfileslist = list(set(keyfileslist))
    # Add Dependent files for uboot and kernel
    # specified in ParamDepKeys
    # will add default image files 
    # if (depfile key not found in Dict or key value is Default) and not no/none
    for depfile in keyfileslist:
        if depfile not in BootParamDisable and \
            (depfile not in BootParams.keys() or \
                (depfile in BootParams.keys() and \
                BootParams[depfile].get('Path') == 'Default')):
            depfilekey = depfile
            archkey = '%s_%s' % (depfile, args.xilinx_arch.upper())
            if plnx_vars.BootFileNames.get(archkey):
                depfilekey = archkey
            plnx_utils.add_dictkey(BootParams, depfile, 'Path', os.path.join(
                plnx_vars.BuildImagesDir.format(proot),
                plnx_vars.BootFileNames[depfilekey])
            )
        elif depfile in BootParams.keys() and \
                BootParams[depfile].get('Path') == 'Default':
            # Delete the key if Default and no/none
            del BootParams[depfile]

    # Read the kernel offset if flash select from flash_info.txt(generated from sysconfig)
    if not os.path.isfile(plnx_vars.HsmOutFile.format(proot)):
        plnx_utils.CreateFile(plnx_vars.HsmOutFile.format(proot))
    kernel_offset = ''
    if not args.boot_device or args.boot_device == 'flash':
        kernel_offset = plnx_utils.get_config_value('kernel',
                                                    plnx_vars.HsmOutFile.format(proot))
        kernel_offset = kernel_offset.split(' ')[0]
        if BootParams.get('KERNEL') and \
                not BootParams['KERNEL'].get('Offset'):
            plnx_utils.add_dictkey(
                BootParams, 'KERNEL', 'Offset', kernel_offset)
    # Update BootParams Dict with Default Boot Attributes
    AddDefaultBootAttributes(proot, args.xilinx_arch)


def CheckOutFile(OutFile, Force):
    ''' Check output file and give error if exists and force not specified'''
    if os.path.exists(OutFile):
        if not os.path.isfile(OutFile):
            logger.error(
                'Expecting Output as File, Please specify a valid --output File path')
            sys.exit(255)
        if Force:
            plnx_utils.RemoveFile(OutFile)
        else:
            logger.error('Output file "%s" already exists.'
                         'Please use --force to overwrite it.' % OutFile)
            sys.exit(255)


def CheckOutDir(OutDir, Force):
    ''' Check output dir and give error if exists and force not specified'''
    if os.path.exists(OutDir):
        if not os.path.isdir(OutDir):
            logger.error(
                'Expecting Output as folder, Please specify a valid --output File path')
            sys.exit(255)
        if Force:
            logger.info('Cleaning %s folder' % os.path.basename(OutDir))
            plnx_utils.RemoveDir(OutDir)
        else:
            logger.error('Output Dir "%s" already exists.'
                         ' Please use --force to overwrite it.'
                         % OutDir)
            sys.exit(255)
