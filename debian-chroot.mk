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
INSTALL_PKG=debian-chroot
INSTALL_DEPS=coreutils
COMPILE_DEPS=$(INSTALL_DEPS)

# Cleanup
KEPT_BINS=chroot
DEL_BINS=
KEPT_LIBS=
DEL_LIBS=
KEPT_INCS=
DEL_INCS=
KEPT_FOLDERS=bin var chroottarget

# Turn sudo cp/rm/tar on
CP_SUDO=yes
RM_SUDO=yes
TAR_SUDO=yes


################
# Import rules #
################
#
include rules.mk
