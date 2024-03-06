#!/usr/bin/env python3

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

PPackageWic = '''
Examples:
    Package wic image using default images:
    $ petalinux-package wic
    This will generate the wic image in images/linux folder with
    the default images from images/linux dir with name petalinux-sdimage.wic.

    Package wic image in specified folder:
    $ petalinux-package wic --outdir wicimage/
    This will generate the wic image in wicimage/ folder as petalinux-sdimage.wic.

    Package wic image with specified images path:
    $ petalinux-package wic --images-dir custom-imagespath/
    This will pack all bootfiles from custom-imagespath/ dir.

    Package wic image with custom size:
    $ petalinux-package wic --size 2G,2G
    This will generate the wic image with boot partition 2G and root partition 2G
    $ petalinux-package wic --size 4G
    This will generate the wic image with boot partition 4G and root partition 4G(default)
    $ petalinux-package wic --size ,6G
    This will generate the wic image with boot partition 2G(default) and root partition 6G

    Package custom bootfiles into /boot dir:
    $ petalinux-package wic --bootfiles "boot.bin userfile1 userfile2"
    This will generate the wic image with specified files copied into /boot dir.
    Make sure these files should be part of images dir.

    $ petalinux-package wic --extra-bootfiles "uImage:kernel"
    This copy file uImage to /boot dir with the name kernel

    $ petalinux-package wic --bootfiles "userfiles/*"
    This will copy files default bootfiles and specified bootfiles by user into /boot dir.

    $ petalinux-package wic --extra-bootfiles "userfiles/*:user_boot"
    This will copy all files in userfiles/ dir to the /boot/user_boot dir.
    Make sure userfiles directory should be in images dir.

    Package custom rootfile system:
    $ petalinux-package wic --rootfs-file custom-rootfs.tar.gz
    This will unpack your custom-rootfs.tar.gz file and copy to the /rootfs dir.

    $ petalinux-package wic --wic-extra-args="-c xz"
    This will compress the wic image with sprecified compressor.
    Supported compressors are: {gzip,bzip2,xz}

    Decompress the wic image:
    $ xz -d petalinux-sdimage.wic.xz
    $ gzip -d petalinux-sdimage.wic.gz
    $ bzip2 -d petalinux-sdimage.wic.bz2

    Copying the image SD card:
    $ dd if=petalinux-sdimage.wic of=/dev/sd<X> conv=fsync
    You need sudo access to do this.
'''

