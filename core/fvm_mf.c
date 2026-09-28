#include "fvm_mf.h"

static inline fvm_degree_t fvm_left_shoulder(
    fvm_value_t x, fvm_value_t a, fvm_value_t b)
{
    if (x <= a) return FVM_SCALE;
    if (x >= b) return 0;

    fvm_value_t den = b - a;
    if (likely(den != 0)) {
        return (fvm_degree_t)(((int64_t)(b - x) * FVM_SCALE) / den);
    }
    return 0;
}

static inline fvm_degree_t fvm_right_shoulder(
    fvm_value_t x, fvm_value_t a, fvm_value_t b)
{
    if (x <= a) return 0;
    if (x >= b) return FVM_SCALE;

    fvm_value_t den = b - a;
    if (likely(den != 0)) {
        return (fvm_degree_t)(((int64_t)(x - a) * FVM_SCALE) / den);
    }
    return 0;
}

static inline fvm_degree_t fvm_triangle(
    fvm_value_t x, fvm_value_t a, fvm_value_t b, fvm_value_t c)
{
    if (x == b) return FVM_SCALE;

    if (x <= a || x >= c) return 0;

    if (x < b) {
        fvm_value_t den = b - a;
        if (likely(den != 0)) {
            return (fvm_degree_t)(((int64_t)(x - a) * FVM_SCALE) / den);
        }
    }

    fvm_value_t den = c - b;
    if (likely(den != 0)) {
        return (fvm_degree_t)(((int64_t)(c - x) * FVM_SCALE) / den);
    }
    return 0;
}

static inline fvm_degree_t fvm_trapezoid(
    fvm_value_t x, fvm_value_t a, fvm_value_t b, fvm_value_t c, fvm_value_t d)
{
    if (x >= b && x <= c) return FVM_SCALE;

    if (x <= a || x >= d) return 0;

    if (x < b) {
        fvm_value_t den = b - a;
        if (likely(den != 0)) {
            return (fvm_degree_t)(((int64_t)(x - a) * FVM_SCALE) / den);
        }
    }

    fvm_value_t den = d - c;
    if (likely(den != 0)) {
        return (fvm_degree_t)(((int64_t)(d - x) * FVM_SCALE) / den);
    }
    return 0;
}

fvm_degree_t fvm_membership_eval(
    const fvm_membership_func_t *mf, fvm_value_t x)
{
    switch (mf->type) {
        case FVM_MF_LEFT_SHOULDER:
            return fvm_left_shoulder(x, mf->a, mf->b);

        case FVM_MF_TRIANGLE:
            return fvm_triangle(x, mf->a, mf->b, mf->c);

        case FVM_MF_TRAPEZOID:
            return fvm_trapezoid(x, mf->a, mf->b, mf->c, mf->d);

        case FVM_MF_RIGHT_SHOULDER:
            return fvm_right_shoulder(x, mf->a, mf->b);

        default:
            return 0;
    }
}