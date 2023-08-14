ifndef PETALINUX
$(error "Error: PETALINUX environment variable not set.  Change to the root of your PetaLinux install, and source the settings.sh file")
endif
include apps.common.mk

all: build install

build:
	make -C @source@ $@

clean:
	make -C @source@ $@

.PHONY: install image

install: build 
	# Please add commands below the comments to install your app to target file system.
	# Use $(TARGETINST) to copy data into the target
	# E.g. there is @appname@ user app in the current directory, and I want
	# to copy it into the target "/bin" directory:
	#$(TARGETINST) -d @appname@ /bin/@appname@

help:
	@echo ""
	@echo "Quick reference for various supported build targets for $(INSTANCE)."
	@echo "----------------------------------------------------"
	@echo "  clean                  clean out build objects"
	@echo "  all                    build $(INSTANCE) and install to rootfs host copy"
	@echo "  build                  build subsystem"
	@echo "  install                install built objects to rootfs host copy"
