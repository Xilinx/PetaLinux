#!/bin/bash
#
# DESCRIPTION:
# This script helps to setup the live tool when you have a pre installed tool
# and want to do some updates on the scripts.
#
# cp livetool_setup.sh <PetaLinux_repo>/
# cd PetaLinux_repo/
# ./scripts/bash/livetool_setup.sh <Absolute Path to PetaLinux Installed tool>
# Example:
# 	./scripts/bash/livetool_setup.sh /opt/PetaLinuxTool/
#

PetaLinuxRepo=`pwd`
PetaLinuxTool="$1"

if [ -z $PetaLinuxTool ] || [ ! -e $PetaLinuxTool ]; then
	echo "ERROR: Please Specify valid PetaLinux Tool Dir $PetaLinuxTool"
	exit 255
fi

LINK_DIRS="components/yocto/source components/yocto/decoupling \
	components/yocto/buildtools components/yocto/buildtools_extended \
	components/xsct tools/xsct:components/xsct \
	"

echo "INFO: Unlinking existing tool links if any"
for Dir in $LINK_DIRS; do
	if [ -L "$PetaLinuxRepo/$Dir" ]; then
		unlink "$PetaLinuxRepo/$Dir"
	fi
done
echo "INFO: Unlinking Done"
	

echo "INFO: Linking the components"
for Dir in $LINK_DIRS; do
	Input=${Dir%%:*}
	Output=${Dir##*:}
	if [ -d $PetaLinuxTool/$Input ]; then
		if [ ! -d $(dirname $Output) ]; then
			mkdir -p $(dirname $Output)
		fi
		ln -s $PetaLinuxTool/$Input $PetaLinuxRepo/$Output
	fi
done
echo "INFO: Linking Done"


