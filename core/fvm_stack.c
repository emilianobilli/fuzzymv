#include "fvm_types.h"
#include "fvm_errors.h"

/**
 * @brief Initialize an FVM stack.
 *
 * @param stack Stack object pointer.
 * @return 0 on success, otherwise -ERROR_CODE.
 */
int fvm_stack_init(fvm_stack_t *stack) {
    if (stack == NULL)
        return -FVM_STACK_ERR_NULL_STACK;

    stack->sp = -1;
    return 0;
}

/**
 * @brief Push one value onto the stack.
 *
 * @param stack Stack object pointer.
 * @param x Value to push.
 * @return 0 on success, otherwise -ERROR_CODE.
 */
int fvm_push(fvm_stack_t *stack, fvm_degree_t x) {
    if (unlikely(stack == NULL))
        return -FVM_STACK_ERR_NULL_STACK;
        
    if (unlikely(stack->sp < -1))
        return -FVM_STACK_ERR_INVALID_STATE;
        
    if (unlikely(stack->sp >= (int)FVM_MAX_STACK_DEPTH - 1))
        return -FVM_STACK_ERR_OVERFLOW;

    stack->stack[++(stack->sp)] = x;
    return 0;
}

/**
 * @brief Pop one value from the stack.
 *
 * @param stack Stack object pointer.
 * @param x Output pointer for popped value.
 * @return 0 on success, otherwise -ERROR_CODE.
 */
int fvm_pop(fvm_stack_t *stack, fvm_degree_t *x) {
    if (unlikely(stack == NULL))
        return -FVM_STACK_ERR_NULL_STACK;
        
    if (unlikely(x == NULL))
        return -FVM_STACK_ERR_NULL_OUTPUT;
        
    if (unlikely(stack->sp >= (int)FVM_MAX_STACK_DEPTH))
        return -FVM_STACK_ERR_INVALID_STATE;
        
    if (unlikely(stack->sp < 0))
        return -FVM_STACK_ERR_UNDERFLOW;

    *x = stack->stack[stack->sp--];
    return 0;
}