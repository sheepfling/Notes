# Diagnose CMake dependency and package-discovery problems

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

When CMake cannot find a dependency, first determine whether the package is missing, installed
under an unexpected prefix, or being consumed through the wrong package interface. Keep each
platform’s build directory separate and use an out-of-source configure.

## Start from a known configure

Use a fresh build directory and pass the source and build locations explicitly:

```bash
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_PREFIX_PATH=/path/to/dependency/prefix
```

On Windows with a multi-configuration generator, select the configuration at build time rather
than relying on `CMAKE_BUILD_TYPE`:

```powershell
cmake -S . -B build -DCMAKE_PREFIX_PATH='C:\path\to\dependency\prefix'
cmake --build build --config Debug --verbose
```

Do not mix a Linux build directory with a Visual Studio or MinGW build directory. If a configure
has cached the wrong compiler or package location, use a new build directory or remove only that
build directory after confirming it contains no source files.

## Turn on the right diagnostics

For package search problems, enable CMake’s find debugging:

```bash
cmake -S . -B build -DCMAKE_FIND_DEBUG_MODE=ON
```

The command-line debug switches are useful when tracing a particular configure:

```bash
cmake --debug-find -S . -B build
cmake --trace-source=CMakeLists.txt --trace-expand -S . -B build
```

Use the narrowest trace that answers the question. Full traces can be very large and may expose
local paths in logs, so keep them in ignored output directories when they are not needed as notes.

## Prefer imported targets

Modern package configurations generally provide imported targets that carry include directories,
compile definitions, and transitive libraries:

```cmake
find_package(Eigen3 CONFIG REQUIRED NO_MODULE)

add_executable(example main.cpp)
target_link_libraries(example PRIVATE Eigen3::Eigen)
```

The target name is package-specific; check the package’s config file or documentation. Avoid
reconstructing include and library flags manually when an imported target is available.

If a legacy package exposes variables instead, inspect them deliberately and keep compatibility
logic local to the package integration:

```cmake
find_package(SomeLibrary CONFIG REQUIRED)
message(STATUS "SomeLibrary_DIR=${SomeLibrary_DIR}")
message(STATUS "SomeLibrary_INCLUDE_DIRS=${SomeLibrary_INCLUDE_DIRS}")
```

Do not invent legacy variables such as `*_FOUND` or `*_ROOT_DIR` merely to silence a configure
error. They can make a broken package appear usable while leaving link failures for later.

## Print the cache and variable context

For a short diagnostic snapshot, inspect the cache and selected variables:

```bash
cmake -LAH -N build
```

For a temporary in-project diagnostic, this CMake fragment lists variables known to the current
configure:

```cmake
get_cmake_property(_variable_names VARIABLES)
foreach (_variable_name IN LISTS _variable_names)
  message(STATUS "${_variable_name}=${${_variable_name}}")
endforeach()
```

Remove or guard the fragment after diagnosing the issue; it can make logs noisy and reveal local
paths.

## Verify the complete build

Configure, build, and run the smallest relevant test target:

```bash
cmake --build build --verbose
ctest --test-dir build --output-on-failure
```

A successful configure proves only that CMake generated build files. A successful compile proves
that headers and link inputs were usable; tests are still needed to validate runtime behavior.
