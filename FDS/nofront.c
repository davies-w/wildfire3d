#include <stdint.h>

typedef struct { uint32_t high; uint32_t low; } ProcessSerialNumber;

extern int SetFrontProcess(const ProcessSerialNumber *psn);
extern int SetFrontProcessWithOptions(const ProcessSerialNumber *psn, uint32_t opts);

static int quiet_SetFrontProcess(const ProcessSerialNumber *psn) { return 0; }
static int quiet_SetFrontProcessWithOptions(const ProcessSerialNumber *psn, uint32_t opts) { return 0; }

#define DYLD_INTERPOSE(_replacement, _replacee)                                \
  __attribute__((used)) static struct {                                        \
    const void *replacement;                                                   \
    const void *replacee;                                                      \
  } _interpose_##_replacee                                                     \
      __attribute__((section("__DATA,__interpose"))) = {                       \
          (const void *)(unsigned long)&_replacement,                          \
          (const void *)(unsigned long)&_replacee};

DYLD_INTERPOSE(quiet_SetFrontProcess, SetFrontProcess)
DYLD_INTERPOSE(quiet_SetFrontProcessWithOptions, SetFrontProcessWithOptions)
