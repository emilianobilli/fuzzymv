#ifndef FVM_MEMBERSHIP_H
#define FVM_MEMBERSHIP_H

#include "fvm_types.h"

fvm_degree_t fvm_membership_eval(
    const fvm_membership_func_t *mf,
    fvm_value_t x
);

#endif