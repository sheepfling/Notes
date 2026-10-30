# Make Ctrl+V paste in VS Code with Vim keybindings

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

When the [VSCodeVim extension](https://marketplace.visualstudio.com/items?itemName=vscodevim.vim) is
active, `Ctrl+V` normally enters Vim Visual Block mode. If ordinary paste is more useful, let
VS Code handle that key instead.

## Recommended setting

Open VS Code `settings.json` and add:

```json
{
  "vim.handleKeys": {
    "<C-v>": false
  }
}
```

This tells VSCodeVim not to intercept `Ctrl+V`, so the editor's normal paste command handles it.
Reload the window or restart VS Code if the change does not take effect immediately.

## Keybindings alternative

If the behavior should vary by editor state, add a rule through `Preferences: Open Keyboard
Shortcuts (JSON)`:

```json
{
  "key": "ctrl+v",
  "command": "editor.action.clipboardPasteAction",
  "when": "editorTextFocus && vim.mode != 'Insert'"
}
```

The `when` clause keeps insert-mode handling separate. Removing it makes the paste command apply
regardless of Vim mode, but can change the expected behavior of the extension more broadly.

## Keep Visual Block mode available

Assign another key sequence to Visual Block mode, for example:

```json
{
  "vim.normalModeKeyBindingsNonRecursive": [
    {
      "before": ["<leader>", "v"],
      "after": ["<C-v>"]
    }
  ]
}
```

Check the configured Vim leader key before choosing the replacement sequence. Verify both paths:
paste in the modes where it is expected, and enter Visual Block mode through the replacement key.
