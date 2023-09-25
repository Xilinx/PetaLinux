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
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')


def PackageSysroot(args, proot):
    ''' Extract the sdk.sh to images/linux Directory'''
    args.arch = plnx_utils.get_system_arch(proot)
    args.xilinx_arch = plnx_utils.get_xilinx_arch(proot)
    # Add default files if not user given
    if not args.sdk:
        args.sdk = plnx_vars.SdkOutFile.format(proot)
    if not args.dir:
        args.dir = plnx_vars.SdkInstallDir.format(proot)

    # Add proot if its not absolute path
    if not os.path.isfile(args.sdk):
        logger.error('SDK file not found: %s' % args.sdk)
        sys.exit(255)
    if args.sdk and not os.path.isabs(args.sdk):
        args.sdk = os.path.join(proot, args.sdk)

    if args.dir and not os.path.isabs(args.dir):
        args.dir = os.path.join(proot, args.dir)
    sdk_command = 'unset LD_LIBRARY_PATH;'
    sdk_command += '%s -p -y -d "%s"' % (args.sdk, args.dir)
    plnx_utils.runCmd(sdk_command, proot, shell=True, checkcall=True)


def pkgsysroot_args(sysroot_parser):
    sysroot_parser.add_argument('-p', '--project', metavar='PROJECT_DIR', type=os.path.realpath,
                                help='Specify full path to a PetaLinux project.'
                                '\nDefault is the working project.')
    sysroot_parser.add_argument('-s', '--sdk', metavar='<SDK installer path>',
                                nargs='?', const=plnx_vars.SdkFile,
                                type=os.path.realpath, help='SDK installer path'),
    sysroot_parser.add_argument('-d', '--dir', metavar='<directory path>',
                                nargs='?', const=plnx_vars.SdkDir,
                                type=os.path.realpath, help='Directory path'
                                )

    sysroot_parser.set_defaults(func=PackageSysroot)

    return
