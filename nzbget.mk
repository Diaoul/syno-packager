# Copyright 2010-2011 Antoine Bertin
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

####################
# Import variables #
####################
#
include variables.mk


#######################
# Light Package Rules #
#        nzbget       #
#######################
#
# Package and dependencies definition
INSTALL_PKG=nzbget
INSTALL_DEPS=libpar2 libxml2 libsigc++ openssl zlib nzbgetweb coreutils util-linux

# Cleanup
KEPT_BINS=nzbget busybox adduser deluser nice ionice
DEL_BINS=
KEPT_LIBS=libcrypto.so% libpar2.so% libsigc-2.0.so% libssl.so% libxml2.so% libz.so%
DEL_LIBS=%.a %.la %.sh
KEPT_INCS=
DEL_INCS=
KEPT_FOLDERS=bin lib nzbgetweb

# OpenSSL version used (1.0.0 or 0.9.8)
OPENSSL_VERSION=0.9.8

# Optimisation flags
OFLAGS=-O0


################
# Import rules #
################
#
include rules.mk
