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
INSTALL_PKG=toolbox
INSTALL_DEPS=Config-Crontab Config-IniFiles util-linux coreutils procps par2cmdline busybox

# Cleanup
KEPT_BINS=nice renice ionice ps par2% busybox adduser deluser
DEL_BINS=
KEPT_LIBS=%
DEL_LIBS=%.a %.la %.sh pkgconfig
KEPT_INCS=
DEL_INCS=
KEPT_FOLDERS=bin lib

# Optimisation flags
OFLAGS=-O2


################
# Import rules #
################
#
include rules.mk
