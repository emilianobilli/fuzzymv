from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


FVM_MAX_STACK_DEPTH = 32


@dataclass
class Instruction:
    opcode: str
    operand: int = 0
    output_index: int = 0


class FVMCompileError(Exception):
    pass


class _TokenCursor:
    """Cursor secuencial sobre una lista de tokens, usado por el
    parser recursivo de condiciones (soporta paréntesis y
    precedencia AND/OR)."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek_upper(self) -> str | None:
        token = self.peek()
        return token.upper() if token is not None else None

    def advance(self) -> str:
        token = self.tokens[self.pos]
        self.pos += 1
        return token


class FVMCompiler:
    MEMBERSHIP_TYPES = {
        "left_shoulder": "FVM_MF_LEFT_SHOULDER",
        "triangle": "FVM_MF_TRIANGLE",
        "trapezoid": "FVM_MF_TRAPEZOID",
        "right_shoulder": "FVM_MF_RIGHT_SHOULDER",
    }

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)

        self.config: dict[str, Any] = {}

        self.name: str = ""
        self.inputs: list[dict[str, Any]] = []
        self.outputs: list[dict[str, Any]] = []
        self.rules: list[str] = []

        self.symbols: dict[str, dict[str, Any]] = {}
        self.output_symbols: dict[str, int] = {}

        self.instructions: list[Instruction] = []

        self.memory_size = 0
        self.max_stack_depth = 0

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def compile(self, output_dir: str | Path) -> None:
        self.load()
        self.validate()
        self.build_symbol_table()
        self.build_output_table()
        self.compile_rules()

        if self.max_stack_depth > FVM_MAX_STACK_DEPTH:
            raise FVMCompileError(
                f"Stack depth {self.max_stack_depth} exceeds "
                f"FVM_MAX_STACK_DEPTH={FVM_MAX_STACK_DEPTH}"
            )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        header_path = output_dir / f"{self.name}.h"
        source_path = output_dir / f"{self.name}.c"
        cpp_path = output_dir / f"{self.str_to_camel_case(self.name)}.hpp"

        header_path.write_text(
            self.generate_c_header(),
            encoding="utf-8",
        )

        source_path.write_text(
            self.generate_source(),
            encoding="utf-8",
        )

        cpp_path.write_text(
            self.generate_cpp_header(),
            encoding="utf-8"
        )

        print(f"Generated: {header_path}")
        print(f"Generated: {source_path}")
        print(f"Generated: {cpp_path}")
        print(f"Memory size: {self.memory_size}")
        print(f"Program size: {len(self.instructions)}")
        print(f"Max stack depth: {self.max_stack_depth}")

    # -------------------------------------------------------------------------
    # Loading
    # -------------------------------------------------------------------------

    def load(self) -> None:
        if not self.config_path.exists():
            raise FVMCompileError(
                f"Config file does not exist: {self.config_path}"
            )

        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise FVMCompileError(
                "Top-level YAML structure must be an object"
            )

        self.config = data

        self.name = str(self.config.get("name", "")).strip()
        self.inputs = self.config.get("inputs", [])
        self.outputs = self.config.get("outputs", [])
        self.rules = self.config.get("rules", [])

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate(self) -> None:
        if not self.name:
            raise FVMCompileError("Controller name is required")

        if not self._is_valid_c_identifier(self.name):
            raise FVMCompileError(
                f"Invalid controller name: {self.name}"
            )

        if not isinstance(self.inputs, list) or not self.inputs:
            raise FVMCompileError(
                "At least one input is required"
            )

        if not isinstance(self.outputs, list) or not self.outputs:
            raise FVMCompileError(
                "At least one output is required"
            )

        if not isinstance(self.rules, list) or not self.rules:
            raise FVMCompileError(
                "At least one rule is required"
            )

        self._validate_inputs()
        self._validate_outputs()
        self._validate_rules()

    def _validate_inputs(self) -> None:
        seen_inputs: set[str] = set()

        for input_def in self.inputs:
            if not isinstance(input_def, dict):
                raise FVMCompileError(
                    "Each input must be an object"
                )

            name = str(input_def.get("name", "")).strip()

            if not name:
                raise FVMCompileError(
                    "Input without name"
                )

            if not self._is_valid_c_identifier(name):
                raise FVMCompileError(
                    f"Invalid input name: {name}"
                )

            if name in seen_inputs:
                raise FVMCompileError(
                    f"Duplicated input: {name}"
                )

            seen_inputs.add(name)

            sets = input_def.get("sets")

            if not isinstance(sets, list) or not sets:
                raise FVMCompileError(
                    f"Input '{name}' must contain at least one set"
                )

            seen_sets: set[str] = set()

            for set_def in sets:
                self._validate_set(name, set_def)

                set_name = set_def["name"]

                if set_name in seen_sets:
                    raise FVMCompileError(
                        f"Duplicated set '{set_name}' "
                        f"in input '{name}'"
                    )

                seen_sets.add(set_name)

    def _validate_set(
        self,
        input_name: str,
        set_def: dict[str, Any],
    ) -> None:
        if not isinstance(set_def, dict):
            raise FVMCompileError(
                f"Invalid set definition in input '{input_name}'"
            )

        name = str(set_def.get("name", "")).strip()

        if not name:
            raise FVMCompileError(
                f"Set without name in input '{input_name}'"
            )

        if not self._is_valid_c_identifier(name):
            raise FVMCompileError(
                f"Invalid set name: {input_name}.{name}"
            )

        mf_type = str(set_def.get("type", "")).strip().lower()

        if mf_type not in self.MEMBERSHIP_TYPES:
            raise FVMCompileError(
                f"Unknown membership type '{mf_type}' "
                f"in {input_name}.{name}"
            )

        params = set_def.get("params")

        if not isinstance(params, list):
            raise FVMCompileError(
                f"'params' must be a list in {input_name}.{name}"
            )

        expected = {
            "left_shoulder": 2,
            "right_shoulder": 2,
            "triangle": 3,
            "trapezoid": 4,
        }[mf_type]

        if len(params) != expected:
            raise FVMCompileError(
                f"{input_name}.{name}: "
                f"{mf_type} expects {expected} parameters, "
                f"got {len(params)}"
            )

        for p in params:
            if not isinstance(p, int):
                raise FVMCompileError(
                    f"{input_name}.{name}: "
                    "membership parameters must be integers"
                )

        self._validate_membership_params(
            input_name,
            name,
            mf_type,
            params,
        )

    def _validate_membership_params(
        self,
        input_name: str,
        set_name: str,
        mf_type: str,
        params: list[int],
    ) -> None:
        fullname = f"{input_name}.{set_name}"

        if mf_type in ("left_shoulder", "right_shoulder"):
            a, b = params

            if a >= b:
                raise FVMCompileError(
                    f"{fullname}: expected a < b"
                )

        elif mf_type == "triangle":
            a, b, c = params

            if not (a < b < c):
                raise FVMCompileError(
                    f"{fullname}: expected a < b < c"
                )

        elif mf_type == "trapezoid":
            a, b, c, d = params

            if not (a < b <= c < d):
                raise FVMCompileError(
                    f"{fullname}: expected a < b <= c < d"
                )

    def _validate_outputs(self) -> None:
        seen: set[str] = set()

        for output_def in self.outputs:
            if not isinstance(output_def, dict):
                raise FVMCompileError(
                    "Each output must be an object"
                )

            name = str(output_def.get("name", "")).strip()

            if not name:
                raise FVMCompileError(
                    "Output without name"
                )

            if not self._is_valid_c_identifier(name):
                raise FVMCompileError(
                    f"Invalid output name: {name}"
                )

            if name in seen:
                raise FVMCompileError(
                    f"Duplicated output: {name}"
                )

            seen.add(name)

    def _validate_rules(self) -> None:
        for rule in self.rules:
            if not isinstance(rule, str):
                raise FVMCompileError(
                    "Each rule must be a string"
                )

            if not rule.strip():
                raise FVMCompileError(
                    "Empty rule"
                )

    # -------------------------------------------------------------------------
    # Symbol tables
    # -------------------------------------------------------------------------

    def build_symbol_table(self) -> None:
        self.symbols.clear()

        addr = 0

        for input_index, input_def in enumerate(self.inputs):
            input_name = input_def["name"]

            for set_def in input_def["sets"]:
                set_name = set_def["name"]

                symbol = f"{input_name}.{set_name}"

                self.symbols[symbol] = {
                    "input_index": input_index,
                    "memory_addr": addr,
                    "set": set_def,
                }

                addr += 1

        self.memory_size = addr

        if self.memory_size > 0xFFFF:
            raise FVMCompileError(
                "Controller requires more memory addresses "
                "than fvm_addr_t can represent"
            )

    def build_output_table(self) -> None:
        self.output_symbols.clear()

        for index, output_def in enumerate(self.outputs):
            self.output_symbols[output_def["name"]] = index

    # -------------------------------------------------------------------------
    # Rule compiler
    # -------------------------------------------------------------------------

    def compile_rules(self) -> None:
        self.instructions.clear()
        self.max_stack_depth = 0

        for rule in self.rules:
            self._compile_rule(rule)

        self.instructions.append(
            Instruction(
                opcode="FVM_OP_END",
                operand=0,
                output_index=0,
            )
        )

    def _compile_rule(self, rule: str) -> None:
        tokens = self._tokenize(rule)

        if not tokens:
            raise FVMCompileError(
                f"Empty rule: {rule}"
            )

        if tokens[0].upper() != "IF":
            raise FVMCompileError(
                f"Rule must start with IF: {rule}"
            )

        upper_tokens = [token.upper() for token in tokens]

        try:
            then_index = upper_tokens.index("THEN")
        except ValueError:
            raise FVMCompileError(
                f"Missing THEN in rule: {rule}"
            )

        condition_tokens = tokens[1:then_index]
        output_tokens = tokens[then_index + 1:]

        if not condition_tokens:
            raise FVMCompileError(
                f"Missing condition in rule: {rule}"
            )

        condition_ast = self._parse_condition_expr(
            condition_tokens,
            rule,
        )

        assignments = self._parse_outputs(
            output_tokens,
            rule,
        )

        # Cada salida necesita su propio grado de disparo en el
        # tope de la pila, así que el antecedente se re-emite una
        # vez por cada asignación THEN (no hay instrucción DUP).
        for output_name, output_value in assignments:
            output_index = self._get_output_index(output_name)

            self._emit_condition_node(
                condition_ast,
                0,
                rule,
            )

            self.instructions.append(
                Instruction(
                    opcode="FVM_OP_SUGENO",
                    operand=output_value,
                    output_index=output_index,
                )
            )

    def _tokenize(self, rule: str) -> list[str]:
        # Permit both:
        #
        # THEN output = 100
        #
        # and:
        #
        # THEN output=100
        #
        # Also separate parentheses and commas so grouped
        # conditions and multiple THEN assignments tokenize
        # correctly even without surrounding spaces, e.g.:
        #
        # IF (a IS x OR b IS y) AND c IS z THEN out1=1,out2=2

        rule = rule.replace("=", " = ")
        rule = rule.replace("(", " ( ")
        rule = rule.replace(")", " ) ")
        rule = rule.replace(",", " , ")

        return rule.split()

    def _parse_condition_expr(
        self,
        tokens: list[str],
        original_rule: str,
    ) -> dict[str, Any]:
        cursor = _TokenCursor(tokens)

        node = self._parse_or_expr(cursor, original_rule)

        if cursor.peek() is not None:
            raise FVMCompileError(
                f"Unexpected token '{cursor.peek()}' "
                f"in rule: {original_rule}"
            )

        return node

    def _parse_or_expr(
        self,
        cursor: _TokenCursor,
        original_rule: str,
    ) -> dict[str, Any]:
        node = self._parse_and_expr(cursor, original_rule)

        while cursor.peek_upper() == "OR":
            cursor.advance()
            right = self._parse_and_expr(cursor, original_rule)
            node = {"op": "OR", "left": node, "right": right}

        return node

    def _parse_and_expr(
        self,
        cursor: _TokenCursor,
        original_rule: str,
    ) -> dict[str, Any]:
        node = self._parse_term(cursor, original_rule)

        while cursor.peek_upper() == "AND":
            cursor.advance()
            right = self._parse_term(cursor, original_rule)
            node = {"op": "AND", "left": node, "right": right}

        return node

    def _parse_term(
        self,
        cursor: _TokenCursor,
        original_rule: str,
    ) -> dict[str, Any]:
        if cursor.peek() == "(":
            cursor.advance()

            node = self._parse_or_expr(cursor, original_rule)

            if cursor.peek() != ")":
                raise FVMCompileError(
                    f"Missing closing ')' in rule: {original_rule}"
                )

            cursor.advance()
            return node

        return self._parse_condition_term(cursor, original_rule)

    def _parse_condition_term(
        self,
        cursor: _TokenCursor,
        original_rule: str,
    ) -> dict[str, Any]:
        input_name = cursor.peek()

        if input_name is None or input_name in ("(", ")", ","):
            raise FVMCompileError(
                f"Expected condition in rule: {original_rule}"
            )

        cursor.advance()

        if cursor.peek_upper() != "IS":
            raise FVMCompileError(
                f"Expected IS after '{input_name}' "
                f"in rule: {original_rule}"
            )

        cursor.advance()

        negate = False

        if cursor.peek_upper() == "NOT":
            negate = True
            cursor.advance()

        set_name = cursor.peek()

        if set_name is None or set_name in ("(", ")", ","):
            raise FVMCompileError(
                f"Missing set name in rule: {original_rule}"
            )

        cursor.advance()

        symbol = f"{input_name}.{set_name}"

        if symbol not in self.symbols:
            raise FVMCompileError(
                f"Unknown fuzzy set '{symbol}' "
                f"in rule: {original_rule}"
            )

        return {
            "op": "COND",
            "input": input_name,
            "set": set_name,
            "not": negate,
        }

    def _parse_outputs(
        self,
        tokens: list[str],
        original_rule: str,
    ) -> list[tuple[str, int]]:
        if not tokens:
            raise FVMCompileError(
                f"Expected THEN <output> = <value>: "
                f"{original_rule}"
            )

        groups = self._split_on_comma(tokens, original_rule)

        assignments: list[tuple[str, int]] = []
        seen_outputs: set[str] = set()

        for group in groups:
            if len(group) != 3:
                raise FVMCompileError(
                    f"Expected '<output> = <value>' "
                    f"in rule: {original_rule}"
                )

            output_name, equals, value_token = group

            if equals != "=":
                raise FVMCompileError(
                    f"Expected '=' after output "
                    f"'{output_name}': {original_rule}"
                )

            if output_name not in self.output_symbols:
                raise FVMCompileError(
                    f"Unknown output '{output_name}' "
                    f"in rule: {original_rule}"
                )

            if output_name in seen_outputs:
                raise FVMCompileError(
                    f"Output '{output_name}' assigned more than "
                    f"once in rule: {original_rule}"
                )

            seen_outputs.add(output_name)

            try:
                value = int(value_token)
            except ValueError:
                raise FVMCompileError(
                    f"Sugeno value must be integer: {original_rule}"
                )

            assignments.append((output_name, value))

        return assignments

    @staticmethod
    def _split_on_comma(
        tokens: list[str],
        original_rule: str,
    ) -> list[list[str]]:
        groups: list[list[str]] = [[]]

        for token in tokens:
            if token == ",":
                groups.append([])
            else:
                groups[-1].append(token)

        for group in groups:
            if not group:
                raise FVMCompileError(
                    f"Empty output assignment "
                    f"in rule: {original_rule}"
                )

        return groups

    def _emit_condition_node(
        self,
        node: dict[str, Any],
        base_depth: int,
        original_rule: str,
    ) -> int:
        """Emite instrucciones para un nodo del AST de condiciones.

        `base_depth` es la cantidad de valores que ya están en la
        pila por fuera de este subárbol (p. ej. el operando
        izquierdo de un AND/OR todavía no combinado).

        Devuelve cuántos valores netos deja este subárbol en la
        pila una vez evaluado por completo (siempre 1).
        """
        if node["op"] == "COND":
            symbol = f"{node['input']}.{node['set']}"
            memory_addr = self.symbols[symbol]["memory_addr"]

            self.instructions.append(
                Instruction(
                    opcode="FVM_OP_PUSH",
                    operand=memory_addr,
                )
            )

            self.max_stack_depth = max(
                self.max_stack_depth,
                base_depth + 1,
            )

            if node["not"]:
                self.instructions.append(
                    Instruction(opcode="FVM_OP_NOT")
                )

            return 1

        if node["op"] not in ("AND", "OR"):
            raise FVMCompileError(
                f"Unsupported operator '{node['op']}' "
                f"in rule: {original_rule}"
            )

        left_added = self._emit_condition_node(
            node["left"],
            base_depth,
            original_rule,
        )

        self._emit_condition_node(
            node["right"],
            base_depth + left_added,
            original_rule,
        )

        opcode = "FVM_OP_AND" if node["op"] == "AND" else "FVM_OP_OR"

        self.instructions.append(Instruction(opcode=opcode))

        # El operador binario hace pop de ambos operandos y
        # empuja un único resultado: queda 1 valor neto.
        return 1

    @staticmethod
    def str_to_camel_case(name) -> str:
        s = name.replace("_", " ")
        return "".join(x for x in s.title() if not x.isspace())

    # -------------------------------------------------------------------------
    # C++ Class generation
    # -------------------------------------------------------------------------
    def generate_cpp_header(self) -> str:
        guard = f"{self.name.upper()}_HPP"

        input_comments = "\n".join(
            f"    //   {index}: {input_def['name']}"
            for index, input_def in enumerate(self.inputs)
        )
        output_comments = "\n".join(
            f"    //   {index}: {output_def['name']}"
            for index, output_def in enumerate(self.outputs)
        )

        return f"""\
