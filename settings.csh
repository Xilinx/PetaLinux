#
# C-shell setup script for PetaLinux development environment.
# Run using 'source ./settings.csh'
#
# Copyright (c) 2013-2022 Xilinx, Inc.  All rights reserved.
# Copyright (c) 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
#
set SETTINGS_FILE=./settings.csh
set XIL_SCRIPT_LOC="./"
if ( $# != 0 ) then
	# The first argument is the location of Xilinx Installation.
	# Don't detect the installation location.
	set XIL_SCRIPT_LOC="$1"
else
	#  XIL_SCRIPT_LOC should point to script location
	set XIL_SCRIPT_LOC_TMP_UNI=`echo $_ | cut -d" " -f 2`
	set XIL_SCRIPT_LOC_TMP_UNI_TAIL=${XIL_SCRIPT_LOC_TMP_UNI:t}
	set XIL_SCRIPT_LOC_TMP_UNI=${XIL_SCRIPT_LOC_TMP_UNI:h}
	if ( "$XIL_SCRIPT_LOC_TMP_UNI" != "" ) then
		if ( "$XIL_SCRIPT_LOC_TMP_UNI" == "$XIL_SCRIPT_LOC_TMP_UNI_TAIL" ) then
			 set XIL_SCRIPT_LOC_TMP_UNI="./"
		endif
		set XIL_SCRIPT_LOC_TMP_UNI=`readlink -f ${XIL_SCRIPT_LOC_TMP_UNI}`
		if ( $? == 0 ) then
			set XIL_SCRIPT_LOC=${XIL_SCRIPT_LOC_TMP_UNI}
		endif
	endif
	unset XIL_SCRIPT_LOC_TMP_UNI_TAIL
	unset XIL_SCRIPT_LOC_TMP_UNI
endif

setenv PETALINUX `readlink -f "${XIL_SCRIPT_LOC}"`

setenv PETALINUX_VER 2024.1
setenv PETALINUX_MAJOR_VER `echo $PETALINUX_VER | cut -d"." -f 1`

setenv XSCT_TOOLCHAIN "${PETALINUX}/components/xsct"

#
# Add toolchains to user's search path
#
setenv PATH "${XSCT_TOOLCHAIN}/gnu/aarch32/lin/aarch64-none-elf/bin:${PATH}"
setenv PATH "${XSCT_TOOLCHAIN}/gnu/aarch32/lin/gcc-arm-linux-gnueabi/bin:${PATH}"
setenv PATH "${XSCT_TOOLCHAIN}/gnu/aarch64/lin/aarch64-none/bin:${PATH}"
setenv PATH "${XSCT_TOOLCHAIN}/gnu/aarch64/lin/aarch64-linux/bin:${PATH}"
setenv PATH "${XSCT_TOOLCHAIN}/gnu/armr5/lin/gcc-arm-none-eabi/bin:${PATH}"
setenv PATH "${XSCT_TOOLCHAIN}/gnu/microblaze/lin/bin:${PATH}"

#
# Add required binary tools to the user's search path
#
setenv PATH "${PETALINUX}/scripts:${PATH}"

#
# Check for "." or ".\" in the path - it's broken
#
echo ${PATH} | tr ":" "\n" | grep '^\./*$' > /dev/null && echo "WARNING: '.' detected in PATH - fixing it." 
setenv PATH `echo ${PATH} | tr ":" "\n" | grep -v '^\./*$' | tr "\n" ":"`
# Strip any trailing or multi-colons - they are interpreted as '.'
setenv PATH `echo ${PATH} | sed -e 's/:*$//g' -e 's/::*/:/g'`

set plnxbanner=" The PetaLinux source code and images provided/generated are for demonstration purposes only."
set length=`expr "$plnxbanner" : '.*'`
printf '%*s\n' $length | tr ' ' '*'
printf "${plnxbanner}\n"
printf '%*s\n' $length | tr ' ' '*'

echo PetaLinux environment set to \'${PETALINUX}\'

foreach s (/bin/sh sh)
	$s --version |& grep -q "^GNU bash"
	if ( $status != 0 ) then
		echo "WARNING: ${s} is not bash! "
		echo "bash is PetaLinux recommended shell. Please set your default shell to bash."
		break
	endif
end

if ( $SHELL != "/bin/bash" ) then
	echo "WARNING: $SHELL is not bash! "
	echo "/bin/bash is Petalinux recommended SHELL variable. Please set your SHELL variable to /bin/bash."
endif

# Add buildtools path
set NATIVE_SYSROOT_PATH="${PETALINUX}/sysroots/x86_64-petalinux-linux"
if ( -d ${NATIVE_SYSROOT_PATH} ) then
	setenv PATH "${NATIVE_SYSROOT_PATH}/usr/bin:${NATIVE_SYSROOT_PATH}/usr/sbin:${NATIVE_SYSROOT_PATH}/sbin:$PATH"
endif

# Has this installation been completed?
${PETALINUX}/scripts/bash/petalinux-env-check
#
# Not to generate the pycache files in tool
setenv PYTHONDONTWRITEBYTECODE 1
