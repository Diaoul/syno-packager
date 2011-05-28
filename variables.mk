# Copyright 2010 Saravana Kannan
# Copyright 2010-2011 Antoine Bertin
# <sarav dot devel [ignore this] at gmail period com>
# <diaoulael [ignore this] at users.sourceforge period net>
#
# This file is part of syno-packager.
#
# syno-packager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# syno-packager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with syno-packager.  If not, see <http://www.gnu.org/licenses/>.

# Default arch
ARCH?=88f5281

# Directories
ifeq ($(ARCH),all)
	OUT_DIR=out
else
	OUT_DIR=out/$(ARCH)
endif
CUR_DIR:=$(PWD)
EXT_DIR=$(CUR_DIR)/ext
PKG_DIR=$(EXT_DIR)/packages
TEMPROOT=$(CUR_DIR)/$(OUT_DIR)/temproot
ROOT=$(CUR_DIR)/$(OUT_DIR)/root

# Non-standard package list
NONSTD_PKGS_CONFIGURE=SABnzbd Python zlib ncurses readline bzip2 openssl libffi tcl psmisc sysvinit coreutils util-linux git curl par2cmdline procps libxml2 nzbget libsigc++ libpar2 polarssl shadow busybox protobuf-c
NONSTD_PKGS_INSTALL=SABnzbd Python bzip2 tcl psmisc sysvinit util-linux coreutils procps libxml2 libsigc++ openssl libpar2 nzbgetweb busybox
PERL_PKGS=Config-IniFiles
PYTHON_PKGS=Markdown Cheetah pyOpenSSL yenc periscope pip setuptools BeautifulSoup
META_PKGS=toolbox

# Using arch-target.map to define some variables
ARCHS=$(shell cat arch-target.map | cut -d: -f1)
MODELS=$(shell cat arch-target.map | cut -d: -f3 | sed -e 's/S /S/g; s/, / /g')
TARGET=$(shell grep ^$(ARCH): arch-target.map | cut -d: -f 2)
CC_PATH=precomp/$(ARCH)$(shell grep ^$(ARCH): arch-target.map | cut -d: -f 4)/$(TARGET)

# Define a magical regex to parse packages
REGEX=^([\+\w-]*?)(-autoconf)?-?([0-9][0-9.a-zRC]+(-pre[0-9])?)(-stable|-gpl|-src)?\.(tgz|tar\.gz|tar\.bz2|zip)$$

# List all packages in $(PKG_DIR) directory
ALL_PKGS=$(strip $(foreach pkg, \
	$(notdir $(wildcard $(PKG_DIR)/*.tgz $(PKG_DIR)/*.tar.gz $(PKG_DIR)/*.tar.bz2 $(PKG_DIR)/*.zip)), \
	$(shell echo $(pkg) | perl -p -e 's/$(REGEX)/\1/') \
))
AVAILABLE_PKGS=$(sort $(ALL_PKGS))

# Handle multi-version packages by creating a PKG_VERSION variable that holds the lowest version number found
$(foreach MVP, \
	$(strip $(shell echo $(ALL_PKGS) | tr " " "\n" | sort | uniq -d | tr "\n" " " | tr [:lower:] [:upper:])), \
	$(call $(eval $(MVP)_VERSION=$(shell find $(PKG_DIR)/ -iname "$(MVP)*" -printf "%f" -quit | perl -p -e 's/$(REGEX)/\3/'))) \
)

# Extra rules for very non-standard packages (no binaries, no source code)
EXTRA_PKGS=$(filter-out $(AVAILABLE_PKGS), $(strip $(INSTALL_PKG) $(INSTALL_DEPS)))

# Sort package names in variables for further use depending of their "standardness"
STD_PKGS_CONFIGURE=$(filter-out $(NONSTD_PKGS_CONFIGURE) $(PERL_PKGS) $(PYTHON_PKGS), $(AVAILABLE_PKGS))
STD_PKGS_INSTALL=$(filter-out $(NONSTD_PKGS_INSTALL) $(PERL_PKGS) $(PYTHON_PKGS), $(AVAILABLE_PKGS))

# Environment variables common to all package compilation
ifeq ($(ARCH),88f628x)
	EXTRA_ARM_CFLAGS=-mfloat-abi=soft
endif
ifeq ($(ARCH),88f5281)
	EXTRA_ARM_CFLAGS=-mfloat-abi=soft
endif
PATH:=$(CUR_DIR)/$(CC_PATH)/bin:$(PATH)
PKG_CONFIG_PATH=$(ROOT)/lib/pkgconfig:$(TEMPROOT)/lib/pkgconfig
CFLAGS=$(OFLAGS) -I$(TEMPROOT)/include -I$(ROOT)/include $(EXTRA_ARM_CFLAGS)# -I$(CUR_DIR)/$(CC_PATH)/include
CPPFLAGS=$(CFLAGS)
LDFLAGS=-Wl,-rpath-link,$(ROOT)/lib -Wl,-rpath-link,$(TEMPROOT)/lib -Wl,-rpath,/usr/local/$(INSTALL_PKG)/lib -L$(TEMPROOT)/lib -L$(ROOT)/lib# -L$(CUR_DIR)/$(CC_PATH)/lib

# Variables used to check for bugged config.h and syno.h
SYNO_H=precomp/$(ARCH)$(shell grep ^$(ARCH): arch-target.map | cut -d: -f 4)/$(TARGET)/include/linux/syno.h
CONFIG_H=precomp/$(ARCH)$(shell grep ^$(ARCH): arch-target.map | cut -d: -f 4)/$(TARGET)/include/linux/config.h

# Packaging variables
SPK_NAME=$(INSTALL_PKG)
SPK_VERSION=$(shell echo $(notdir $(wildcard $(PKG_DIR)/$(INSTALL_PKG)*.*)) | perl -p -e 's/$(REGEX)/\3/; s/^\s*$$/tip/')
SPK_ARCH="$(ARCH)"

# Build types
BUILD_TYPES=release build zip spk-clean spk-perms spk-strip

# First called Makefile
TOP_MK=$(firstword $(MAKEFILE_LIST))
