#!/usr/bin/env python
"""把打补丁后的 H5 写回 APK 副本 (不改其它条目)

h2u: python repack.py <原APK> <输出APK>
之后必须重新对齐并签名，否则无法安装：
  zipalign -p -f 4 out.apk out-aligned.apk
  apksigner sign --ks <your.jks> --out out-signed.apk out-aligned.apk
（改了签名等于换包，需先卸载原应用，本地数据会丢失）
"""
import shutil, sys, zipfile

ENTRY = 'assets/h5hybrid/assets/index-cc95ce0f.js'
PATCH = 'index-cc95ce0f.js'

src, dst = sys.argv[1], sys.argv[2]
patched = open(PATCH, 'rb').read()
shutil.copyfile(src, dst)

# zipfile 无法原地替换条目：重建
with zipfile.ZipFile(src, 'r') as zi, zipfile.ZipFile(dst, 'w') as zo:
    for item in zi.infolist():
        data = patched if item.filename == ENTRY else zi.read(item.filename)
        ni = zipfile.ZipInfo(item.filename, date_time=item.date_time)
        ni.compress_type = item.compress_type
        ni.external_attr = item.external_attr
        zo.writestr(ni, data)
print('written', dst)
print('entry replaced:', ENTRY, len(patched), 'bytes')
