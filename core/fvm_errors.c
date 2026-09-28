#include "fvm_errors.h"

const char *const FVM_ERROR_STRINGS[FVM_ERROR_MAX_CODE + 1] = {
    [0]                            = "No error",
    [FVM_STACK_ERR_NULL_STACK]     = "Null stack pointer",
    [FVM_STACK_ERR_NULL_OUTPUT]    = "Null output pointer",
    [FVM_STACK_ERR_OVERFLOW]       = "Stack overflow",
    [FVM_STACK_ERR_UNDERFLOW]      = "Stack underflow",
    [FVM_STACK_ERR_INVALID_STATE]  = "Invalid stack state",
    [FVM_EXEC_ERR_NULL_CONTEXT]    = "Null execution context",
    [FVM_EXEC_ERR_NULL_CODE]       = "Null controller or program",
    [FVM_EXEC_ERR_NULL_MEMORY]     = "Null context memory",
    [FVM_EXEC_ERR_NULL_AND_FN]     = "Null AND function",
    [FVM_EXEC_ERR_NULL_OR_FN]      = "Null OR function",
    [FVM_EXEC_ERR_BAD_OPCODE]      = "Invalid opcode",
    [FVM_EXEC_ERR_BAD_ADDRESS]     = "Memory address out of range",
    [FVM_EXEC_ERR_MISSING_END]     = "Missing END instruction in program",
    [FVM_EXEC_ERR_EMPTY_RESULT]    = "Empty result (zero denominator)"
};
