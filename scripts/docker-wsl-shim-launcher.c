/* Launch the Docker CLI in WSL while preserving the original Docker argv. */

#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <windows.h>

static const wchar_t *skip_executable(const wchar_t *command_line) {
    if (*command_line == L'"') {
        ++command_line;
        while (*command_line != L'\0' && *command_line != L'"') {
            ++command_line;
        }
        if (*command_line == L'"') {
            ++command_line;
        }
    } else {
        while (*command_line != L'\0' && *command_line != L' ' && *command_line != L'\t') {
            ++command_line;
        }
    }
    while (*command_line == L' ' || *command_line == L'\t') {
        ++command_line;
    }
    return command_line;
}

int wmain(void) {
    const wchar_t *distribution = _wgetenv(L"WSL_DOCKER_DISTRIBUTION");
    if (distribution == NULL) {
        fputws(L"WSL Docker shim environment is not configured.\n", stderr);
        return 1;
    }

    const wchar_t *args = skip_executable(GetCommandLineW());
    size_t command_size = wcslen(distribution) + wcslen(args) + 64;
    wchar_t *command = calloc(command_size, sizeof(*command));
    if (command == NULL) {
        fputws(L"Failed to allocate WSL Docker shim command line.\n", stderr);
        return 1;
    }
    swprintf_s(
        command,
        command_size,
        L"wsl.exe -d %s -u root --exec env -u DOCKER_HOST docker %s",
        distribution,
        args
    );

    STARTUPINFOW startup_info = { 0 };
    startup_info.cb = sizeof(startup_info);
    PROCESS_INFORMATION process_info = { 0 };
    if (!CreateProcessW(NULL, command, NULL, NULL, TRUE, 0, NULL, NULL, &startup_info,
                        &process_info)) {
        fwprintf(stderr, L"Failed to start WSL Docker shim: %lu\n", GetLastError());
        free(command);
        return 1;
    }
    free(command);

    WaitForSingleObject(process_info.hProcess, INFINITE);
    DWORD exit_code = 1;
    GetExitCodeProcess(process_info.hProcess, &exit_code);
    CloseHandle(process_info.hThread);
    CloseHandle(process_info.hProcess);
    return (int)exit_code;
}
