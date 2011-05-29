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

##################
# Standard rules #
##################
#
all: out check-arch $(COMPILE_DEPS) $(INSTALL_PKG)
	@echo "$(if $(strip $^),done,Run \"make help\" to get help info)."

$(ARCHS): out
	@echo "Making SPK $(INSTALL_PKG) version $(SPK_VERSION) for arch $@ type $(patsubst bt-%,%,$(BUILD_TYPE))..."
	@mkdir -p out/logs
	@nice $(MAKE) -f $(TOP_MK) ARCH=$@ $(BUILD_TYPE) > out/logs/$@.log 2>&1 && \
	echo "SPK $(INSTALL_PKG) for arch $@ type $(patsubst bt-%,%,$(BUILD_TYPE)) built successfully" >> out/logs/status.log || \
	echo "Error while building SPK $(INSTALL_PKG) for arch $@ type $(patsubst bt-%,%,$(BUILD_TYPE)), check logs for more details" >> out/logs/status.log &

spk:
	@echo -n "Making SPK $(SPK_NAME) version $(SPK_VERSION) for arch $(SPK_ARCH)..."
	@rm -rf $(OUT_DIR)/spk
	@SPK_NAME=$(SPK_NAME) SPK_VERSION=$(SPK_VERSION) SPK_ARCH=$(SPK_ARCH) \
	./src/buildspk.sh
	@echo " ok"

$(MODELS):
	$(MAKE) -f $(TOP_MK) $(shell grep $@[,.] arch-target.map | cut -d: -f1)

