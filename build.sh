#!/bin/bash
# system
cd ~/s26fe && rm -f system_new.img && ~/rom85/tools/mkfs.erofs -zlz4hc --mount-point=/system \
  --fs-config-file=sys17/config/system_fs_config --file-contexts=sys17/config/system_file_contexts system_new.img sys17/system
# vendor
rm -f vendor_new.img && ~/rom85/tools/mkfs.erofs -zlz4hc --mount-point=/vendor \
  --fs-config-file=$HOME/cmp/v17_fs_config --file-contexts=$HOME/cmp/v17_merged_fc vendor_new.img ~/cmp/v17
# empty product
mkdir -p ~/emptyprod; printf ' 0 0 0755\n' > ~/emptyprod_fsc; echo '/product(/.*)? u:object_r:system_file:s0' > ~/emptyprod_fc
~/rom85/tools/mkfs.erofs -zlz4hc --mount-point=/product --fs-config-file=$HOME/emptyprod_fsc --file-contexts=$HOME/emptyprod_fc product_empty.img ~/emptyprod
# kernel
cd ~/mint14 && ./build_ultimate.sh
