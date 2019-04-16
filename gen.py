import os
import sys

from clang.cindex import CursorKind, Index


def upper_camel_case(s):
    """Turns an UPPER_CASE string into UpperCamelCase."""
    return "".join(
        (x[0] + x[1:].lower() if len(x) > 0 else "_")
        for x in s.split("_")
    )


class Rust:
    reserved_keywords = ()

    def file_header(self):
        pass

    def start_enum(self, name, full_name, brief_comment):
        print(
            f'/// {brief_comment}\n'
            f'#[cfg_attr(feature = "serialization", derive(Deserialize, Serialize)]\n'
            f'#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n'
            f'#[repr(C)]\n'
            f'enum {name} {{'
        )

    def enum_member(self, name, full_name, val, brief_comment):
        name = upper_camel_case(name)
        if brief_comment is not None:
            print(f"    /// {brief_comment}\n    {name} = {val},")
        else:
            print(f"    {name} = {val},")

    def end_enum(self):
        print("}\n")


class Pyx:
    reserved_keywords = ('IF',)

    def file_header(self):
        print(
            '# THIS FILE IS AUTO-GENERATED USING zydis-bindgen!\n'
            '# distutils: language=3\n'
            '# distutils: include_dirs=ZYDIS_INCLUDES\n\n'
            'from enum import IntEnum\n'
            'from .cenums cimport *\n\n'
        )

    def start_enum(self, name, full_name, brief_comment):
        print(
            f"class {name}(IntEnum):\n"
            f'    """{brief_comment}"""'
        )

    def enum_member(self, name, full_name, val, brief_comment):
        if name == "REQUIRED_BITS":
            return
        if brief_comment:
            print(f"    # {brief_comment}")
        print(f"    {name} = {full_name}")

    def end_enum(self):
        print("\n")


class Pxd:
    reserved_keywords = ()

    def file_header(self):
        print(
            '# THIS FILE IS AUTO-GENERATED USING zydis-bindgen!\n\n'
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


MODES = {"rust": Rust(), "pyx": Pyx(), "pxd": Pxd()}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <zydis path> <{'|'.join(MODES)}>", file=sys.stderr)
        exit(1)

    zydis_path = sys.argv[1]
    mode = MODES[sys.argv[2]]

    tu = Index.create().parse(
        f"{zydis_path}/include/Zydis/Zydis.h",
        args=[
            f"-I./include",
            f"-I{zydis_path}/include/",
            f"-I{zydis_path}",
            f"-I{zydis_path}/dependencies/zycore/include",
        ],
    )

    mode.file_header()

    for c in tu.cursor.get_children():
        if c.kind == CursorKind.ENUM_DECL and c.displayname[:5] == "Zydis":
            mode.start_enum(c.displayname[5:-1], c.displayname, c.brief_comment)
            *children, = [x.displayname for x in c.get_children()]
            skip_prefix = len(os.path.commonprefix(children))

            for x in c.get_children():
                name = x.displayname[skip_prefix:]
                if name[0].isdigit() or name in mode.reserved_keywords:
                    name = "_" + name
                mode.enum_member(name, x.displayname, x.enum_value, x.brief_comment)
            mode.end_enum()
