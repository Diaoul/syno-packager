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
#######################
#
# Package and dependencies definition
INSTALL_PKG=perl
INSTALL_DEPS=perl-dbi perl-dbd-sqlite

# Cleanup
KEPT_BINS=%
DEL_BINS=
KEPT_LIBS=%
DEL_LIBS=
KEPT_INCS=%
DEL_INCS=
KEPT_FOLDERS=bin lib CORE

################
# Import rules #
################
#
include rules.mk


################
# Custom rules #
################
#
perl: install-optware-perl install-optware-perl-dbi install-optware-perl-dbd-sqlite
	@ls -A $(ROOT)/bin/ > /dev/null 2>&1 && for f in $(ROOT)/bin/*; \
	do \
		echo -n "Changing references to /opt/ in `basename $$f`..."; \
		sed -i "s|/opt/bin|/usr/local/$(INSTALL_PKG)/bin|g" $$f > /dev/null 2>&1 && echo " ok" || echo " failed!"; \
	done || echo "No changes done to files headers"
	@echo -n "Creating symlink to CORE"
	@cd $(ROOT) && ln -s $(shell chrpath -l optware/$(OPTWARE_ARCH)/builds/perl-*-ipk/opt/bin/perl | sed "s|^.*:/opt/lib/\(.*\)$$|lib/\1|") CORE > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Changing rpath of perl..."
	@chrpath -r /usr/local/$(INSTALL_PKG)/lib/:/usr/local/$(INSTALL_PKG)/CORE $(ROOT)/bin/perl > /dev/null 2>&1 && echo " ok" || echo " failed!"
