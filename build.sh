#!/bin/bash
# A50 One UI 9 port - build script
# Usage: ./build_rom.sh system | vendor | product | kernel | all
# ---- edit paths here ----
WORK=~/s26fe
SYS=$WORK/sys17/system
SYSCFG=$WORK/sys17/config
VENDOR=~/cmp/v17
VCFG=~/cmp/v17_fs_config
VCTX=~/cmp/v17_merged_fc
KERNEL=~/mint14
MKFS=~/rom85/tools/mkfs.erofs
USB=/media/gord/C887-5F91
# --------------------------

check() {  # $1=image  $2=minimum size in MB
  local mb=$(( $(stat -c%s "$1" 2>/dev/null || echo 0) / 1048576 ))
  if [ "$mb" -lt "$2" ]; then echo "!! $1 is only ${mb} MB - build FAILED, not copying"; return 1; fi
  echo "OK $1 = ${mb} MB"
  if [ -d "$USB" ]; then cp "$1" "$USB/" && sync && echo "md5 laptop: $(md5sum < "$1" | cut -c1-32)" && echo "md5 usb:    $(md5sum < "$USB/$(basename "$1")" | cut -c1-32)"; else echo "(USB stick not mounted - image left in $WORK)"; fi
}

build_system() {
  sed -i '/^\s*$/d' $SYSCFG/system_fs_config $SYSCFG/system_file_contexts
  cd $WORK && rm -f system_new.img
  $MKFS -zlz4hc --mount-point=/system --fs-config-file=$SYSCFG/system_fs_config \
    --file-contexts=$SYSCFG/system_file_contexts system_new.img $SYS 2>&1 | grep -aiE 'fail|err|canned'
  check $WORK/system_new.img 1000
}

build_vendor() {
  cd $WORK && rm -f vendor_new.img
  $MKFS -zlz4hc --mount-point=/vendor --fs-config-file=$VCFG --file-contexts=$VCTX vendor_new.img $VENDOR 2>&1 | grep -aiE 'fail|err|canned'
  check $WORK/vendor_new.img 100
}

build_product() {
  mkdir -p ~/emptyprod; printf ' 0 0 0755\n' > ~/emptyprod_fsc
  echo '/product(/.*)? u:object_r:system_file:s0' > ~/emptyprod_fc
  cd $WORK && rm -f product_empty.img
  $MKFS -zlz4hc --mount-point=/product --fs-config-file=$HOME/emptyprod_fsc --file-contexts=$HOME/emptyprod_fc product_empty.img ~/emptyprod
  [ -f product_empty.img ] && echo "OK product_empty.img" && [ -d "$USB" ] && cp product_empty.img "$USB/" && sync
}

build_kernel() {
  cd $KERNEL && rm -f out/boot.img
  ./build_ultimate.sh > ~/build_kernel.log 2>&1; tail -3 ~/build_kernel.log
  if [ -f out/boot.img ]; then cp out/boot.img "$USB/new-boot.img" 2>/dev/null && sync; echo "OK boot.img -> new-boot.img"; else echo "!! kernel build FAILED - see ~/build_kernel.log"; fi
}

case "$1" in
  system)  build_system ;;
  vendor)  build_vendor ;;
  product) build_product ;;
  kernel)  build_kernel ;;
  all)     build_system; build_vendor; build_product; build_kernel ;;
  *) echo "Usage: $0 system | vendor | product | kernel | all" ;;
esac
cd ~
