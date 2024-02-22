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
import shutil
import sys
import gen_downloadbit
import plnx_utils
import plnx_vars
from package_common import BootParams

logger = logging.getLogger('PetaLinux')


def ValidateFlashSize(flash_size_arg, flash_type, flash_size):
    ''' Validate the Flash size between user given flash_size
    and auto detected flash_size '''
    if not flash_size_arg:
        if not flash_size:
            flash_size = '16'
            logger.warning('User hasnot specified flash size, and the tool failed '
                           'to detect the size of the system flash, will use the default value '
                           '"16 Mbytes".')
        else:
            flash_size = int(int(flash_size, base=16) / 1024 / 1024)
            logger.info('User hasnot specified flash size, will use the auto '
                        'detected system flash size: %s MBytes.' % (flash_size))
    else:
        flash_size = flash_size_arg
    if flash_size and not (1 == bin(int(flash_size)).count('1')):
        logger.error(
            'Flash size "%s" is invalid, it should be the power of 2.' % flash_size)
        sys.exit(255)
    return flash_size


def GetFlashInterface(flash_intf_arg, flash_type, flash_width, bitfile):
    ''' Getting Flash Interface using the bitstream file 
    if not use the default flash as SPIx1 '''
    auto_flash_intf = ''
    if flash_type == 'spi':
        auto_flash_intf = 'SPIx1'
        if bitfile:
            spi_width = ''
            if not shutil.which('xxd'):
                logger.warning(
                    'Failed to detect SPI width from bitstream since xxd is not in your path.')
                logger.warning('Using default one: %s' % auto_flash_intf)
            else:
                for i in range(24, 49):
                    # Check the first 1024 bytes from the bitstream only
                    spi_widthcmd = 'xxd -p -c %s -l 1024 %s' % (i, bitfile)
                    stdout = plnx_utils.runCmd(
                        spi_widthcmd, os.getcwd(), shell=True)
                    for line in ''.join(stdout).splitlines():
                        try:
                            line = line.decode('utf-8')
                        except AttributeError:
                            pass
                        if line.upper().startswith('FFFFFFFFFFFFFFFFAA99556620000000'):
                            n = 2
                            spi_width_ = [(line[i:i + n])
                                          for i in range(0, len(line), n)]
                            if spi_width_:
                                spi_width = '0x%s' % spi_width_[22]
                                spi_width = int(spi_width, base=16)
                                break
                    if spi_width:
                        break

                if spi_width == '':
                    logger.warning(
                        'Failed to detect SPI width from bitstream.')
                    logger.warning('Using default one: %s' % auto_flash_intf)
                elif spi_width == 0:
                    auto_flash_intf = 'SPIx1'
                elif spi_width == 1:
                    auto_flash_intf = 'SPIx2'
                elif spi_width == 2:
                    auto_flash_intf = 'SPIx4'
                else:
                    logger.warning(
                        'Unknown SPI width detected: %s.' % spi_width)
                    logger.warning('Using default one: %s' % auto_flash_intf)
    elif flash_type == 'parallel':
        if flash_width in ('8', '16'):
            auto_flash_intf = 'BPIx%s' % flash_width
        else:
            logger.warning(
                'Auto detect: Unsupported parallel system flash width: %s.' % flash_width)
    if flash_intf_arg:
        if flash_intf_arg not in ('SERIALx1', 'SPIx1', 'SPIx2',
                                  'SPIx4', 'SPIx8', 'BPIx8', 'BPIx16',
                                  'SMAPx8', 'SMAPx16', 'SMAPx32'):
            logger.error(
                'Unsupported user specified flash interface: %s' % flash_intf_arg)
            sys.exit(255)
        if auto_flash_intf and flash_intf_arg != auto_flash_intf:
            logger.warning('User specified Flash interface %s is different to the '
                           'auto detected one %s. Will use the user specified one.' % (
                               flash_intf_arg, auto_flash_intf))
        return flash_intf_arg
    elif auto_flash_intf:
        logger.info(
            'User hasnot specified flash interface, will use the auto detected one %s' % auto_flash_intf)
        return auto_flash_intf
    else:
        logger.warning('User hasnot specified flash interface, and failed to detect '
                       'it from system flash settings, will use the default one %s.' % auto_flash_intf)
        return auto_flash_intf


