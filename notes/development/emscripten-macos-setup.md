# Set up Emscripten on macOS

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

## Purpose

Install the officially supported Emscripten SDK (`emsdk`) on macOS, activate it for a shell, verify the toolchain, and compile a small C++ program for the browser or Node.js.

The commands below use `$HOME/bin/emsdk` as the SDK location. `$HOME` keeps the instructions independent of the local macOS username.

## Prerequisites

Install or confirm:

- macOS 10.14 (Mojave) or newer
- Xcode Command Line Tools
- Git
- CMake, if the project or its build system needs it

Install the Command Line Tools if necessary:

```zsh
xcode-select --install
```

Check the basic tools:

```zsh
git --version
python3 --version
cmake --version
```

The SDK includes its own Python. A system Python is still useful for surrounding project tools.

## Install the SDK

Clone the SDK manager into the chosen location:

```zsh
mkdir -p "$HOME/bin"
git clone https://github.com/emscripten-core/emsdk.git "$HOME/bin/emsdk"
cd "$HOME/bin/emsdk"
```

Install and activate the latest tagged release:

```zsh
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
```

source changes only the current terminal. Run it again in each new shell unless a startup helper is configured.

## Optional zsh helper

Add a small function to ~/.zshrc:

```zsh
emsdk-activate() {
    source "$HOME/bin/emsdk/emsdk_env.sh"
}
```

Reload the shell configuration and activate the environment:

```zsh
source ~/.zshrc
emsdk-activate
```

Keep this helper only if the SDK remains at `$HOME/bin/emsdk`.

## Verify the installation

From the SDK directory, run the official sanity check:

```zsh
cd "$HOME/bin/emsdk"
./emcc --check
```

After the environment is sourced, `emcc --check` should complete without warnings about missing or mismatched components.

Check the compiler version:

```zsh
emcc --version
em++ --version
```

## Compile a minimal C++ example

Create hello.cpp in a separate working directory:

```cpp
#include <iostream>

int main() {
    std::cout << "Hello from WebAssembly!\n";
    return 0;
}
```

Compile a browser-targeted HTML launcher:

```zsh
em++ hello.cpp -O2 -o hello.html
```

This produces the HTML launcher and the JavaScript/WebAssembly files it loads. Serve the directory over HTTP rather than opening the HTML file directly:

```zsh
python3 -m http.server 8000
```

Then open http://localhost:8000/hello.html in a browser.

For a Node.js-oriented output, compile JavaScript instead:

```zsh
em++ hello.cpp -O2 -o hello.js
node hello.js
```

Use the target that matches the runtime. Browser output may rely on DOM or Web APIs; Node output does not provide those browser APIs.

## Update the SDK

The initial clone may be refreshed with git pull; the official installation instructions use that command. For routine SDK maintenance, update the available tool registry, then install and activate the desired target:

```zsh
cd "$HOME/bin/emsdk"
./emsdk update
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
```

If a recently published tag is missing, refresh the tag list:

```zsh
./emsdk update-tags
```

## Switch to a specific version

List available targets:

```zsh
./emsdk list
```

Install and activate a specific tagged release:

```zsh
./emsdk install <version>
./emsdk activate <version>
source ./emsdk_env.sh
```

Replace `<version>` with the exact target shown by `./emsdk list`. `latest` means the newest tagged release, so it is convenient but not reproducible.

## Reproducible project setup

For a project that must keep using the same toolchain:

1. Record the exact Emscripten version in the project’s build documentation or configuration.
2. Install and activate that version rather than latest.
3. Record the `emsdk` repository revision when the toolchain is established:

   ```zsh
   git -C "$HOME/bin/emsdk" rev-parse HEAD
   ```

4. Run `emcc --version` in CI or setup diagnostics and keep the output with the build record.

The SDK directory itself should generally remain outside the project repository.

## Troubleshooting

### `emcc` is not found

The current shell has not loaded the SDK environment, or the helper points to the wrong location:

```zsh
source "$HOME/bin/emsdk/emsdk_env.sh"
command -v emcc
```

### emcc --check reports missing or mismatched tools

Run the check from the SDK directory, confirm the intended target is active, and reinstall or activate it:

```zsh
cd "$HOME/bin/emsdk"
./emsdk list
./emsdk install <version>
./emsdk activate <version>
source ./emsdk_env.sh
./emcc --check
```

If the SDK cache appears inconsistent, the compiler can clear its cache:

```zsh
emcc --clear-cache
```

### The browser example does not run

- Serve the directory with HTTP; do not rely on file://.
- Check the browser developer console.
- Confirm that the generated .js and .wasm files are beside the HTML file.
- Use a browser-targeted .html build rather than the Node.js .js build.

### Build-system integration fails

Activate the SDK in the same shell that invokes CMake or the project build:

```zsh
source "$HOME/bin/emsdk/emsdk_env.sh"
emcmake cmake -S . -B build
cmake --build build
```

The project may also require its own documented CMake version or Emscripten-specific options.

## Uninstall

Remove the SDK directory after closing shells or scripts that use it:

```zsh
rm -rf "$HOME/bin/emsdk"
```

Before deleting it, remove or update any emsdk-activate helper in ~/.zshrc. If emsdk activate created a user-level .emscripten configuration, inspect it before removing it; another Emscripten installation may depend on it.

## References

- Emscripten: Download and install — https://emscripten.org/docs/getting_started/downloads.html
- Emscripten: Verify the development environment — https://emscripten.org/docs/building_from_source/verify_emscripten_environment.html
