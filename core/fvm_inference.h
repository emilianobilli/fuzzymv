#ifndef FVM_INFERENCE_H
#define FVM_INFERENCE_H

#include "fvm_types.h"

/**
 * @brief Evaluate a compiled fuzzy controller.
 *
 * @param controller Compiled controller (sets + program).
 * @param ctx Working context (memory, stack and per-output
 *            Sugeno accumulators). Buffers must be sized by
 *            the caller according to controller->memory_size
 *            and controller->output_count.
 * @param inputs Crisp input values (controller->input_count).
 * @param outputs Output buffer (controller->output_count).
 * @return 0 on success, otherwise -ERROR_CODE (see fvm_errors.h).
 */
int fvm_eval(
    const fvm_controller_t *controller,
    fvm_context_t *ctx,
    const fvm_value_t *inputs,
    fvm_value_t *outputs
);

#endif
