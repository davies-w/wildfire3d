# Stopping Smokeview from stealing focus on macOS

## Symptom

Launching Smokeview while a full-screen game is running switches Spaces and
pulls the user out of the game.

## Cause

Not the colour bar, not batching, not how it is launched.  Smokeview's GLUT
window creation calls **`SetFrontProcess`** from inside the process:

    smokeview: (LaunchServices) ... CHECKEDIN: ... foreground=0
    smokeview: (HIServices) ... SetFrontProcess: asn=... options=0

`foreground=0` shows the launch itself was already treated as background, and
the call is what overrides that.  Any launch-time mitigation is therefore
useless -- it happens too early to matter.

## Things that do NOT work

- `open -g` (do not bring to foreground) -- Smokeview activates itself anyway
- a bundle with `LSUIElement=true` -- the launch is correctly marked
  `uiElement=1 ... dontMakeFrontmost=1`, and is then overridden by the call
  above.  Verified in the log, not assumed.

## Fix

Interpose `SetFrontProcess` with a no-op via dyld:

    FDS/nofront.c      -> clang -arch x86_64 -arch arm64 -dynamiclib \
                            -o nofront.dylib nofront.c -framework ApplicationServices
    FDS/bin/smv_quiet  -> sets DYLD_INSERT_LIBRARIES, execs the real smokeview

Both architectures are required: the installed Smokeview is x86_64 (Rosetta),
so an arm64-only shim fails to load.

## Verification

Run a render and grep the log -- `SetFrontProcess` and `BringForward` must both
be absent, and the window must report:

    ordered front from a non-active application and may order beneath the
    active application's windows

Confirmed with the game running, twice.

`dyld` prints a load failure if the architecture is wrong; check for that, or a
silently missing shim looks like success.
