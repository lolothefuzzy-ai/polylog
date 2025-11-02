cmake_minimum_required(VERSION 3.16)
project(Polylog6 VERSION 1.0.0 LANGUAGES CXX)

# Project-wide settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Build options
option(POLYLOG_BUILD_TESTS "Build unit and graphics tests" ON)
option(POLYLOG_ENABLE_DETERMINISM "Enable determinism mode by default" ON)
option(POLYLOG_ENABLE_VALIDATION "Enable validation layers" ON)
option(POLYLOG_BUILD_TOOLS "Build tools (shader compiler, asset baker)" ON)

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

# Fetch dependencies
include(FetchContent)

# GLM (header-only math library)
FetchContent_Declare(glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 0.9.9.8
)

# Google Test
FetchContent_Declare(googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.14.0
)

FetchContent_MakeAvailable(glm googletest)

# OpenGL (system package)
find_package(OpenGL REQUIRED)

# Enable testing
if(POLYLOG_BUILD_TESTS)
    enable_testing()
endif()

# Subdirectories
add_subdirectory(core)
add_subdirectory(render)
add_subdirectory(physics)

if(POLYLOG_BUILD_TESTS)
    add_subdirectory(tests)
endif()

if(POLYLOG_BUILD_TOOLS)
    add_subdirectory(tools)
endif()

# Summary
message(STATUS "=== Polylog6 Configuration ===")
message(STATUS "Build tests: ${POLYLOG_BUILD_TESTS}")
message(STATUS "Determinism mode: ${POLYLOG_ENABLE_DETERMINISM}")
message(STATUS "Validation layers: ${POLYLOG_ENABLE_VALIDATION}")
message(STATUS "Build tools: ${POLYLOG_BUILD_TOOLS}")
message(STATUS "Output: ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}")
