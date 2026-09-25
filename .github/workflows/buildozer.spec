[app]
title = ANVI Garments
package.name = anvigarments
package.domain = com.sharad.anvigarments
source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,txt,json
source.exclude_exts = spec
source.exclude_dirs = bin,.git,.github,__pycache__,tests,logs,docs,config,data,scripts,output_screenshots
version = 8.9.18
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True
presplash.filename = %(source.dir)s/assets/login_background.png
icon.filename = %(source.dir)s/assets/anvi_garments_logo_new.png

[buildozer]
log_level = 2
warn_on_root = 1
