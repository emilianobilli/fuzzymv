#ifndef FVM_TYPES_H
#define FVM_TYPES_H

#include <stdint.h>
#include <stddef.h>

/* FVM_INPUT(arr, index, value) -> arr[index] = value */
#define FVM_INPUT(arr, index, value) ((arr)[(index)] = (value))

#ifndef likely
#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#endif

/**
 * Integer types
 */
typedef int32_t  fvm_value_t;
typedef uint16_t fvm_addr_t;
typedef uint16_t fvm_degree_t;

#define FVM_SCALE 10000U
#define FVM_MAX_STACK_DEPTH 32U

/**
 *  Membershipt Function types
 */
typedef enum {
    FVM_MF_LEFT_SHOULDER = 0,
    FVM_MF_TRIANGLE,
    FVM_MF_TRAPEZOID,
    FVM_MF_RIGHT_SHOULDER
} fvm_membership_t;

typedef struct {
    fvm_membership_t type;

    fvm_value_t a;
    fvm_value_t b;
    fvm_value_t c;
    fvm_value_t d;
} fvm_membership_func_t;

typedef enum {
    FVM_OP_PUSH,
    FVM_OP_AND,
    FVM_OP_OR,
    FVM_OP_NOT,
    FVM_OP_SUGENO,
    FVM_OP_END
} fvm_opcode_t;

typedef struct  {
    fvm_opcode_t opcode;
    int32_t      operand;
    uint16_t     output_index;
} fvm_instruction_t;


/** 
 * Set type
 */
typedef struct {
    int input_index;

    fvm_addr_t memory_addr;
    fvm_membership_func_t func;
} fvm_set_t;

typedef struct {
    int sp;
    fvm_degree_t stack[FVM_MAX_STACK_DEPTH];
} fvm_stack_t;


typedef struct {
    fvm_degree_t *memory;
    fvm_stack_t  *stack;
    int64_t *numerator;
    int64_t *denominator;
} fvm_context_t;

typedef struct {
    const fvm_set_t *sets;
    uint16_t set_count;

    const fvm_instruction_t *program;
    uint16_t program_size;

    uint16_t input_count;
    uint16_t output_count;

    uint16_t memory_size;

} fvm_controller_t;

#endif