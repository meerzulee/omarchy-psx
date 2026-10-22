.PHONY: check check-root check-ps4
check: check-root check-ps4
check-root:
	python3 scripts/check-provenance
	python3 scripts/check-ps5-image-source
	python3 scripts/check-ps5-compatibility --validate-manifest
	sh -n rootfs/initramfs/init
	sh -n platforms/ps5/rootfs/probe-init
	python3 -B -m unittest discover -s tests -v
check-ps4:
	./platforms/ps4/scripts/check-source
