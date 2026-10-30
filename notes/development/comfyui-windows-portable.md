# ComfyUI Portable on Windows

> Type: how-to  
> Status: historical  
> Updated: 2026-08-01

This is a durable snapshot of an older ComfyUI setup note, focused on the standalone Windows
package. It deliberately omits personal paths, model binaries, copied tutorial transcripts, and
unstable third-party video links. It is a memory aid, not a promise that today's package layout,
launcher flags, Python version, or custom-node APIs are unchanged.

The [official portable Windows guide](https://docs.comfy.org/installation/comfyui_portable_windows)
is the place to check current downloads and hardware-specific packages when this note is revisited.
The historical package contained an embedded Python environment, so it could be extracted and run
without first creating a separate Python environment.

## Install and launch

1. Choose the current portable package matching the GPU or CPU mode from the official guide.
2. Extract it with a trusted archive tool into a short, writable directory such as
   `<install-root>\ComfyUI_windows_portable`. Avoid a deeply nested path while troubleshooting.
3. Confirm the extracted layout includes:

   ```text
   ComfyUI_windows_portable\
   ├── ComfyUI\
   ├── python_embeded\
   ├── update\
   ├── README_VERY_IMPORTANT.txt
   ├── run_cpu.bat
   └── run_nvidia_gpu.bat
   ```

4. Run `run_nvidia_gpu.bat` for a supported NVIDIA setup or `run_cpu.bat` for CPU mode. Use the
   corresponding AMD/Intel launcher if the downloaded package provides one.
5. Keep the command window open. The local interface normally listens at
   `http://127.0.0.1:8188`; opening the window is also the quickest way to see startup errors.

Do not commit the portable package, embedded Python environment, model weights, or generated
images to this notes repository.

## Model locations

The default model folders are under `ComfyUI\models`. Keep large model collections outside the
installation when multiple instances need to share them. Copy
`ComfyUI\extra_model_paths.yaml.example` to `ComfyUI\extra_model_paths.yaml`, then edit the copy.
The [upstream example configuration](https://github.com/Comfy-Org/ComfyUI/blob/master/extra_model_paths.yaml.example)
lists the supported model categories and current naming conventions.

A minimal shared-model configuration looks like this:

```yaml
shared_models:
  base_path: <models-root>
  checkpoints: models/checkpoints
  configs: models/configs
  loras: models/loras
  vae: models/vae
  text_encoders: |
    models/text_encoders
    models/clip
  diffusion_models: |
    models/diffusion_models
    models/unet
  clip_vision: models/clip_vision
  controlnet: models/controlnet
  upscale_models: models/upscale_models
```

Use forward slashes or quoted Windows paths when a path contains spaces. Back up the YAML before
editing and restart ComfyUI after changing it. If a node cannot find a model, check the category,
the filename, and the startup log before downloading another copy.

## External custom nodes

An additional custom-node path can be declared separately:

```yaml
shared_nodes:
  custom_nodes: <custom-nodes-root>
```

This adds a search path; it does not move the default `ComfyUI\custom_nodes` directory. Each
custom node may have its own dependencies. Install them with the embedded interpreter from the
portable root, not with an unrelated system Python:

```powershell
.\python_embeded\python.exe -m pip install -r .\ComfyUI\custom_nodes\<node>\requirements.txt
```

Inspect a node's files before running its install script. Third-party nodes execute code and may
change the embedded environment. Restart ComfyUI after installing dependencies.

## Updating

The `update` directory contains the portable updater scripts. Back up workflows and
`extra_model_paths.yaml` first, then choose the stable update script unless you intentionally need
the latest commit. Use the script that updates Python dependencies only when a dependency problem
requires it; changing the runtime can break older custom nodes.

Read the package's `README_VERY_IMPORTANT.txt` and the [ComfyUI repository instructions](https://github.com/Comfy-Org/ComfyUI/blob/master/README.md)
before updating an older installation. Test one workflow after each update, and retain the last
known-good package until the new one is confirmed. Treat the exact update filenames above as
historical examples, not a current package contract.

## ComfyUI-Manager

ComfyUI-Manager is a third-party extension for finding and maintaining custom nodes. Its install
procedure changes, so use the current [ComfyUI-Manager repository](https://github.com/Comfy-Org/ComfyUI-Manager)
instructions rather than copying an old batch file or clone command from this note. Install its
dependencies into the same embedded Python environment and review what it will install.

## LAN access

The default loopback binding is safer for a single machine. If another device genuinely needs
access, add `--listen` to the launcher command, for example:

```bat
.\python_embeded\python.exe -s ComfyUI\main.py --listen --windows-standalone-build
pause
```

This changes the exposure from local-only to the host's network interfaces. Before enabling it,
restrict the Windows Firewall rule to the intended private network, avoid forwarding the port to
the Internet, and understand whether the selected ComfyUI build provides authentication. Use a
placeholder such as `http://<local-host>:8188` in documentation; never record a real address.

## Long paths and troubleshooting

If extraction or custom-node installation fails because a path is too long, shorten the installation
root first. Windows also has a `LongPathsEnabled` policy, but applications must opt in before the
policy helps them. Check the policy with:

```powershell
Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name LongPathsEnabled
```

When startup fails, work from the command window and isolate in this order: GPU launcher versus
CPU launcher, missing model path, custom-node import error, dependency mismatch, then driver or
hardware problem. Keep a copy of the startup log and redact paths, usernames, hostnames, and local
addresses before sharing it.
