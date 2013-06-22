#include "common.hpp"
#include "except.hpp"

CSPException::CSPException(const char *m, DWORD code) {
    if (!code)
        code = GetLastError();
    snprintf(msg, 256, "%s (0x%x)", m, code);
}