hash:
	@rm -f out/*.hashs
	@for f in out/*.*; \
	do \
		echo ""; \
		echo "`basename $$f`:"; \
		echo "MD5: `md5sum $$f | awk '{ print $$1 }'`"; \
		echo "SHA1: `sha1sum $$f | awk '{ print $$1 }'`"; \
		echo "MD5: `md5sum $$f | awk '{ print $$1 }'`" > out/`basename $$f`.hashs; \
		echo "SHA1: `sha1sum $$f | awk '{ print $$1 }'`" >> out/`basename $$f`.hashs; \
	done
out:
	@mkdir -p out

check-arch:
	@echo -n "Checking whether architecture $(ARCH) is supported..."
ifeq ($(ARCH),all)
	@echo " yes (all archs)"
	@echo "$(OUT_DIR)"
else
	@grep ^$(ARCH): arch-target.map > /dev/null || (echo " no" && exit 1)
	@echo " yes"
	@echo "Target: $(TARGET)"
endif

archs:
	@echo "List of supported architectures and models:"
	@grep ^[^#] arch-target.map | cut -d: -f1,3 --output-delimiter="		"

models: archs

pkgs:
	@echo "List of packages:"
	@echo "$(AVAILABLE_PKGS)"

tests: gcc-version
	@echo "Current variables and their values:"
	@echo "Configuration (auto-detected):"
	@echo "	ARCH				$(ARCH)"
	@echo "	TARGET				$(TARGET)"
	@echo "	GCC_VERSION			$(GCC_VERSION)"
	@echo "	GCC_MAJOR			$(GCC_MAJOR)"
	@echo ""
	@echo "Packages (user defined):"
	@echo "	INSTALL_PKG			$(INSTALL_PKG)"
	@echo "	NONSTD_PKGS_CONFIGURE		$(NONSTD_PKGS_CONFIGURE)"
	@echo "	NONSTD_PKGS_INSTALL		$(NONSTD_PKGS_INSTALL)"
	@echo "	INSTALL_DEPS			$(INSTALL_DEPS)"
	@echo ""
	@echo "Packages (auto-detected):"
	@echo "	AVAILABLE_PKGS			$(AVAILABLE_PKGS)"
	@echo "	EXTRA_PKGS			$(EXTRA_PKGS)"
	@echo "	STD_PKGS_CONFIGURE		$(STD_PKGS_CONFIGURE)"
	@echo "	STD_PKGS_INSTALL_ROOT		$(STD_PKGS_INSTALL_ROOT)"
	@echo "	STD_PKGS_INSTALL_TEMPROOT	$(STD_PKGS_INSTALL_TEMPROOT)"
	@echo ""
	@echo "Directories:"
	@echo "	TEMPROOT			$(TEMPROOT)"
	@echo "	ROOT				$(ROOT)"
	@echo "	EXT_DIR				$(EXT_DIR)"
	@echo "	CUR_DIR				$(CUR_DIR)"
	@echo "	OUT_DIR				$(OUT_DIR)"
	@echo ""
	@echo "Compilation:"
	@echo "	PATH				$(PATH)"
	@echo "	PKG_CONFIG_PATH			$(PKG_CONFIG_PATH)"
	@echo "	CFLAGS				$(CFLAGS)"
	@echo "	CPPFLAGS			$(CPPFLAGS)"
	@echo "	LDFLAGS				$(LDFLAGS)"
	@echo ""
	@echo "SPK Informations :"
	@echo "	SPK_NAME			$(SPK_NAME)"
	@echo "	SPK_VERSION			$(SPK_VERSION)"
	@echo "	SPK_ARCH			$(SPK_ARCH)"

help:
	@echo "usage: make [ARCH=] COMMAND"
	@echo ""
	@echo "The most common COMMANDs are:"
	@echo "  all		Make everything but SPK for ARCH, default command"
	@echo "  buildall	Make everything for all supported archs in background"
	@echo "  hash		Generate MD5 and SHA1 checksums of created SPKs"
	@echo "  out		Create out directory (no need to run this alone)"
	@echo "  check-arch	Check if ARCH is supported"
	@echo "  archs		List all supported archs and models"
	@echo "  models	Same as archs"
	@echo "  pkgs		List all packages"
	@echo "  tests		List current variables and their values"
	@echo "  spk		Make SPK for ARCH"
	@echo "  help		Display this help"
	@echo "  clean		Remove out directory for ARCH"
	@echo "  cleanstatus	Remove status.log (no need to run this alone)"
	@echo "  cleanall	Remove out directory"
	@echo "  realclean	Remove out directory and unpack directory for precomp"
	@echo ""
	@echo "You can also run:"
	@echo "  <arch>			Make everything for specified <arch> in background"
	@echo "  <model>			Make everything for specified <model> in background"
	@echo "  <pkg>				Make <pkg>"
	@echo "  <pkg>.clean			Clean <pkg>"
	@echo "  out/<arch>/<pkg>.unpack	Unpack <pkg> for <arch>"
	@echo "  out/<arch>/<pkg>/syno.config	Configure <pkg> for <arch>"
	@echo "  out/<arch>/<pkg>/syno.install	Make and install <pkg> for <arch>"
	@echo ""

unpack: precomp/$(ARCH)

gcc-version: precomp/$(ARCH)
	$(eval GCC_VERSION:=$(shell $(CC_PATH)/bin/$(TARGET)-gcc --version | head -1 | awk -F" " '{ printf $$3 }'))
	$(eval GCC_MAJOR:=$(shell echo $(GCC_VERSION) | awk -F"." '{ printf $$1}'))

# Cleaning rules
clean:
	rm -rf $(OUT_DIR)

cleanstatus:
	rm -f out/logs/status.log

cleanall:
	rm -rf out

realclean: cleanall
	rm -rf precomp

# Zip rules
$(ARCHS:%=%.zip): out
	@cd out/ && find . -maxdepth 1 -name "*.spk" -a -name "*$(patsubst %.zip,%,$@)*" -a -name "*$(INSTALL_PKG)*" -exec zip '{}'.zip '{}' \;

zip: $(ARCH:%=%.zip)

# Package Cleaner
spk-clean:
	@echo -n "Removing binaries not in KEPT_BINS... "
	@cd $(ROOT)/bin/ > /dev/null 2>&1 && rm -rf $(filter-out $(KEPT_BINS), $(notdir $(wildcard $(ROOT)/bin/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Removing binaries in DEL_BINS... "
	@cd $(ROOT)/bin/ > /dev/null 2>&1 && rm -rf $(filter $(DEL_BINS), $(notdir $(wildcard $(ROOT)/bin/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Removing libraries not in KEPT_LIBS... "
	@cd $(ROOT)/lib/ > /dev/null 2>&1 && rm -rf  $(filter-out $(KEPT_LIBS), $(notdir $(wildcard $(ROOT)/lib/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Removing libraries in DEL_LIBS... "
	@cd $(ROOT)/lib/ > /dev/null 2>&1 && rm -rf  $(filter $(DEL_LIBS), $(notdir $(wildcard $(ROOT)/lib/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Removing includes not in KEPT_INCS... "
	@cd $(ROOT)/include/ > /dev/null 2>&1 && rm -rf $(filter-out $(KEPT_INCS), $(notdir $(wildcard $(ROOT)/include/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Removing includes in DEL_INCS... "
	@cd $(ROOT)/include/ > /dev/null 2>&1 && rm -rf $(filter $(DEL_INCS), $(notdir $(wildcard $(ROOT)/include/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"
	@echo -n "Removing folders not in KEPT_FOLDERS... "
	@cd $(ROOT) > /dev/null 2>&1 && rm -rf $(filter-out $(KEPT_FOLDERS), $(notdir $(wildcard $(ROOT)/*))) > /dev/null 2>&1 && echo " ok" || echo " failed!"

# Package Permissions
spk-perms:
	@echo -n "Setting full permissions for root directory..."
	@chmod -R 777 $(ROOT)/* > /dev/null 2>&1 && echo " ok" || echo " failed!"

# Package Stripper
spk-strip:
	@ls -A $(ROOT)/bin > /dev/null 2>&1 && for f in $(ROOT)/bin/*; \
	do \
		echo -n "Stripping `basename $$f`..."; \
		$(TARGET)-strip $$f > /dev/null 2>&1 && echo " ok" || echo " failed!"; \
	done || echo "Nothing to strip"

# Pre defined build types
bt-release: clean all spk-clean spk-perms spk-strip spk
bt-buildall: all
bt-spk-cleanall: spk-clean
bt-spk-permsall: spk-perms
bt-spk-stripall: spk-strip
bt-zipall: zip

# Implicit rule to define BUILD_TYPE
$(BUILD_TYPES:%=imp-%):imp-%:
	$(eval BUILD_TYPE=bt-$*)

# Related targets
$(BUILD_TYPES:%=%all):%all: imp-% $(ARCHS)

release: bt-release


##################
# Specific rules #
##################
#
# Unpack the toolchain, remove conflicting flex and correct buggy config.h on some arch.
precomp/$(ARCH):
	grep ^$(ARCH) arch-target.map
	mkdir -p precomp/$(ARCH)
	tar xf ext/precompiled/$(ARCH).* -C precomp/$(ARCH)
	rm -f $(CC_PATH)/bin/flex
	rm -f $(CC_PATH)/bin/flex++
	if [ -f $(SYNO_H) ] && [ -f $(CONFIG_H) ] && cat $(SYNO_H) | grep -q '[0-9]define[0-9]'; then \
		sed -i -e "s|^#include|//#include|" $(CONFIG_H); \
		echo "config.h has been corrected"; \
	else \
		echo "config.h is not buggy"; \
	fi
	if [ -f $(SYNO_H) ] && cat $(SYNO_H) | grep -q '[0-9]define[0-9]'; then \
		find $@ -type f -name '*.h' -exec sed -i -e "s|^#include <linux/syno.h>$$|//#include <linux/syno.h>|" {} \;; \
		echo "References to syno.h has been deleted"; \
	else \
		echo "syno.h is not buggy"; \
	fi
	find $@ -type f -name '*.la' -exec sed -i -e "s|^libdir=.*$$|libdir='$(CUR_DIR)/$(CC_PATH)/$(TARGET)/lib'|" {} \;

# For each package, create a out/<arch>/<pkg>.unpack target that unpacks the
# source to out/<arch>/<versionned pkg> and creates a symlink called
# out/<arch>/<pkg> that points to it.
$(AVAILABLE_PKGS:%=$(OUT_DIR)/%.unpack):$(OUT_DIR)/%.unpack:
	@echo $@ ----\> $^
	@mkdir -p $(OUT_DIR)
	@if [ -f $(PKG_DIR)/$**$($(shell echo $* | tr [:lower:] [:upper:])_VERSION)*.t* ]; then \
		tar mxf $(PKG_DIR)/$**$($(shell echo $* | tr [:lower:] [:upper:])_VERSION)*.t* -C $(OUT_DIR); \
	elif [ -f $(PKG_DIR)/$**$($(shell echo $* | tr [:lower:] [:upper:])_VERSION)*.zip ]; then \
		unzip $(PKG_DIR)/$**$($(shell echo $* | tr [:lower:] [:upper:])_VERSION)*.zip -d $(OUT_DIR); \
	fi
	@cd $(OUT_DIR)/ && [ -e $* ] || ln -s $*-* $*
	touch $@

# For each standard package, create a out/<arch>/<pkg>/syno.config target.
# This target <prefix>/syno.config depends on <prefix>.unpack and
# precomp/<arch> and handles calling the standard ./configure script with the
# right options.
$(STD_PKGS_CONFIGURE:%=$(OUT_DIR)/%/syno.config): %/syno.config: %.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--disable-gtk --disable-nls \
			--enable-static --enable-daemon \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

# For each package to be installed, create a out/<arch>/<pkg>/syno.install.
# This target <prefix>/syno.install depends on <prefix>/syno.config and
# handles calling make and make install to install the package in "root".
$(STD_PKGS_INSTALL:%=$(OUT_DIR)/%/syno.install): $(OUT_DIR)/%/syno.install: $(OUT_DIR)/%/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@)
	make -C $(dir $@) install
	touch $@

# For each package, create a easy to use target called <pkg> that depends
# on out/<arch>/<package>/syno.install
$(AVAILABLE_PKGS): %: $(OUT_DIR)/%/syno.install
	@echo $@ ----\> $^

# For each package, create a easy to use <pkg>.clean target that deletes
# all out/<arch>/<pkg>*
$(AVAILABLE_PKGS:%=%.clean):
	rm -rf $(OUT_DIR)/$(patsubst %.clean,%, $@)*

# Perl module installation
$(PERL_PKGS:%=$(OUT_DIR)/%/syno.install):%/syno.install: %.unpack precomp/$(ARCH)
	cd $* && \
	perl Makefile.PL INSTALL_BASE=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	make -C $(dir $@)
	make -C $(dir $@) install

# Python modules installation
$(PYTHON_PKGS:%=$(OUT_DIR)/%/syno.install):%/syno.install: $(OUT_DIR)/Python/syno.config %.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/lib/python2.7/site-packages/
	cd $* && \
	PYTHONPATH="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/lib/python2.7/site-packages/:$(CUR_DIR)/$*" \
	LDFLAGS="$(LDFLAGS)" \
	../Python/hostpython setup.py install --prefix $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	touch $@

$(META_PKGS) $(NONSTD_MODULE_PKGS):%: $(OUT_DIR)/%/syno.install


##############################
# User defined, non-standard #
# configure rules            #
##############################
#
$(OUT_DIR)/transmission/syno.config: $(OUT_DIR)/openssl/syno.install $(OUT_DIR)/zlib/syno.install $(OUT_DIR)/curl/syno.install $(OUT_DIR)/libevent/syno.install

$(OUT_DIR)/umurmur/syno.config: $(OUT_DIR)/protobuf-c/syno.install $(OUT_DIR)/libconfig/syno.install $(OUT_DIR)/polarssl/syno.install $(OUT_DIR)/openssl/syno.install $(OUT_DIR)/umurmur.unpack precomp/$(ARCH)

$(OUT_DIR)/libpar2/syno.config: $(OUT_DIR)/libsigc++/syno.install $(OUT_DIR)/libpar2.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	patch -d $(dir $@) -p 1 -i $(EXT_DIR)/others/libpar2-0.2-bugfixes.patch
	patch -d $(dir $@) -p 1 -i $(EXT_DIR)/others/libpar2-0.2-cancel.patch
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/libsigc++/syno.config: $(OUT_DIR)/libsigc++.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/libxml2/syno.config: $(OUT_DIR)/zlib/syno.install $(OUT_DIR)/libxml2.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/nzbget/syno.config: $(OUT_DIR)/ncurses/syno.terminfo $(OUT_DIR)/openssl/syno.install $(OUT_DIR)/libsigc++/syno.install $(OUT_DIR)/libxml2/syno.install $(OUT_DIR)/libpar2/syno.install $(OUT_DIR)/nzbgetweb/syno.install $(OUT_DIR)/nzbget.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" CXXFLAGS="$(CPPFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/coreutils/syno.config: $(OUT_DIR)/coreutils.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/openssl/syno.config: $(OUT_DIR)/zlib/syno.install $(OUT_DIR)/openssl.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
ifeq ($(shell echo $(OPENSSL_VERSION) | sed 's/[a-zA-Z]//g'),1.0.0)
	@echo "Using OpenSSL version 1.0.0"
	cd $(OUT_DIR)/openssl && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./Configure --prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			zlib-dynamic shared \
			"syno:$(TARGET)-gcc:-O3 $(CFLAGS)::(unknown)::-ldl $(LDFLAGS):BN_LLONG:::::::::::::::dlfcn:linux-shared:-fPIC::.so.\\\$$\(SHLIB_MAJOR\).\\\$$\(SHLIB_MINOR\):"
endif
ifeq ($(shell echo $(OPENSSL_VERSION) | sed 's/[a-zA-Z]//g'),0.9.8)
	@echo "Using OpenSSL version 0.9.8"
	cd $(OUT_DIR)/openssl && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./Configure --prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			zlib-dynamic shared \
			"syno:$(TARGET)-gcc:-O3 $(CFLAGS)::(unknown)::-ldl $(LDFLAGS):BN_LLONG::::::::::::dlfcn:linux-shared:-fPIC::.so.\\\$$\(SHLIB_MAJOR\).\\\$$\(SHLIB_MINOR\):"
endif
	touch $(OUT_DIR)/openssl/syno.config

$(OUT_DIR)/zlib/syno.config: $(OUT_DIR)/zlib.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(OUT_DIR)/zlib && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	CHOST=$(TARGET) \
	./configure --prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) --static --shared
	touch $(OUT_DIR)/zlib/syno.config

$(OUT_DIR)/curl/syno.config: $(OUT_DIR)/zlib/syno.install $(OUT_DIR)/openssl/syno.install  $(OUT_DIR)/curl.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(OUT_DIR)/curl && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			--with-random=/dev/urandom \
			--with-ssl --with-zlib \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $(OUT_DIR)/curl/syno.config

$(OUT_DIR)/polarssl/syno.config: $(OUT_DIR)/polarssl.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	@sed -i "1i\CC=$(TARGET)-gcc" $(OUT_DIR)/polarssl/Makefile $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "/cd programs/d" $(OUT_DIR)/polarssl/Makefile
	@sed -i "/cd tests/d" $(OUT_DIR)/polarssl/Makefile
	@sed -i "/^DESTDIR/ c\DESTDIR=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))" $(OUT_DIR)/polarssl/Makefile
	@sed -i "/\.SILENT:/d" $(OUT_DIR)/polarssl/Makefile $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "s/ -Wdeclaration-after-statement//g" $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "/^CFLAGS/a \CFLAGS+=$(CFLAGS)" $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "/# CFLAGS += -fPIC/ c\CFLAGS += -fPIC" $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "/all: static/ c\all: static shared" $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "s/^\tar /\t$(TARGET)-ar /" $(OUT_DIR)/polarssl/library/Makefile
	@sed -i "s/^\tranlib /\t$(TARGET)-ranlib /" $(OUT_DIR)/polarssl/library/Makefile
	touch $(OUT_DIR)/polarssl/syno.config

$(OUT_DIR)/protobuf-c/syno.config: $(OUT_DIR)/protobuf-c.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(OUT_DIR)/protobuf-c && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			--disable-protoc \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $(OUT_DIR)/protobuf-c/syno.config

$(OUT_DIR)/Python/host.install: $(OUT_DIR)/ncurses/syno.install $(OUT_DIR)/readline/syno.install $(OUT_DIR)/zlib/syno.install $(OUT_DIR)/bzip2/syno.install $(OUT_DIR)/sqlite/syno.install $(OUT_DIR)/openssl/syno.install $(OUT_DIR)/libffi/syno.install $(OUT_DIR)/Python.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	patch -d $(dir $@) -p1 -i $(EXT_DIR)/others/Python-2.7.1-hostcompile.patch
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --with-zlib=/usr/include
	make -C $(dir $@)
	mv $(dir $@)python $(dir $@)hostpython
	mv $(dir $@)Parser/pgen $(dir $@)Parser/hostpgen
	touch $@

$(OUT_DIR)/Python/syno.config: $(OUT_DIR)/Python/host.install
	@echo $@ ----\> $^
	patch -d $(dir $@) -p1 -i $(EXT_DIR)/others/Python-2.7.1-xcompile.patch
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))" \
			--with-cxx-main=$(TARGET)-g++ \
			CFLAGS="-DPATH_MAX=4096 $(CFLAGS)" LDFLAGS="$(LDFLAGS)" CPPFLAGS="$(CPPFLAGS)"
	touch $@

$(OUT_DIR)/util-linux/syno.config: $(OUT_DIR)/ncurses/syno.install $(OUT_DIR)/util-linux.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))" \
			CFLAGS="-DPATH_MAX=4096 $(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/ncurses/syno.config: $(OUT_DIR)/ncurses.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			--with-shared --enable-rpath --enable-overwrite \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/readline/syno.config: $(OUT_DIR)/ncurses/syno.install $(OUT_DIR)/readline.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/libffi/syno.config: $(OUT_DIR)/libffi.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/tcl/syno.config: $(OUT_DIR)/tcl.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@)unix && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	ac_cv_func_strtod=yes \
	tcl_cv_strtod_buggy=1 \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	@sed -i "s|\./\$${TCL_EXE}|\$$\{TCL_EXE\}|" $(OUT_DIR)/tcl/unix/Makefile
	touch $@

$(OUT_DIR)/psmisc/syno.config: $(OUT_DIR)/psmisc.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	ac_cv_func_malloc_0_nonnull=yes \
	ac_cv_func_realloc_0_nonnull=yes \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/git/syno.config: $(OUT_DIR)/curl/syno.install $(OUT_DIR)/git.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	ac_cv_c_c99_format=yes \
	ac_cv_fread_reads_directories=yes \
	ac_cv_snprintf_returns_bogus=no \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/sysvinit/syno.config: $(OUT_DIR)/sysvinit.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	touch $@

$(OUT_DIR)/par2cmdline/syno.config: $(OUT_DIR)/par2cmdline.unpack precomp/$(ARCH) gcc-version
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	@echo $(shell if [ $(GCC_MAJOR) -eq 4 ]; then \
			patch -d $(dir $@) -p 1 -i $(EXT_DIR)/others/par2cmdline-0.4-gcc4.patch; \
		fi)
	touch $@

$(OUT_DIR)/shadow/syno.config: $(OUT_DIR)/shadow.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	ac_cv_func_setpgrp_void=yes \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
			CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)"
	touch $@

$(OUT_DIR)/busybox/syno.config: $(OUT_DIR)/busybox.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	make -C $(dir $@) ARCH=$(ARCH) CROSS_COMPILE=$(TARGET)- CONFIG_PREFIX=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.config,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" allnoconfig menuconfig
	touch $@


##############################
# User defined, non-standard #
# install rules              #
##############################
#
$(OUT_DIR)/pip/syno.install: $(OUT_DIR)/setuptools/syno.install $(OUT_DIR)/Python/syno.config $(OUT_DIR)/pip.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/lib/python2.7/site-packages/
	cd $(dir $@) && \
	PYTHONPATH="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/lib/python2.7/site-packages/:$(CUR_DIR)/$*" \
	LDFLAGS="$(LDFLAGS)" \
	../Python/hostpython setup.py install --prefix $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	sed -e "s|%CORRECT_PATH%|$(CUR_DIR)/$(OUT_DIR)|g" $(EXT_DIR)/others/pip-1.0.1-syno.tmpl.patch | patch -d $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin -p1
	touch $@

$(OUT_DIR)/CouchPotato.install:
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	cd $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) && git clone https://github.com/RuudBurger/CouchPotato.git
	rm -rf $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/Sick-Beard $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/CouchPotato/.git*
	touch $@

$(OUT_DIR)/SickBeard.install:
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	cd $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) && git clone https://github.com/midgetspy/Sick-Beard.git
	mv $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/Sick-Beard $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/SickBeard
	rm -rf $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/Sick-Beard $(if $(filter $(patsubst $(OUT_DIR)/%.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/SickBeard/.git*
	touch $@

$(OUT_DIR)/SABnzbd/syno.install: $(OUT_DIR)/SABnzbd.unpack
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/SABnzbd
	cp -Rf $(OUT_DIR)/SABnzbd/* $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/SABnzbd
	touch $@

$(OUT_DIR)/Python/syno.install: $(OUT_DIR)/Python/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@) distclean
	cd $(dir $@) && \
	PKG_CONFIG_PATH=$(PKG_CONFIG_PATH) \
	./configure --host=$(TARGET) --target=$(TARGET) \
			--build=i686-pc-linux \
			--prefix="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))" \
			--with-cxx-main=$(TARGET)-g++ \
			CFLAGS="-DPATH_MAX=4096 $(CFLAGS)" LDFLAGS="$(LDFLAGS)" CPPFLAGS="$(CPPFLAGS)"
	make -C $(dir $@) HOSTPYTHON=./hostpython HOSTPGEN=./Parser/hostpgen \
			BLDSHARED="$(TARGET)-gcc -shared" CROSS_COMPILE=$(TARGET)- \
			CROSS_COMPILE_TARGET=yes
	make -C $(dir $@) install HOSTPYTHON=./hostpython \
			HOSTPGEN=./Parser/hostpgen BLDSHARED="$(TARGET)-gcc -shared" \
			CROSS_COMPILE=$(TARGET)- CROSS_COMPILE_TARGET=yes
	rm -rf $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/lib/python2.7/test
	rm -f $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/lib/python2.7/config/*.a
	touch $@

$(OUT_DIR)/bzip2/syno.install: $(OUT_DIR)/bzip2.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	make -C $(dir $@) libbz2.a bzip2 bzip2recover CC="$(TARGET)-gcc" AR="$(TARGET)-ar" RANLIB="$(TARGET)-ranlib" LDFLAGS="$(LDFLAGS)"
	make -C $(dir $@) install PREFIX="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))"
	touch $@

$(OUT_DIR)/sysvinit/syno.install: $(OUT_DIR)/sysvinit/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@) SBIN="killall5" CC="$(TARGET)-gcc" LDFLAGS="$(LDFLAGS)" CFLAGS="$(CFLAGS)" CPPFLAGS="$(CPPFLAGS)"
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/
	cp $(dir $@)src/killall5 $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/
	touch $@

$(OUT_DIR)/tcl/syno.install: $(OUT_DIR)/tcl/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@)unix
	make -C $(dir $@)unix install
	touch $@

$(OUT_DIR)/coreutils/syno.install: $(OUT_DIR)/coreutils/syno.config
	@echo $@ ----\> $^
	cd $(dir $@)man && for f in *.x; \
	do \
		touch `basename $$f .x`.1; \
	done;
	make -C $(dir $@)
	make -C $(dir $@) install
	touch $@

$(OUT_DIR)/util-linux/syno.install: $(OUT_DIR)/util-linux/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@)schedutils ionice
	make -C $(dir $@)sys-utils renice
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/
	cp $(dir $@)schedutils/ionice $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/
	cp $(dir $@)sys-utils/renice $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/
	touch $@

$(OUT_DIR)/psmisc/syno.install: $(OUT_DIR)/psmisc/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@) ac_cv_func_malloc_0_nonnull=yes ac_cv_func_realloc_0_nonnull=yes
	make -C $(dir $@) install
	touch $@

$(OUT_DIR)/libxml2/syno.install: $(OUT_DIR)/libxml2/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@)
	make -C $(dir $@) install
	touch $@

$(OUT_DIR)/openssl/syno.install: $(OUT_DIR)/openssl/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@)
	make -C $(dir $@) install
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/var/
	cp $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/ssl/openssl.cnf $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/var/
	touch $@

$(OUT_DIR)/libsigc++/syno.install: $(OUT_DIR)/libsigc++/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@)
	make -C $(dir $@) install
	touch $@

$(OUT_DIR)/libpar2/syno.install: $(OUT_DIR)/libpar2/syno.config
	@echo $@ ----\> $^
	make -C $(dir $@) PKG_CONFIG_PATH=$(PKG_CONFIG_PATH)
	make -C $(dir $@) install
	touch $@

$(OUT_DIR)/procps/syno.install: $(OUT_DIR)/procps.unpack precomp/$(ARCH) $(OUT_DIR)/ncurses/syno.install
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/ $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/usr/share/man/man1/
	make -C $(dir $@) SHARED=0 CC=$(TARGET)-gcc CFLAGS="-DPATH_MAX=4096 $(CFLAGS)" LDFLAGS="$(LDFLAGS)" \
		DESTDIR=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) \
		install="install" \
		usr/bin="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/" \
		usr/proc/bin="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/" \
		sbin="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/" \
		bin="$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin/" \
		SKIP="\$$(MANFILES)" install
	touch $@

$(OUT_DIR)/nzbgetweb/syno.install: $(OUT_DIR)/nzbgetweb.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	cp -R $(dir $@) $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))
	touch $@

$(OUT_DIR)/busybox/syno.install: $(OUT_DIR)/busybox/syno.config
	@echo $@ ----\> $^
	mkdir -p $(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT))/bin
	make -C $(dir $@) ARCH=$(ARCH) CROSS_COMPILE=$(TARGET)- CONFIG_PREFIX=$(if $(filter $(patsubst $(OUT_DIR)/%/syno.install,%,$@), $(INSTALL_DEPS) $(INSTALL_PKG)),$(ROOT),$(TEMPROOT)) CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" all install
	touch $@


##############
# Meta Rules #
##############
$(OUT_DIR)/busybox/syno.lightusermanagement: $(OUT_DIR)/busybox.unpack precomp/$(ARCH)
	@echo $@ ----\> $^
	cp $(EXT_DIR)/others/busybox-lightusermanagement.config $(OUT_DIR)/busybox/.config
	make -C $(dir $@) ARCH=$(ARCH) CROSS_COMPILE=$(TARGET)- CONFIG_PREFIX=$(ROOT) CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" all install
	touch $@

$(OUT_DIR)/ncurses/syno.terminfo: $(OUT_DIR)/ncurses/syno.install
	@echo $@ ----\> $^
	mkdir -p  $(ROOT)/share/terminfo
	cp -R $(TEMPROOT)/share/terminfo $(ROOT)/share/terminfo
	touch $@

$(OUT_DIR)/toolbox.install: $(OUT_DIR)/Config-IniFiles/syno.install $(OUT_DIR)/util-linux/syno.install $(OUT_DIR)/coreutils/syno.install $(OUT_DIR)/procps/syno.install $(OUT_DIR)/par2cmdline/syno.install $(OUT_DIR)/busybox/syno.lightusermanagement
