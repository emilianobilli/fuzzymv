#ifndef FVM_ERRORS
#define FVM_ERRORS

enum {
    FVM_STACK_ERR_NULL_STACK    = 1,
    FVM_STACK_ERR_NULL_OUTPUT   = 2,
    FVM_STACK_ERR_OVERFLOW      = 3,
    FVM_STACK_ERR_UNDERFLOW     = 4,
    FVM_STACK_ERR_INVALID_STATE = 5,
    FVM_EXEC_ERR_NULL_CONTEXT   = 6,
    FVM_EXEC_ERR_NULL_CODE      = 7,
    FVM_EXEC_ERR_NULL_MEMORY    = 8,
    FVM_EXEC_ERR_NULL_AND_FN    = 9,
    FVM_EXEC_ERR_NULL_OR_FN     = 10,
    FVM_EXEC_ERR_BAD_OPCODE     = 11,
    FVM_EXEC_ERR_BAD_ADDRESS    = 12,
    FVM_EXEC_ERR_MISSING_END    = 13,
    FVM_EXEC_ERR_EMPTY_RESULT   = 14
};

#define FVM_ERROR_MAX_CODE FVM_EXEC_ERR_EMPTY_RESULT

extern const char *const FVM_ERROR_STRINGS[FVM_ERROR_MAX_CODE + 1];

/**
 * @brief Translate an fvm_eval() return code into a human-readable string.
 *
 * Accepts both the raw error code and the negated code returned by
 * fvm_eval() (0 on success, -ERROR_CODE on failure).
 *
 * @param rc Return code from fvm_eval() or a generated *_eval() function.
 * @return Static string, never NULL (falls back to "Unknown error code").
 */
const char *fvm_error_string(int rc);

#endif