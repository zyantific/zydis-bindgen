import os
import sys

from clang.cindex import CursorKind, Index

def underscoreify(s):
    """Turns a string like "FooBarBaz" into "foo_bar_baz"."""
    res = ""
    # Avoid turning CPU into c_p_u
    last_was_upper = False
    for i, c in enumerate(s):
        if i != 0 and c.isupper() and not last_was_upper:
            res += "_"
        res += c.lower()
        last_was_upper = c.isupper()
    return res


class Rust:
    reserved_keywords = ()
    bitflags = ["ZydisOperandAction_"]

    def file_header(self):
        print("""// AUTO-GENERATED USING zydis-bindgen!

#[cfg(feature = "serialization")]
use serde::{Deserialize, Serialize};
""")

    def start_enum(self, name, full_name, brief_comment):
        self.closed = False

        if name == "FormatterProperty":
            print(
                f"""/// We wrap this in a nicer rust enum `FormatterProperty` already,
/// use that instead.
#[cfg_attr(feature = "serialization", derive(Deserialize, Serialize))]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub enum {full_name[:-1]} {{"""
            )
            self.enum_name = full_name[:-1]
        else:
            print(
                f"/// {brief_comment}\n"
                f'#[cfg_attr(feature = "serialization", derive(Deserialize, Serialize))]\n'
                f"#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash)]\n"
                f"#[repr(C)]\n"
                f"pub enum {name} {{"
            )
            self.enum_name = name

    def enum_member(self, name, full_name, val, brief_comment):
        if name == "REQUIRED_BITS":
            return
        elif name == "MAX_VALUE":
            # Work around that we can't use negative values in unsigned constants.
            if self.enum_name == "Padding":
                return
            self.closed = True
            print(f"}}\n\npub const {full_name[6:]}: usize = {val};\n")
            return

        if brief_comment is not None:
            print(f"    /// {brief_comment}\n    {name} = {val},")
        else:
            print(f"    {name} = {val},")

    def end_enum(self):
        if not self.closed:
            print("}\n")


class Py:
    reserved_keywords = ("IF",)
    bitflags = []

    def file_header(self):
        print(
            "# THIS FILE IS AUTO-GENERATED USING zydis-bindgen!\n"
            "# distutils: include_dirs=ZYDIS_INCLUDES\n\n"
            "from enum import IntEnum\n"
        )

    def start_enum(self, name, full_name, brief_comment):
        print(f'class {name}(IntEnum):\n    """{brief_comment}"""')

    def enum_member(self, name, full_name, val, brief_comment):
        if name == "REQUIRED_BITS":
            return
        if brief_comment:
            print(f"    # {brief_comment}")
        print(f"    {name} = {val}")

    def end_enum(self):
        print("\n")


class Pxd:
    reserved_keywords = ()
    bitflags = []

    def file_header(self):
        print(
            "# THIS FILE IS AUTO-GENERATED USING zydis-bindgen!\n\n"
            'cdef extern from "Zydis/Zydis.h":'
        )

    def start_enum(self, name, full_name, brief_comment):
        print(f"    ctypedef enum {full_name[:-1]}:")

    def enum_member(self, name, full_name, val, brief_comment):
        if name == "REQUIRED_BITS":
            return
        print(f"        {full_name}")

    def end_enum(self):
        print()


class CSharp:
    reserved_keywords = ()
    bitflags = []

    def file_header(self):
        print("// THIS FILE IS AUTO-GENERATED USING zydis-bindgen!\n")

    def start_enum(self, name, full_name, brief_comment):
        print(f'/// <summary>{brief_comment}</summary>')
        print(f'public enum {name}\n{{')

    def enum_member(self, name, full_name, val, brief_comment):
        if name == "REQUIRED_BITS":
            return
        if brief_comment:
            print(f"    /// <summary>{brief_comment}</summary>")
        print(f"    {name} = {val},")

    def end_enum(self):
        print("}\n")


class Ocaml:
    reserved_keywords = ()
    bitflags = ["ZydisOperandAction_"]

    def __init__(self):
        self.current_name = None

    def file_header(self):
        print("(* THIS FILE IS AUTO-GENERATED USING zydis-bindgen! *)\n")

    def start_enum(self, name, full_name, brief_comment):
        self.current_name = name
        self.i = 0
        print(f"type {underscoreify(name)} =")

    def enum_member(self, name, full_name, val, brief_comment):
        if self.i == 0 and name == "NONE":
            self.i += 1
            return

        if name == "REQUIRED_BITS" or name == "MAX_VALUE":
            return
        if name[0] == "_":
            name = self.current_name + name[1:]
        print(f"  | {name}")
        self.i += 1

    def end_enum(self):
        print()


MODES = {
    "rust": Rust(),
    "py": Py(),
    "pxd": Pxd(),
    "csharp": CSharp(),
    "ocaml": Ocaml(),
}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <zydis path> <{'|'.join(MODES)}>", file=sys.stderr)
        exit(1)

    zydis_path = sys.argv[1]
    mode = MODES[sys.argv[2]]

    tu = Index.create().parse(
        f"{zydis_path}/include/Zydis/Zydis.h",
        args=[
            "-DZYAN_NO_LIBC=1",
            "-I./include",
            f"-I{zydis_path}/include/",
            f"-I{zydis_path}",
            f"-I{zydis_path}/dependencies/zycore/include",
        ],
    )

    for error in tu.diagnostics:
        print(f"Err: {error!s}", file=sys.stderr)

    mode.file_header()

    for c in tu.cursor.get_children():
        if c.kind == CursorKind.ENUM_DECL and c.displayname[:5] == "Zydis" and c.displayname not in mode.bitflags:
            mode.start_enum(c.displayname[5:-1], c.displayname, c.brief_comment)
            *children, = [x.displayname for x in c.get_children()]
            skip_prefix = len(os.path.commonprefix(children))

            for x in c.get_children():
                name = x.displayname[skip_prefix:]
                if name[0].isdigit() or name in mode.reserved_keywords:
                    name = "_" + name
                mode.enum_member(name, x.displayname, x.enum_value, x.brief_comment)
            mode.end_enum()
