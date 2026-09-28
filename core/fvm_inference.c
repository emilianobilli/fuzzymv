
#include "fvm_types.h"
#include "fvm_errors.h"
#include "fvm_stack.h"
#include "fvm_mf.h"
#include "fvm_inference.h"

int fvm_eval(
    const fvm_controller_t *controller,
    fvm_context_t *ctx,
    const fvm_value_t *inputs,
    fvm_value_t *outputs
)
{
    int rc;
    int ended = 0;
    uint16_t pc = 0;

    if (unlikely(controller == NULL || controller->sets == NULL ||
        controller->program == NULL))
        return -FVM_EXEC_ERR_NULL_CODE;

    if (unlikely(ctx == NULL || ctx->stack == NULL))
        return -FVM_EXEC_ERR_NULL_CONTEXT;

    if (unlikely(ctx->memory == NULL))
        return -FVM_EXEC_ERR_NULL_MEMORY;

    if (unlikely(ctx->numerator == NULL || ctx->denominator == NULL))
        return -FVM_EXEC_ERR_NULL_MEMORY;

    if (unlikely(inputs == NULL || outputs == NULL))
        return -FVM_EXEC_ERR_NULL_CONTEXT;

    rc = fvm_stack_init(ctx->stack);
    if (unlikely(rc != 0))
        return rc;

    for (uint16_t i = 0; i < controller->output_count; i++) {
        ctx->numerator[i]   = 0;
        ctx->denominator[i] = 0;
    }

    /* 1. Evaluar todos los sets (fuzzificación) */
    for (uint16_t i = 0; i < controller->set_count; i++) {
        const fvm_set_t *set = &controller->sets[i];

        if (unlikely(set->memory_addr >= controller->memory_size))
            return -FVM_EXEC_ERR_BAD_ADDRESS;

        ctx->memory[set->memory_addr] =
            fvm_membership_eval(
                &set->func,
                inputs[set->input_index]
            );
    }

    while (pc < controller->program_size) {

        const fvm_instruction_t *ins =
            &controller->program[pc++];

        switch (ins->opcode) {

            case FVM_OP_PUSH: {
                fvm_addr_t addr = (fvm_addr_t)ins->operand;

                if (unlikely(addr >= controller->memory_size))
                    return -FVM_EXEC_ERR_BAD_ADDRESS;

                rc = fvm_push(ctx->stack, ctx->memory[addr]);
                if (unlikely(rc != 0))
                    return rc;

                break;
            }

            case FVM_OP_AND: {
                fvm_degree_t a, b;

                rc = fvm_pop(ctx->stack, &b);
                if (unlikely(rc != 0))
                    return rc;

                rc = fvm_pop(ctx->stack, &a);
                if (unlikely(rc != 0))
                    return rc;

                rc = fvm_push(ctx->stack, a < b ? a : b);
                if (unlikely(rc != 0))
                    return rc;

                break;
            }

            case FVM_OP_OR: {
                fvm_degree_t a, b;

                rc = fvm_pop(ctx->stack, &b);
                if (unlikely(rc != 0))
                    return rc;

                rc = fvm_pop(ctx->stack, &a);
                if (unlikely(rc != 0))
                    return rc;

                rc = fvm_push(ctx->stack, a > b ? a : b);
                if (unlikely(rc != 0))
                    return rc;

                break;
            }

            case FVM_OP_NOT: {
                fvm_degree_t a;

                rc = fvm_pop(ctx->stack, &a);
                if (unlikely(rc != 0))
                    return rc;

                rc = fvm_push(ctx->stack, FVM_SCALE - a);
                if (unlikely(rc != 0))
                    return rc;

                break;
            }

            case FVM_OP_SUGENO: {
                fvm_degree_t degree;

                if (unlikely(ins->output_index >= controller->output_count))
                    return -FVM_EXEC_ERR_BAD_ADDRESS;

                rc = fvm_pop(ctx->stack, &degree);
                if (unlikely(rc != 0))
                    return rc;

                ctx->numerator[ins->output_index] +=
                    (int64_t)degree * ins->operand;
                ctx->denominator[ins->output_index] += degree;

                break;
            }

            case FVM_OP_END:
                ended = 1;
                goto done;

            default:
                return -FVM_EXEC_ERR_BAD_OPCODE;
        }
    }

done:
    if (unlikely(!ended))
        return -FVM_EXEC_ERR_MISSING_END;

    for (uint16_t o = 0; o < controller->output_count; o++) {
        if (unlikely(ctx->denominator[o] == 0))
            return -FVM_EXEC_ERR_EMPTY_RESULT;

        outputs[o] =
            (fvm_value_t)(ctx->numerator[o] / ctx->denominator[o]);
    }

    return 0;
}