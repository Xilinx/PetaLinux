#
# This file is the @appname@ recipe.
#

SUMMARY = "Simple @appname@ to use dfx_dtg_versal_full class"
SECTION = "PETALINUX/apps"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit dfx_dtg_versal_full

COMPATIBLE_MACHINE:versal = ".*"

