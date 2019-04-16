zydis-bindgen
=============

Auto-generate Zydis enums (and possibly later also structs) for various language
bindings. The information is extracted from the C headers using `libclang`.

## Preparation

#### Arch Linux & Manjaro
```sudo pacman -S clang```

#### macOS (MacPorts)
```sudo port install clang-7.0 py37-clang +clang70```

## Usage

```
git clone https://github.com/zyantific/zydis.git
git clone https://github.com/zyantific/zydis-bindgen.git
cd zydis-bindgen
python3 ./gen.py ../zydis rust
```