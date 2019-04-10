import os.path
import sys

from clang.cindex import CursorKind, Index


def upper_camel_case(s):
    """Turns an UPPER_CASE string into UpperCamelCase.

    :param s: The UPPER_CASE string.
    :returns: The UpperCamelCase string.
    :rtype: string

    """
    return "".join(
        (x[0] + x[1:].lower() if len(x) > 0 else "_") for x in s.split("_"))


class Rust:
    def print_enum_attributes(self):
        print("""
#[cfg_attr(feature = "serialization", derive(Deserialize, Serialize)]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]""")

    def start_enum(self, name):
        self.print_enum_attributes()
        print(f"enum {name} {{")

    def enum_member(self, name, val, brief_comment):
        name = upper_camel_case(name)
        if brief_comment is not None:
            print(f"    /// {brief_comment}\n    {name} = {val},")
        else:
            print(f"    {name} = {val},")

    def end_enum(self):
        print("}")


class Pyx:
    pass


class Pxd:
    pass


ZYDIS_PATH = sys.argv[1]
MODE = {"rust": Rust(), "pyx": Pyx(), "pxd": Pxd()}[sys.argv[2]]

index = Index.create()
tu = index.parse(
    f"{ZYDIS_PATH}/include/Zydis/Zydis.h",
    args=[
        f"-I{ZYDIS_PATH}/include/",
        f"-I{ZYDIS_PATH}",
        f"-I{ZYDIS_PATH}/dependencies/zycore/include",
    ])

for c in tu.cursor.get_children():
    if c.kind == CursorKind.ENUM_DECL:
        if c.displayname[:5] == "Zydis":
            MODE.start_enum(c.displayname[5:-1])
            *children, = [x.displayname for x in c.get_children()]
            skip_prefix = len(os.path.commonprefix(children))

            for x in c.get_children():
                name = x.displayname[skip_prefix:]
                if name[0].isdigit():
                    name = "_" + name
                MODE.enum_member(name, x.enum_value, x.brief_comment)
            MODE.end_enum()
