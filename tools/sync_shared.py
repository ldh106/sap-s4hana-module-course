#!/usr/bin/env python3
"""shared/ 의 공통 파일을 각 앱 webapp/ 으로 복사한다. (각 앱은 따로 실행되므로 파일을 각자 가지고 있어야 함)

실행: python3 tools/sync_shared.py   (레포 루트에서)
"""
import os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = ['so-json', 'so-odata', 'bp', 'je']
for app in APPS:
    dst = os.path.join(ROOT, 'apps', app, 'webapp', 'ext')
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'shared', 'ext', 'Inspector.js'), dst)
    print(f'shared/ext/Inspector.js -> apps/{app}/webapp/ext/')
