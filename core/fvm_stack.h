#ifndef FVM_STACK_H
#define FVM_STACK_H

#include "fvm_types.h"

/**
 * @brief Initialize an FVM stack.
 *
 * @param stack Stack object pointer.
 * @return 0 on success, otherwise -ERROR_CODE.
 */
int fvm_stack_init(fvm_stack_t *stack);


/**
 * @brief Push one value onto the stack.
 *
 * @param stack Stack object pointer.
 * @param x Value to push.
 * @return 0 on success, otherwise -ERROR_CODE.
 */
int fvm_push(fvm_stack_t *stack, fvm_degree_t x);

/**
 * @brief Pop one value from the stack.
 *
 * @param stack Stack object pointer.
 * @param x Output pointer for popped value.
 * @return 0 on success, otherwise -ERROR_CODE.
 */
int fvm_pop(fvm_stack_t *stack, fvm_degree_t *x);

#endif