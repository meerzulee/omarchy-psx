.PHONY: check check-root check-ps4
check: check-root check-ps4
check-root:
	python3 scripts/check-provenance
	sh -n rootfs/initramfs/init
	python3 -B -m unittest discover -s tests -v
check-ps4:
	./platforms/ps4/scripts/check-source
