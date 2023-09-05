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

PConfig = '''
Examples:
    Sync hardware description from Vivado export to PetaLinux BSP project:
    $ petalinux-config --get-hw-description <Vivado_Export_to_SDK_Directory>
    It will sync up the XSA file from <Vivado_Export_to_SDK_Directory> to project-spec/hw-description/ directory.

    If more than one XSA files in <Vivado_Export_to_SDK_Directory> specify the exact file path using
    $ petalinux-config --get-hw-description <Vivado_Export_to_SDK_Directory>/system.xsa

    Configure PetaLinux project:
    $ petalinux-config

    Configure kernel:
    $ petalinux-config -c kernel

    Configure rootfs:
    $ petalinux-config -c rootfs
'''

PBuild = '''
Examples:
    Build the project:
    $ petalinux-build
    The bootable images are in <PROJECT>/images/linux/.

    Build SDK:
    $ petalinux-build -s | --sdk
    The equivalent bitbake task is do_populate_sdk, Built sdk is deployed at <PROJECT>/images/linux/sdk.sh

    Build Minimal eSDK:
    $ petalinux-build -e | --esdk
    The equivalent bitbake task is do_populate_sdk_ext, Built esdk is deployed at <PROJECT>/images/linux/esdk.sh
    This can be imported to petalinux tool with user source changes

    Build project with archiver:
    $ petalinux-build -a | --archiver

    Build SDK with archiver:
    $ petalinux-build --sdk --archiver

    Build kernel only:
    $ petalinux-build -c kernel

    Compile kernel forcefully:
    $ petalinux-build -c kernel -x compile -f

    Deploy kernel forcefully:
    $ petalinux-build -c kernel -x deploy -f

    Build rootfs only:
    $ petalinux-build -c rootfs

    Build myapp of rootfs only:
    $ petalinux-build -c myapp

    List all rootfs sub-components:
    $ petalinux-build -c rootfs -h

    Clean up u-boot and build again:
    $ petalinux-build -c u-boot -x distclean
    Above command will remove tmp files and sstate cache of u-boot.

    $ petalinux-build -x distclean
    Above command will remove tmp files and sstate cache files.

    Clean up the project build and the generated bootable images:
    $ petalinux-build -x mrproper
    Above command will remove tmp files, <PROJECT>/images/,  <PROJECT>/build/
		and <PROJECT>/components/plnx_workspace directories
'''

PPackageBoot = '''
Examples:
    Package BOOT.BIN:
    $ petalinux-package boot --u-boot
    It will add all the dependencies into BOOT.BIN to boot u-boot.
    
    Package boot.mcs file for MicroBlaze,Zynq,ZynqMP,versal and versal-net:
    $ petalinux-package boot --uboot --kernel --offset 0xF40000 --format MCS
    It will add all the dependencies into boot.mcs to boot upto kernel.

    $ petalinux-package boot --plm <PLM_ELF> --psmfw <PSMFW_ELF> --u-boot --dtb
    It will generate BOOT.BIN,BOOT_bh.bin and qemu_boot.img in specified directory.
    The default dtb load address will be 0x1000. To change the dtb load address Use below command

    $ petalinux-package boot --plm <PLM_ELF> --psmfw <PSMFW_ELF> --u-boot --dtb --load <load_address>
    It will generate a BOOT.BIN with specifed load address for dtb.

    $ petalinux-package boot --plm no --psmfw no.
    It will skip the plm and psmfw to pack into BOOT.BIN.

    $ petalinux-package boot --bif <BIF_FILE>
    It will generate a BOOT.BIN with specifed bif file, It will overrides all other settings.

    $ petalinux-package boot --fsbl <FSBL_ELF> --fpga <BITSTREAM> --u-boot --pmufw <PMUFW_ELF>
    It will generate a BOOT.BIN in your working directory with:
        * specified <BITSTREAM>
        * specified <FSBL_ELF>
        * specified < PMUFW_ELF > *
        * newly built u-boot image which is <PROJECT>/images/linux/u-boot.elf

    Generate bitstream merged with fsbl
    $ petalinux-package boot --fsbl <FSBL_ELF> --fpga <BITSTREAM> --format DOWNLOAD.BIT
    It will generate a download.bit in <PROJECT>/images/linux, with specified <BITSTREAM> and <FSBL_ELF>.
'''

PPackageBsp = '''
Examples:
    Package BSP with a PetaLinux project:
    $ petalinux-package bsp -p <PATH_TO_PROJECT> --output MY.BSP
    It will generate MY.BSP including:
        * <PROJECT>/.petalinux
        * <PROJECT>/.gitignore
        * <PROJECT>/README
        * <PROJECT>/README.hw
        * <PROJECT>/pre-built
        * <PROJECT>/project-spec
        * <PROJECT>/components
    from the specified project.

    Package BSP with hardware source:
    $ petalinux-package bsp -p <PATH_TO_PROJECT> --hwsource <PATH_TO_HARDWARE_PROJECT> --output MY.BSP
    It will not modify the specified PetaLinux project <PATH_TO_PROJECT>. It will
    put the specified hardware project source to <PROJECT>/hardware/ inside MY.BSP archive.

    Package BSP excluding some files:
    $ petalinux-package bsp -p <PATH_TO_PROJECT> --exclude-from-file <EXCLUDE_FILE> --output MY.BSP.
    It excludes the files specified in EXCLUDE_FILE from MY.BSP

    Package BSP excluding workspace directory:
    $ petalinux-package bsp -p <PATH_TO_PROJECT> --exclude-workspace --output MY.BSP.
    It excludes the Changes done in workspace and pack the BSP.
'''

PPackagePrebuilts = '''
Examples:
    Package prebuilt images:
    $ petalinux-package prebuilt
    It will create a pre-built/ directory in <PROJECT>/, and copy all the files
    from <PROJECT>/images to <PROJECT>/pre-built/linux/images/ directory:

    Package prebuilt images and specified bitstream:
    $ petalinux-package prebuilt --fpga <BITSTREAM>
    Besides copying the images, it will copy the bitstream to <PROJECT>/pre-built/linux/implentation/

    Package prebuilt images and add myfile to prebuilt:
    $ petalinux-package prebuilt --add myfile:images/myfile
    Besides copying the images, it will copy myfile to <PROJECT>/pre-built/linux/images/myfile
'''

PPackageSysroot = '''
Examples:
    Install defaults
    $ petalinux-package sysroot
    It will install <PROJECT>/images/linux/sdk.sh to <PROJECT>/images/linux/sdk

    Install Custom SDK to specified directory
    $ petalinux-package sysroot --sdk|-s <SDK installer path> --dir|-d <directory path>
'''
