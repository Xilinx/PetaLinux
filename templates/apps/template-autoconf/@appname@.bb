#
# This is the GPIO-DEMO apllication recipe
#
#

SUMMARY = "@appname@ autoconf application"
SECTION = "PETALINUX/apps"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"
SRC_URI = "file://@appname@ \
        "
S = "${WORKDIR}/@appname@"
CFLAGS:prepend = "-I ${S}/include"
inherit autotools
