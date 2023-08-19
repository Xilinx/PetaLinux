#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import sys

scripts_path = os.path.dirname(os.path.realpath(__file__))
libs_path = scripts_path + '/libs'
sys.path = sys.path + [libs_path]
import bitbake_utils
import package_common
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')

PrebuiltDirDefList = 'images implementation'


def PackagePrebuilt(args, proot):
    ''' Copy image/linux to prebuilts folder'''
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)
    global PrebuiltDirDefList
    package_common.CheckOutDir(plnx_vars.PreBuildsDir.format(proot),
                               args.force)
    logger.info('Updating software prebuilt')
    for Dir in PrebuiltDirDefList.split():
        plnx_utils.CreateDir(
            os.path.join(plnx_vars.PreBuildsDir.format(proot),
                         Dir)
        )
    logger.info('Installing software images')
    rsync_cmd = 'rsync -avu "%s"/* "%s"' % (
        plnx_vars.BuildImagesDir.format(proot),
        plnx_vars.PreBuildsImagesDir.format(proot),
    )
    if os.path.exists(plnx_vars.BuildImagesDir.format(proot)) and \
            os.listdir(plnx_vars.BuildImagesDir.format(proot)):
        plnx_utils.runCmd(rsync_cmd, os.getcwd(), shell=True)
    else:
        logger.error(
            'Fail to update the pre-built, No images/linux folder found.')
        sys.exit(255)

    # Update prebuilts with user added files
    for fromadd in args.add:
        src_ = fromadd.split(':')
        src = os.path.realpath(src_[0])
        dest = src_[0]
        if len(src_) >= 2 and src_[1]:
            dest = src_[1]
        dest = os.path.join(plnx_vars.PreBuildsDir.format(proot),
                            dest)
        if os.path.exists(src):
            user_dir = os.path.dirname(dest)
            plnx_utils.CreateDir(user_dir)
            if os.path.isfile(src):
                plnx_utils.CopyFile(src, dest)
            elif os.path.isdir(src):
                plnx_utils.CopyDir(src, dest)
        else:
            logger.warning('Failed to copy %s, File not found.' % src)

    # Update prebuilts with fpga bitstream paths
    FpgaDir = os.path.join(plnx_vars.PreBuildsDir.format(proot),
                           'implementation')
    for fpgafile in args.fpga:
        if os.path.isfile(fpgafile):
            plnx_utils.CopyFile(fpgafile, FpgaDir)
    logger.info('Pre-built directory is updated.')


def pkgprebuilt_args(prebuilt_parser):
    prebuilt_parser.add_argument('-p', '--project', metavar='PROJECT_DIR', type=os.path.realpath,
                                 help='Specify full path to a PetaLinux project.'
                                 '\nDefault is the working project.')
    prebuilt_parser.add_argument('--fpga', action='append', type=os.path.realpath,
                                 help='FPGA bitstream Path', default=[])
    prebuilt_parser.add_argument('-a', '--add', metavar='src:dest', action='append',
                                 default=[],
                                 help='Add file/folder to prebuilt directory "src" with "dest"'
                                 )

    prebuilt_parser.set_defaults(func=PackagePrebuilt)

    return
