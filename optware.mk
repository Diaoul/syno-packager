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

###########
# Install #
###########
#
optware:
	svn co http://svn.nslu2-linux.org/svnroot/optware/trunk optware

optware-update:
	cd optware/ ; svn up

optware-%: optware
	$(MAKE) -C optware/ $(OPTWARE_ARCH)-target
	cd optware/$(OPTWARE_ARCH)/ && $(MAKE) directories ipkg-utils toolchain $*

install-optware-%: optware-%-ipk
	@mkdir -p $(if $(filter $*, $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/
	@cp -R optware/$(OPTWARE_ARCH)/builds/$*-*-ipk/opt/* $(if $(filter $*, $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/ > /dev/null 2>&1 && echo "Files copied for $* (/opt)" || echo "Nothing to copy for $* (/opt)"
	@cp -R optware/$(OPTWARE_ARCH)/builds/$*-*-ipk/usr/local/perl/* $(if $(filter $*, $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/ > /dev/null 2>&1 && echo "Files copied for $* (/usr/local/$(INSTALL_PKG))" || echo "Nothing to copy for $* (/usr/local/$(INSTALL_PKG)"
	@ls -A optware/$(OPTWARE_ARCH)/builds/$*-*-ipk/opt/bin/ > /dev/null 2>&1 && for f in optware/$(OPTWARE_ARCH)/builds/$*-*-ipk/opt/bin/*; \
	do \
		echo -n "Changing rpath for `basename $$f`..."; \
		chrpath -r /usr/local/$(INSTALL_PKG)/lib $(if $(filter $*, $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/`basename $$f` > /dev/null 2>&1 && echo " ok" || echo " failed!"; \
	done || echo "No changes of rpath needed"

