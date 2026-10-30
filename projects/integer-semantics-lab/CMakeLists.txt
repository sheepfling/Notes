cmake_minimum_required(VERSION 3.25)

project(integer_semantics_lab VERSION 1.0.0 LANGUAGES CXX)

option(INTEGER_SEMANTICS_BUILD_TESTS "Build the portable C++ tests" ON)
option(INTEGER_SEMANTICS_BUILD_UB_LAB "Build the intentionally undefined-behavior specimens" OFF)

add_library(integer_semantics_options INTERFACE)
target_compile_features(integer_semantics_options INTERFACE cxx_std_23)
target_include_directories(
    integer_semantics_options
    INTERFACE
        "${CMAKE_CURRENT_SOURCE_DIR}/cpp/include"
)

if(MSVC)
    target_compile_options(integer_semantics_options INTERFACE /W4 /permissive-)
else()
    target_compile_options(
        integer_semantics_options
        INTERFACE
            -Wall
            -Wextra
            -Wpedantic
            -Wconversion
            -Wsign-conversion
    )
endif()

add_executable(cpp_integer_semantics cpp/src/main.cpp)
target_link_libraries(cpp_integer_semantics PRIVATE integer_semantics_options)

include(CTest)
if(BUILD_TESTING AND INTEGER_SEMANTICS_BUILD_TESTS)
    add_executable(cpp_integer_semantics_tests cpp/tests/probe_tests.cpp)
    target_link_libraries(cpp_integer_semantics_tests PRIVATE integer_semantics_options)
    add_test(NAME cpp_integer_semantics_tests COMMAND cpp_integer_semantics_tests)
endif()

if(INTEGER_SEMANTICS_BUILD_UB_LAB)
    add_executable(cpp_integer_ub_lab cpp/ub_lab/signed_overflow.cpp)
    target_compile_features(cpp_integer_ub_lab PRIVATE cxx_std_23)
    if(MSVC)
        target_compile_options(cpp_integer_ub_lab PRIVATE /W4)
    else()
        target_compile_options(cpp_integer_ub_lab PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif()
