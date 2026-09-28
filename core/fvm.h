#ifndef FVM_H
#define FVM_H

/**
 * Umbrella header for the FVM (Fuzzy Virtual Machine) core.
 * Generated controllers (see compiler.py) include this single
 * header to get access to every type and function they need:
 * types, error codes, stack primitives, membership functions
 * and the inference entry point (fvm_eval).
 */

#include "fvm_types.h"
#include "fvm_errors.h"
#include "fvm_stack.h"
#include "fvm_mf.h"
#include "fvm_inference.h"

#endif
