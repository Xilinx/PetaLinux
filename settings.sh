#
# Setup script for PetaLinux development environment.
#
# Copyright (c) 1995-2022 Xilinx, Inc.  All rights reserved.
# Copyright (c) 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
#

SETTINGS_FILE='settings.sh'
# The right location will be replaced by the installer
XIL_SCRIPT_LOC="./"

if [ $# != 0 ]; then
	# The first argument is the location of PetaLinux Installation
	# Don't detect the installation location
	XIL_SCRIPT_LOC="$1"
else
	#  XIL_SCRIPT_LOC should point to script location
	if [ "$0" == "ksh" ]; then
		XIL_SCRIPT_LOC_TMP_UNI=`readlink -f ${XIL_ARG_}`
	else
		XIL_SCRIPT_LOC_TMP_UNI=$BASH_SOURCE
	fi
	XIL_SCRIPT_LOC_TMP_UNI=${XIL_SCRIPT_LOC_TMP_UNI%/*}
	if [ "$XIL_SCRIPT_LOC_TMP_UNI" != "" ]; then
		if [ "$XIL_SCRIPT_LOC_TMP_UNI" == "settings.sh" ]; then
			XIL_SCRIPT_LOC_TMP_UNI="./"
		fi
		XIL_SCRIPT_LOC_TMP_UNI=`readlink -f ${XIL_SCRIPT_LOC_TMP_UNI}`
		if [ $? == 0 ]; then
			XIL_SCRIPT_LOC=${XIL_SCRIPT_LOC_TMP_UNI}
		fi
	fi
	unset XIL_SCRIPT_LOC_TMP_UNI
fi

export PETALINUX=`readlink -f "${XIL_SCRIPT_LOC}"`

if echo "${PETALINUX}" | grep -q ' '; then
	echo "********************************************************"
	echo "WARNING: PetaLinux SDK installation path contains spaces"
	echo "WARNING: You are STRONGLY recommend to fix this".
	echo "********************************************************"
fi
export PETALINUX_VER=2024.2
export PETALINUX_MAJOR_VER=${PETALINUX_VER%%.*}

export XSCT_TOOLCHAIN="${PETALINUX}/components/xsct"

# Figure out host system architecture
# for now, only linux-i386 supported

#
# Add toolchains to user's search path
#
PATH="${XSCT_TOOLCHAIN}/gnu/aarch32/lin/gcc-arm-none-eabi/bin:${PATH}"
PATH="${XSCT_TOOLCHAIN}/gnu/aarch32/lin/gcc-arm-linux-gnueabi/bin:${PATH}"
PATH="${XSCT_TOOLCHAIN}/gnu/aarch64/lin/aarch64-none/bin:${PATH}"
PATH="${XSCT_TOOLCHAIN}/gnu/aarch64/lin/aarch64-linux/bin:${PATH}"
PATH="${XSCT_TOOLCHAIN}/gnu/armr5/lin/gcc-arm-none-eabi/bin:${PATH}"
PATH="${XSCT_TOOLCHAIN}/gnu/microblaze/lin/bin:${PATH}"

#
# Add required binary tools to the user's search path
#
PATH="${PETALINUX}/scripts:${PATH}"

#
# Check for "." or ".\" in the path - it's broken
#
echo "${PATH}" | tr ":" "\n" | grep '^\./*$' > /dev/null && 
	echo "WARNING: '.' detected in PATH - fixing it." 1>&2
PATH=`echo ${PATH} | tr ":" "\n" | grep -v '^\./*$' | tr "\n" ":"`

# Strip any trailing or multi-colons - they are interpreted as '.'
PATH=$(echo ${PATH} | sed -e 's/:*$//g' -e 's/::*/:/g')

plnxbanner="The PetaLinux source code and images provided/generated are for demonstration purposes only."
plnxbanner_url="Please refer to https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/2741928025/Moving+from+PetaLinux+to+Production+Deployment
 for more details"
printf "%${#plnxbanner_url}s\n" | tr " " "*"
printf "${plnxbanner}\n"
printf "${plnxbanner_url}\n"
printf "%${#plnxbanner_url}s\n" | tr " " "*"

echo PetaLinux environment set to \'${PETALINUX}\'

for s in /bin/sh sh; do
	if ! $s --version 2>/dev/null | grep -q "^GNU bash"; then
		echo "WARNING: $s is not bash! "
		echo "bash is PetaLinux recommended shell. Please set your default shell to bash."
		break
	fi
done

if ! echo $SHELL | grep -q "bash"; then
	echo "WARNING: $SHELL is not bash! "
	echo "/bin/bash is Petalinux recommended SHELL variable. Please set your SHELL variable to /bin/bash."
fi


export PATH

source "${PETALINUX}"/.environment-setup-x86_64-petalinux-linux
"${PETALINUX}"/scripts/bash/petalinux-env-check
#
# Not to generate the pycache files in tool
export PYTHONDONTWRITEBYTECODE=1
