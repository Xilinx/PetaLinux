#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import sys
import plnx_utils
import plnx_vars
import boot_common


logger = logging.getLogger('PetaLinux')


def QemuBootSetup(args, proot):
    print(args, proot)


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

    qemu_parser.set_defaults(func=QemuBootSetup)

    return