#ifndef {guard}
#define {guard}

#include <stdexcept>
#include <string>

extern "C" {{
#include "{self.name}.h"
}}

class {self.str_to_camel_case(self.name)} {{
public:
    static constexpr unsigned kInputCount = {self.name.upper()}_INPUT_COUNT;
    static constexpr unsigned kOutputCount = {self.name.upper()}_OUTPUT_COUNT;

    {self.str_to_camel_case(self.name)}() = default;

    // "in" must have kInputCount elements, in this order:
{input_comments}
    // "out" must have kOutputCount elements, in this order:
{output_comments}
    void Evaluate(const fvm_value_t *in, fvm_value_t *out) {{
        int rc = {self.name}_eval(in, out);
        if (rc != 0) {{
            throw std::runtime_error("{self.name}_eval failed with code " +
                                      std::to_string(rc));
        }}
    }}
}};

#endif
"""

    # -------------------------------------------------------------------------
    # C generation
    # -------------------------------------------------------------------------

    def generate_c_header(self) -> str:
        guard = f"{self.name.upper()}_H"

        input_enum = self._generate_input_enum()
        output_enum = self._generate_output_enum()

        return f"""\
#ifndef {guard}
#define {guard}

#include "fvm_types.h"

#define {self.name.upper()}_INPUT_COUNT {len(self.inputs)}U
#define {self.name.upper()}_OUTPUT_COUNT {len(self.outputs)}U
#define {self.name.upper()}_MEMORY_SIZE {self.memory_size}U
#define {self.name.upper()}_PROGRAM_SIZE {len(self.instructions)}U
#define {self.name.upper()}_MAX_STACK_DEPTH {self.max_stack_depth}U

