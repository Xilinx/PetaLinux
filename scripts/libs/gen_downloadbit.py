#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import logging
import os
import re
import sys
import package_common
import plnx_utils
import plnx_vars
from package_common import BootParams

logger = logging.getLogger('PetaLinux')


def CreateDownloadbit(args, proot, download_bit_out):
    ''' Creating DOWNLOAD.BIT file '''
    if not BootParams.get('FSBL'):
        logger.warning('You have specified no for First Stage Bootloader, '
                       'we will not add bootloader to block RAM')
        return 0
    FsblFile = BootParams['FSBL'].get('Path')
    if not os.path.isfile(FsblFile):
        logger.error('Specified or Default First Stage Bootloader '
                     'not found. Use "--fsbl" option to specify one.')
        sys.exit(255)
    if not BootParams.get('FPGA'):
        logger.error('Failed to generate download.bit file '
                     'because no bitstream file is specified')
        sys.exit(255)
    SystemBitFile = BootParams['FPGA']['Path']
    download_bit_prefix = 'DOWNLOAD_BIT_image_CONTENT'
    package_common.CheckOutFile(download_bit_out, args.force)
    plnx_utils.check_tool('updatemem',
                          'Please source Xilinx Tools settings first.')
    if args.mmi:
        mmi_filename = args.mmi
    else:
        mmi_filename = plnx_utils.GetFileFromXsa(proot, bootfile_ext='mmi')
    if not mmi_filename:
        logger.error('Unable to find file with mmi TYPE in HW file')
        sys.exit(255)
    mmi_filepath = os.path.join(plnx_vars.HWDescDir.format(proot),
                                mmi_filename)
    if not os.path.isfile(mmi_filepath):
        logger.warning('Default MMI file not found')
        logger.warning('Auto Detecting MMI file from %s' %
                       os.path.dirname(SystemBitFile))
        import glob
        mmi_filepath = glob.glob(os.path.join(os.path.dirname(SystemBitFile),
                                              '*.mmi'))[0]
        if not os.path.isfile(mmi_filepath):
            logger.error(
                'Failed to detect MMI file, please use --mmi to specify one')
            sys.exit(255)
    logger.info('Creating download.bit')
    logger.info('Fpga bitstream: %s' % SystemBitFile)
    logger.info('Fpga bitstream %s file: %s' % ('MMI', mmi_filepath))
    logger.info('Fsbl file: %s' % FsblFile)
    logger.info('Output download.bit: %s' % download_bit_out)
    if args.updatemem_extra_args:
        logger.info('Updatemem Extra Args: %s' % (args.updatemem_extra_args))
    proc_ipname = plnx_utils.get_config_value(
        plnx_vars.ProcConfs['Prefix'] +
        '_', plnx_vars.SysConfFile.format(proot),
        'choice', plnx_vars.ProcConfs['Select'])
    proc_ipindex = plnx_utils.get_config_value(
        plnx_vars.ProcConfs['Prefix'], plnx_vars.SysConfFile.format(proot),
        'choice', '%s="%s"' % (plnx_vars.ProcConfs['IpName'],
                               proc_ipname)
    )
    proc_inst_name = plnx_utils.get_config_value(
        '%s%s%s' % (plnx_vars.ProcConfs['Prefix'], proc_ipindex,
                    plnx_vars.ProcConfs['InstanceName']),
        plnx_vars.SysConfFile.format(proot)
    )
    updatemem_cmd = 'updatemem -meminfo %s -bit %s -data %s \
		            -proc %s %s -out %s' % (mmi_filepath, SystemBitFile,
                                      FsblFile, proc_inst_name, args.updatemem_extra_args,
                                      download_bit_out)
    stdout, stderr = plnx_utils.runCmd(updatemem_cmd,
                                       plnx_vars.BuildDir.format(proot), shell=True)
    if re.search('Usage:', stdout) or re.search('ERROR:', stdout):
        logger.error(stdout)
        logger.error(stderr)
        logger.error('Unable to perform updatemem')
        logger.error(
            'Failed to create download bit file for MicroBlaze %s file.' % args.format)
        sys.exit(255)

    return