PBootJtag = '''
Examples:
    Images for loading on target can be selected from:
    1. prebuilt directory:<PROJECT>/pre-built/linux/images
    2. images directory:<PROJECT>/images/linux

    Some possible Use-Cases:
    UC1 : Download bitstream and additonally FSBL for Zynq, FSBL and PMUFW for ZynqMP boards:
      $ petalinux-boot jtag --prebuilt 1  # images are taken from <PROJECT>/pre-built/linux/images directory

    UC2 : Boot u-boot on target board:
      $ petalinux-boot jtag --prebuilt 2 # images are taken from <PROJECT>/pre-built/linux/images directory
      $ petalinux-boot jtag --u-boot --fpga # images are taken from <PROJECT>/images/linux directory

      For microblaze,the above command will download the bitstream to target board, and
      then boot the u-boot on target board.
      For Zynq, it will download the bitstream and FSBL to target board,
      and then boot the u-boot on target board.
      For Zynq UltraScale+, it will download the bitstream, PMUFW and FSBL,
      and then boot the u-boot on target board.

    UC3 : Boot prebuilt kernel on target board:
      $ petalinux-boot jtag --prebuilt 3 # images are taken from <PROJECT>/pre-built/linux/images directory
      $ petalinux-boot jtag --kernel --fpga # images are taken from <PROJECT>/images/linux directory

      For microblaze, it will download the bitstream to target board, and
      then boot the kernel image on target board.
      For Zynq, it will download the bitstream and FSBL to target board,
      and then boot the u-boot and then the kernel on target
      board.
      For Zynq UltraScale+, it will download the bitstream, PMUFW and FSBL,
      and then boot the kernel with help of linux-boot.elf to set kernel
      start and dtb addresses.

    UC4 : Generate xsdb tcl using petalinux-boot command:
      $ petalinux-boot jtag --kernel --fpga --tcl mytcl # images are taken from <PROJECT>/images/linux directory

      This is similar to UC3, but instead of loading images on target a tcl(mytcl) is generated.
      This script can be modified further by users and used directly with xsdb to load images. Ex: xsdb mytcl

    UC5 : Generate debug messages while loading images:
      $ petalinux-boot jtag --kernel --fpga -v # images are taken from <PROJECT>/images/linux directory

      This is similar to UC3 but with more debug information while invoking xsdb

    UC6: To download a image with a bitstream with --fpga --bitstream <BITSTREAM> option:
      $ petalinux-boot jtag --u-boot --fpga --bitstream <BITSTREAM> # images are taken from <PROJECT>/images/linux directory
      $ petalinux-boot jtag --kernel --fpga --bitstream <BITSTREAM> # images are taken from <PROJECT>/images/linux directory
      $ petalinux-boot jtag --prebuilt <BOOT_LEVEL> --fpga --bitstream <BITSTREAM> # specify bitstream path
      $ petalinux-boot jtag --prebuilt <BOOT_LEVEL> --fpga --bitstream no # skip loading bitstream

    Boot customised u-boot image with jtag:
      $ petalinux-boot jtag --u-boot/--uboot <specify custom u-boot.elf path>

    Boot customised kernel image with jtag:
      For zynqMP , versal and versal-net use Image
      $ petalinux-boot jtag --kernel <specify custom Image path>

    Boot customised kernel image with jtag:
      For zynq use uImage
      $ petalinux-boot jtag --kernel <specify custom uImage path>

      For microblaze use linux.bin.ub
      $ petalinux-boot jtag --kernel <specify custom linux.bin.ub path>

    Boot customised dtb image with kernel:
      $ petalinux-boot jtag --kernel <specify custom kernel path> --dtb <specify custom dtb path>

    Boot customised dtb image with uboot:
      $ petalinux-boot jtag --u-boot/--uboot  <specify custom u-boot path> --dtb <specify custom dtb path>
      It will support for microblaze,zynq and zynqMP.

    Boot customised rootfs image with kernel:
      $ petalinux-boot jtag --kernel --rootfs <specify custom cpio rootfs path>
'''

PBootQemu = '''
Examples:
    Boot prebuilt u-boot with QEMU:
      $ petalinux-boot qemu --prebuilt 2

    Boot prebuilt kernel with QEMU:
      $ petalinux-boot qemu --prebuilt 3

    Download newly built u-boot with QEMU:
      $ petalinux-boot qemu --u-boot
      It will boot <PROJECT>/images/linux/u-boot.elf with QEMU.

    Download newly built kernel to target board:
      $ petalinux-boot qemu --kernel
      For MicroBlaze, it will boot <PROJECT>/images/linux/image.elf with QEMU.
      For Zynq, it will boot <PROJECT>/images/linux/zImage with QEMU.
      For Zynq UltraScale+ ,versal and versal-net it will boot <PROJECT>/images/linux/Image with QEMU.

    Boot customised u-boot image with QEMU:
      $ petalinux-boot qemu --u-boot/--uboot <specify custom u-boot.elf path>
      It will support for microblaze,zynq and zynqMP.

    Boot customised kernel image with QEMU:
      For zynqMP,versal and versal-net use Image
      $ petalinux-boot qemu --kernel <specify custom Image path>

    Boot customised kernel image with QEMU:
      For zynq use zImage
      $ petalinux-boot qemu --kernel <specify custom zimage path>

      For microblaze use Image.elf
      $ petalinux-boot qemu --kernel <specify custom Image.elf  path>

    Boot customised dtb image with kernel:
      $ petalinux-boot qemu --kernel <specify custom kernel path> --dtb <specify custom dtb path>
      It will support for microblaze,zynq and zynqMP.

    Boot customised dtb image with uboot:
      $ petalinux-boot qemu --u-boot/--uboot  <specify custom u-boot path> --dtb <specify custom dtb path>
      It will support for microblaze,zynq and zynqMP.

    Boot customised rootfs image with kernel:
      $ petalinux-boot qemu --kernel --rootfs <specify custom cpio rootfs path>

    Specify qemu-no-gdb option to disable gdb via qemu boot
      $ petalinux-boot qemu --prebuilt 2/--prebuilt 3 --qemu-no-gdb
      $ petalinux-boot qemu --u-boot/--kernel --qemu-no-gdb
'''
