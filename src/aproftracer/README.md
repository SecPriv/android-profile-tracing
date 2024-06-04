# aproftracer

## EBPF based tracer for profiles on Android

### Table of Contents

- [Installation](#installation)
- [Development](#development)
- [License](#license)

## Installation

```console
pip install .
```

it depends on a binary compatible with the target Android (Emulator) architecture that implements these arguments:

```txt
Usage: tracer.bin APKID OATFILE OFFSETSCSV OUTPUT

Arguments:
    APKID       the package/app id to trace
    OATFILE     the oat/odex file containing AOT compiled code
    OFFSETCSV   the csv containing the offsets of methods to trace in the oat file. note they are the EXECUTABLE_OFFSET + CODE_OFFSET in oatdump
    OUTPUT      the output file to save the trace
```

## Development

```console
pip install -e .[development]
```

Run `nox` for linting and tests.

## License

`aproftracer` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
