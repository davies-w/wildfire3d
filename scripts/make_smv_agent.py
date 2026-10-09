"""Wrap smokeview in a minimal macOS .app bundle that cannot steal focus.

Two mechanisms combine:
  LSUIElement=true  makes the bundle an "agent" app -- no Dock icon, and macOS
                    does not treat launching it as activation
  open -g           tells the launcher not to bring the app to the foreground

Together these should stop a render from switching Spaces and pulling the user
out of a full-screen game.  This script builds the bundle; whether it works is
tested separately.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, shutil, stat

REAL = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
APP = os.path.join(FDS_ROOT, "apps/SmokeviewAgent.app")

shutil.rmtree(APP, ignore_errors=True)
os.makedirs(os.path.join(APP, "Contents", "MacOS"))

plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>smokeview-launch</string>
  <key>CFBundleIdentifier</key><string>local.smv.agent</string>
  <key>CFBundleName</key><string>SmokeviewAgent</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>LSUIElement</key><true/>
  <key>LSBackgroundOnly</key><false/>
</dict>
</plist>
"""
open(os.path.join(APP, "Contents", "Info.plist"), "w").write(plist)

launcher = os.path.join(APP, "Contents", "MacOS", "smokeview-launch")
open(launcher, "w").write('#!/bin/bash\nexec "%s" "$@"\n' % REAL)
os.chmod(launcher, os.stat(launcher).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print("built", APP)
print("plist LSUIElement:", "LSUIElement" in plist)
