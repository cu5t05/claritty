# Getting Started with Claritty

Claritty is a controlled terminal and AI chat environment. Every command is validated before it runs. Every agent action requires your explicit approval.

---

## Input Conventions

Learn these before anything else. Most first-session friction comes from input format, not the commands themselves.

| Input type | How to enter it |
|------------|-----------------|
| Single line | Type and press Enter |
| Multiline | `<<EOF` on its own line, paste content, then `EOF` on its own line with no leading whitespace |
| y/n prompts | `y` or `n` only, no other input is accepted |
| String arguments | Wrap in single quotes. Use heredoc if the string contains a single quote or apostrophe |

The heredoc marker `EOF` must appear alone on its own line. Leading whitespace will prevent it from closing.

---

## Modes

Switch modes with colon commands.

| Command | Action |
|---------|--------|
| `:shell` | Run whitelisted system commands |
| `:chat` | Talk to an AI model |
| `:var` | View and manage stored variables |
| `:quit` | Exit Claritty |

---

## Shell Mode

Type commands normally. Only whitelisted commands and approved directories are permitted.

```
ls -la ./
cat -n ./notes.txt
grep -i "error" ./logs.txt
cd ./projects
```

Output appears between `---output---` and an exit code with timestamps.

If a command is rejected, Claritty states the reason. Nothing fails silently.

`Ctrl+C` at the prompt exits Claritty. `Ctrl+C` during a running command stops that command immediately and returns to the prompt with `[exit: 130]`.

---

## Variables

Capture command output into a variable for reuse.

```
$FILES= ls -la ./
```

Reference it later:

```
grep -i "config" $FILES
write $FILES ./output.txt
```

View all stored variables with `:var`. Clear one with `clear [name]` or all with `clear all`.

Variables are session-scoped and do not persist between sessions.

---

## Writing Files

Create a new file:

```
write 'hello world' ./notes.txt
```

Edit a specific line:

```
write -n 3 'updated line' ./notes.txt
```

Wrap content in single quotes. Everything inside is preserved literally, including double quotes and special characters. If the content contains a single quote or apostrophe, use heredoc instead:

```
write <<EOF ./notes.txt
it's a "complicated" string
EOF
```

Write multiple lines using heredoc:

```
write <<EOF ./notes.txt
line one
line two
EOF
```

`EOF` must appear on its own line with no leading whitespace or the block will not close.

---

## Actions

Actions are pre-authored scripts you run with the do command.

```
do hash 'my string'
```

Single quotes wrap the argument as a raw string, everything inside is preserved literally, including double quotes, nested quotes, and special characters:

```
do hash 'print("hello")'
do hash 'grep "status: "critical"" ./report.txt'
```

The only exception is a literal single quote or apostrophe inside the string. For those, use heredoc:

```
do hash <<EOF
it's a "complicated" string
EOF
```

Heredoc is also the right choice for multiline content:

```
do hash <<EOF
line one
line two
EOF
```

Before an action can run, its hash must be registered in config.json. If the code changes, the hash no longer matches and the action is rejected.

Actions bypass the directory whitelist by design, they can operate on any path their code references. Review action code before hashing and trusting it. See the administrator section in the README for how to add and trust new actions.

---

## Chat Mode

Switch to chat with `:chat`. Type your message and press Enter to send.

For multiline input, use heredoc:

```
<<EOF
paste your content here
EOF
```

`Ctrl+C` during heredoc input cancels collection and returns to the prompt.

`Ctrl+C` at any other point exits Claritty.

Manage your conversation:

| Command | Action |
|---------|--------|
| `:buffer` | View conversation history |
| `:revert [index]` | Remove entries after index |
| `:chat-clear` | Clear entire conversation |
| `:save [filepath]` | Export conversation to file |

---

## Agent Mode

Agent mode lets the AI generate commands for execution. Only works inside chat mode.

Enable it:

```
:agent
```

When enabled, the AI receives your command whitelist and available actions as context automatically. You do not need to explain available commands to the agent, it already knows what it can propose.

The model cannot see your terminal output. It only knows what you explicitly send in chat. Token usage stays minimal because the model never ingests your filesystem.

When the AI responds with a code block, Claritty will:

1. Ask `y` to proceed or `n` to abort
2. If the response contains multiple code blocks, you will be shown a numbered list and asked to select one
3. Show every command with a `PASSED` or `FAILED` status
4. Ask you to type a 3-digit confirmation number before anything runs

Nothing executes without your explicit approval at every step. The model cannot see the consent number and cannot influence which batch runs.

`Ctrl+C` at any prompt during the agent flow aborts the batch immediately.

Disable agent mode at any time with `:agent` again.

---

## Configuration

All configuration lives in `config.json`. Open it in any text editor before first use.

**CONFIG_PATH**

Open `chat.py` and `claritty.py` and update `CONFIG_PATH` to the absolute path of your `config.json`. This must be an absolute path, relative paths will fail.

**allowed_directories**

List every folder Claritty is permitted to access. Any path outside these will be rejected.

Best practice: keep this to a single directory. Every additional entry expands the attack surface and increases the agent's potential blast radius. Plan your workflow around one root folder and keep everything inside it.

```json
"allowed_directories": [
    "/Users/yourname/projects"
]
```

**command_whitelist**

Each entry defines one permitted command. You can add, remove, or modify commands to fit your workflow. Each command has four fields:

| Field | Description |
|-------|-------------|
| `man` | Description shown to the agent |
| `requires_path` | Whether the command needs a file or directory argument |
| `allowed_flags` | Flags permitted for this command |
| `allows_text` | Whether plain text arguments are accepted |

Example adding a new command:

```json
"wc": {
    "man": "Count lines, words, or characters in a file. Flags: -l lines, -w words, -c characters.",
    "requires_path": true,
    "allowed_flags": ["-l", "-w", "-c"],
    "allows_text": false
}
```

**actions_whitelist**

Each entry maps an action name to the SHA-256 hash of its code string. An action missing from this list or with a mismatched hash will be rejected before execution.

```json
"actions_whitelist": {
    "hash": "3dee60c3daa787d74c6642967faa1d96f9f61ba80dbc543f2015731139636a7c"
}
```

**api_template**

Configures available chat providers. Three providers are included: anthropic, openai, and llamacpp for local models. Update models to reflect the versions you have access to. Set max_calls_per_minute and token_limit_warning to match your usage limits.

---

## Key Principles

- The AI never sees your terminal output unless you send it explicitly
- No command runs without passing whitelist validation
- Agent execution always requires your physical confirmation
- The model cannot see the consent number and cannot influence which batch runs
- Actions bypass the directory whitelist, review code before trusting it
- All data you keep local stays local
- Multiline input uses heredoc. y/n prompts accept only y or n