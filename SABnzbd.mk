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
#       SABnzbd       #
#######################
#
# Package and dependencies definition
INSTALL_PKG=SABnzbd
INSTALL_DEPS=Python zlib openssl sqlite par2cmdline coreutils util-linux busybox Markdown Cheetah pyOpenSSL yenc procps Config-IniFiles

# Cleanup
KEPT_BINS=python nice renice ionice ps par2% busybox adduser deluser
DEL_BINS=
KEPT_LIBS=libcrypto.so% libssl.so% libz.so% libsqlite3.so% python% engines perl5
DEL_LIBS=%.a %.la %.sh pkgconfig
KEPT_INCS=python%
DEL_INCS=
KEPT_FOLDERS=bin lib SABnzbd include

# OpenSSL version used (1.0.0 or 0.9.8)
OPENSSL_VERSION=1.0.0

# Optimisation flags
OFLAGS=-O2


################
# Import rules #
################
#
include rules.mk
