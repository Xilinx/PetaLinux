#!/usr/bin/env python

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

PCreateProject = '''
Examples:
    Create project from PetaLinux Project BSP:
    $ petalinux-create project -s <PATH_TO_PETALINUX_PROJECT_BSP>

    Create project from PetaLinux Project BSP and specify the TMPDIR PATH:
    $ petalinux-create project -s <PATH_TO_PETALINUX_PROJECT_BSP> --tmpdir <TMPDIR PATH>

    Create project from template and specify the TMPDIR PATH:
    $ petalinux-create project -n <PROJECT> --template <TEMPLATE> --tmpdir <TMPDIR PATH>

    Create project from template:
    For microblaze project,
    $ petalinux-create project -n <PROJECT> --template microblaze

    For zynq project,
    $ petalinux-create project -n <PROJECT> --template zynq

    For zynqMP project,
    $ petalinux-create project -n <PROJECT> --template zynqMP

    For versal project,
    $ petalinux-create project -n <PROJECT> --template versal

    For versal-net project,
    $ petalinux-create project -n <PROJECT> --template versal-net
'''

PcreateApps = '''
Examples:
    Create an app and enable it:
    $ petalinux-create apps -n myapp --enable
        The application "myapp" will be created with c template in:
        <PROJECT>/project-spec/meta-user/recipes-apps/myapp

    Create an app with remote sources(Ex:https://example.git):
    $ petalinux-create apps -n myapp --enable --srcuri "git://example.git;protocol=https"
    $ petalinux-create apps -n myapp --enable --srcuri "https://example.tar.gz"

    Create an app with local source files:
    $ petalinux-create apps --template dfx_user_dts -n gpio --enable --srcuri "<path>/pl.dtsi <path>/system.bit <path>/shell.json"
    This will create "gpio" application with pl.dtsi,system.bit and shell.json added to SRC_URI and copied to files directory.

    $ petalinux-create apps --template dfx_user_dts -n gpio --enable --srcuri "<path>/pl.dtsi <path>/system.pdi <path>/accel.json"
    This will create "gpio" application with pl.dtsi,system.pdi and accel.json added to SRC_URI and copied to files directory.

    Create an app with with multiple dtsi files:
    $ petalinux-create apps --template dfx_user_dts -n gpio --enable --srcuri "<path>/user.dts <path>/user1.dtsi <path>/user2.dtsi <path>/system.bit <path>/shell.json"
    It will create "gpio" application with user.dts, user1.dtsi, user2.dtsi, system.bit and shell.json added
    to SRC_URI and copied to files directory.

    Create an app to extract the bit from flat xsa, generates the dtsi using dtg for specified xsa and install .dtbo and .bit.bin
    into rootfs(/lib/firmware/xilinx)
    For Zynq:
    $ petalinux-create apps --template dfx_dtg_zynq_full -n gpio --enable --srcuri "<path>/gpio.xsa"

    For ZynqMP:
    $ petalinux-create apps --template dfx_dtg_zynqmp_full -n gpio --enable --srcuri "<path>/gpio.xsa <path>/shell.json"

    For Versal:
    $ petalinux-create apps --template dfx_dtg_versal_full -n gpio --enable --srcuri "<path>/flat.xsa <path>/shell.json"

    Create an app for zynqmp to extract the bit from dfx_static xsa, generates the dtsi using dtg for specified xsa and install .dtbo and .bit.bin
    into rootfs(/lib/firmware/xilinx)
    $ petalinux-create apps --template dfx_dtg_zynqmp_static -n static-app --enable --srcuri "<path>/static.xsa <path>/shell.json"
    
    Create a RP/RM application for zynqmp to extract bit from dfx_partial xsa, generates the partial dtsi using dtg with that xsa and 
    install .dtbo and .bit.bin into rootfs(/lib/firmware/xilinx)
    $ petalinux-create apps --template dfx_dtg_zynqmp_partial -n rprm-app --enable --srcuri "<path>/rprm.xsa <path>/accel.json" --static-pn "static-app"

    Create an app for versal to extract the pdi from dfx_static xsa, generates the dtsi using dtg with that xsa and install .dtbo and .pdi
    into rootfs(/lib/firmware/xilinx)
    $ petalinux-create apps --template dfx_dtg_versal_static -n static-app --enable --srcuri "<path>/static.xsa <path>/shell.json"

    Create a RP/RM application for versal to extract pdi from dfx_partial xsa, generates the partial dtsi using dtg with that xsa and 
    install .dtbo and .pdi into rootfs(/lib/firmware/xilinx)
    $ petalinux-create apps --template dfx_dtg_versal_partial -n rprm-app --enable --srcuri "<path>/rprm.xsa <path>/accel.json" --static-pn "static-app"
'''

PCreateModules = '''
Examples:
    Create an module and enable it:
    $ petalinux-create modules -n mymodule --enable
    The module "mymodule" will be created with template in: <PROJECT>/project-spec/meta-user/recipes-modules/mymodule

    Create an module with source files:
    $ petalinux-create modules -n mymodule --enable --srcuri "<path>/mymoudle.c <path>/Makefile"
'''