def CreateMBBootBin(args, proot):
    ''' Creating MCS/BIN file for Microblaze '''
    download_bit_out = os.path.join(os.path.dirname(args.output),
                                    'download.bit')
    gen_downloadbit.CreateDownloadbit(args, proot, download_bit_out)
    BootParams['FPGA']['Path'] = download_bit_out
    # Read the offsets if flash select from flash_info.txt(generated from sysconfig)
    if not os.path.isfile(plnx_vars.HsmOutFile.format(proot)):
        plnx_utils.CreateFile(plnx_vars.HsmOutFile.format(proot))
    flash_type = plnx_utils.get_config_value('flash_type',
                                             plnx_vars.HsmOutFile.format(proot)
                                             )
    flash_width = plnx_utils.get_config_value('flash_width',
                                              plnx_vars.HsmOutFile.format(
                                                  proot)
                                              )
    flash_size = plnx_utils.get_config_value('flash_size',
                                             plnx_vars.HsmOutFile.format(proot)
                                             )
    fpga_prop = plnx_utils.get_config_value('fpga',
                                            plnx_vars.HsmOutFile.format(proot)
                                            )
    uboot_prop = plnx_utils.get_config_value('boot',
                                             plnx_vars.HsmOutFile.format(proot)
                                             )
    kernel_prop = plnx_utils.get_config_value('kernel',
                                              plnx_vars.HsmOutFile.format(
                                                  proot)
                                              )
    jffs2_prop = plnx_utils.get_config_value('jffs2',
                                             plnx_vars.HsmOutFile.format(proot)
                                             )
    flash_size = ValidateFlashSize(args.flash_size, flash_type, flash_size)
    flash_intf = GetFlashInterface(args.flash_intf, flash_type,
                                   flash_width, BootParams['FPGA'].get('Path'))

    cfgmem_args = ''
    fpga_args = ''
    data_args = ''
    # Check the Offset value for given keys
    for file_ in BootParams.keys():
        if file_ in ('FSBL', 'DTB'):
            continue
        file_path = BootParams[file_].get('Path')
        if not os.path.isabs(file_path):
            file_path = os.path.join(proot, file_path)
        plnx_utils.CheckFileExists(
            file_path, 'Failed to generate %s file, ' % args.format)
        if not BootParams[file_].get('Offset'):
            bootfile_offset = ''
            bootfile_size = ''
            if file_ in ('FPGA', 'UBOOT', 'KERNEL', 'JFFS2'):
                file_prop = eval('%s_prop' % file_.lower())
                if file_prop:
                    try:
                        bootfile_offset = file_prop.split()[0]
                    except IndexError:
                        bootfile_offset = ''
                    BootParams[file_]['Offset'] = bootfile_offset
                    try:
                        bootfile_size = file_prop.split()[1]
                    except IndexError:
                        bootfile_size = ''
                file_size = os.path.getsize(file_path)
                if bootfile_size and file_size > int(bootfile_size, base=16):
                    logger.error('Size of BootFile "%s" is %s larger than the %s partition size %s.' % (
                        file_path, bootfile_size, file_.lower(), int(file_path, base=16)))
                    sys.exit(255)
        if not BootParams[file_].get('Offset'):
            logger.error('Offset of file "%s" is empty. '
                         'Please use "--offset" to specify the offset.' % (
                             BootParams[file_].get('Path')))
            sys.exit(255)

        file_offset = BootParams[file_].get('Offset')
        if flash_intf == 'BPIx16':
            # Devide offset by 2 if BPIx16
            file_offset = hex(int(int(file_offset, base=16) / 2))

        logger.info('Add File %s at %s' % (file_path, file_offset))
        if file_ == 'FPGA':
            fpga_args = '-loadbit "up %s %s"' % (file_offset, file_path)
        else:
            data_args += ' up %s %s' % (file_offset, file_path)
    if data_args:
        data_args = '-loaddata "%s"' % data_args
    cfgmem_args = '-force -format %s -size %s -interface %s' % (
        args.format, flash_size, flash_intf)
    writecfg_cmd = 'write_cfgmem %s %s %s %s' % (
        cfgmem_args, fpga_args, data_args, args.output)
    plnx_utils.RemoveDir(plnx_vars.CfgMemDir.format(proot))
    plnx_utils.CreateDir(plnx_vars.CfgMemDir.format(proot))
    write_cfgmemfile = os.path.join(plnx_vars.CfgMemDir.format(proot),
                                    'write_cfgmem_hsm.tcl')
    plnx_utils.CreateFile(write_cfgmemfile)
    plnx_utils.add_str_to_file(write_cfgmemfile, writecfg_cmd)
    cfgmemlog = os.path.join(plnx_vars.CfgMemDir.format(proot), 'cfgmem.log')
    cfgmemjou = os.path.join(plnx_vars.CfgMemDir.format(proot), 'cfgmem.jou')
    vivado_cmd = 'vivado -log %s -jou %s -mode batch -s %s' % (
        cfgmemlog, cfgmemjou, write_cfgmemfile)
    logger.info('Generating %s file...' % args.format)
    stdout, stderr = plnx_utils.runCmd(vivado_cmd,
                                       plnx_vars.CfgMemDir.format(proot), shell=True)
    return