{input_enum}

{output_enum}

int {self.name}_eval(
    const fvm_value_t *inputs,
    fvm_value_t *outputs
);

#endif
"""

    def generate_source(self) -> str:
        sets = self._generate_sets()
        program = self._generate_program()

        return f"""\
#include "{self.name}.h"
#include "fvm.h"

static const fvm_set_t {self.name}_sets[] = {{
{sets}
}};

static const fvm_instruction_t {self.name}_program[] = {{
{program}
}};

static const fvm_controller_t {self.name}_controller = {{
    .sets = {self.name}_sets,
    .set_count = {len(self.symbols)}U,

    .program = {self.name}_program,
    .program_size = {len(self.instructions)}U,

    .input_count = {len(self.inputs)}U,
    .output_count = {len(self.outputs)}U,

    .memory_size = {self.memory_size}U
}};

int {self.name}_eval(
    const fvm_value_t *inputs,
    fvm_value_t *outputs
)
{{
    fvm_degree_t memory[{max(1, self.memory_size)}];

    fvm_stack_t stack;

    fvm_stack_init(&stack);

    int64_t numerator[{max(1, len(self.outputs))}] = {{ 0 }};
    int64_t denominator[{max(1, len(self.outputs))}] = {{ 0 }};

    fvm_context_t ctx = {{
        .memory = memory,
        .stack = &stack,
        .numerator = numerator,
        .denominator = denominator
    }};

    return fvm_eval(
        &{self.name}_controller,
        &ctx,
        inputs,
        outputs
    );
}}
"""

    def _generate_sets(self) -> str:
        lines: list[str] = []

        ordered = sorted(
            self.symbols.values(),
            key=lambda item: item["memory_addr"],
        )

        for info in ordered:
            set_def = info["set"]

            mf_name = str(set_def["type"]).lower()
            mf_type = self.MEMBERSHIP_TYPES[mf_name]

            params = list(set_def["params"])

            while len(params) < 4:
                params.append(0)

            a, b, c, d = params[:4]

            lines.append(
                f"""    {{
        .input_index = {info["input_index"]},
        .memory_addr = {info["memory_addr"]}U,
        .func = {{
            .type = {mf_type},
            .a = {a},
            .b = {b},
            .c = {c},
            .d = {d}
        }}
    }}"""
            )

        return ",\n".join(lines)

    def _generate_program(self) -> str:
        lines: list[str] = []

        for ins in self.instructions:
            lines.append(
                "    { "
                f".opcode = {ins.opcode}, "
                f".operand = {ins.operand}, "
                f".output_index = {ins.output_index}U "
                "}"
            )

        return ",\n".join(lines)

    def _generate_input_enum(self) -> str:
        enum_name = f"{self.name}_input_t"

        entries = []

        for index, input_def in enumerate(self.inputs):
            symbol = (
                f"{self.name.upper()}_INPUT_"
                f"{input_def['name'].upper()}"
            )

            entries.append(
                f"    {symbol} = {index}"
            )

        body = ",\n".join(entries)

        return f"""typedef enum {{
{body}
}} {enum_name};"""

    def _generate_output_enum(self) -> str:
        enum_name = f"{self.name}_output_t"

        entries = []

        for index, output_def in enumerate(self.outputs):
            symbol = (
                f"{self.name.upper()}_OUTPUT_"
                f"{output_def['name'].upper()}"
            )

            entries.append(
                f"    {symbol} = {index}"
            )

        body = ",\n".join(entries)

        return f"""typedef enum {{
{body}
}} {enum_name};"""

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_valid_c_identifier(value: str) -> bool:
        if not value:
            return False

        if not (
            value[0].isalpha()
            or value[0] == "_"
        ):
            return False

        return all(
            char.isalnum() or char == "_"
            for char in value
        )

    def _get_output_index(self, name: str) -> int:
        try:
            return self.output_symbols[name]
        except KeyError:
            raise FVMCompileError(
                f"Unknown output: {name}"
            )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Yaml to C - FVM fuzzy controller compiler"
    )

    parser.add_argument(
        "config",
        help="Controller YAML file"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="./generated",
        help="Output directory"
    )

    args = parser.parse_args()

    compiler = FVMCompiler(args.config)

    try:
        compiler.compile(args.output)
    except FVMCompileError as exc:
        print(f"FVM compile error: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()