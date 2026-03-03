# Claritty

A portable, zero-dependency Python shell built for controlled human-AI collaboration. Claritty gives users and AI agents access to local systems through a configurable command whitelist, with every execution requiring explicit human consent.

## Philosophy

Most shells are built for unrestricted access and retrofitted with security. Claritty inverts that, restriction is the foundation, not an afterthought. Every command must be whitelisted before it can run. Every AI-generated code block requires human review and consent before execution. The system is designed to keep humans in control while making AI assistance genuinely useful.

Rather than anticipating every use case and baking it in, Claritty opens a door and trusts the user to walk through it responsibly. Capability scales through intent, not complexity. The action system is the clearest expression of this: users define what the system can do, verify it with a hash, and the system trusts it. No feature creep. No inherited complexity.

The three-file architecture is itself a security statement. A system small enough to read in an afternoon is a system you can actually trust.

Security concerns that belong to the OS or deployment layer are intentionally delegated there. Claritty enforces only what an application layer should enforce.

## Why Claritty

**For security-conscious teams**
Every executed command is whitelisted. Every AI-generated action requires explicit human consent and a physical keyboard confirmation. The audit trail is the architecture, not an add-on. Nothing executes without authorization, and every rejection tells you why.

**For environments where accountability matters**
Claritty's design maps naturally onto the principles that high-accountability environments require: least-privilege access, data minimization, human-in-the-loop controls, and verifiable execution chains. The model reasons and proposes. The human decides. These are not settings, they are the foundation.

Data stays local. The model sees only what you explicitly send it. Command output never enters the AI's context unless you choose to share it. This is not a privacy feature, it is the architecture.

**For developers who want AI assistance without surrendering control**
Claritty makes AI genuinely useful in sensitive workflows without exposing your system to the model. The model never ingests your filesystem, it only sees what you explicitly feed it. You get the reasoning capability without the access risk, and token usage stays minimal as a direct result.

**For administrators**
A four-file deployment with no external dependencies, no network calls beyond the AI provider API, and a configuration model that requires no code changes to extend or restrict capability. The entire trust surface is readable in an afternoon.

## Security Foundations

1. User input is handled as raw text, validated before subprocess, no shell expansion possible.
2. Single whitelisted directory eliminates ambiguity, enforces security inheritance, contains all agentic work within one auditable boundary.
3. Whitelist is explicit and extensible, constrains without blocking real dev workflows, forces clarity about what the agent actually needs.
4. Defense in depth: raw text, whitelist, path validation, consent gate, and batch fail-fast are independent choke points.
5. Chat and shell are separate: model only sees prompts and responses, command outputs never enter chat memory.
6. Consent number lives in Claritty's terminal only, model cannot see or influence it.
7. Whitelist man keys self-define the agent's available workflow: AI can only propose what the whitelist permits.
8. New tools like git or Terraform added via a single dict entry, blast radius contained automatically.
9. API keys session-only, memory-only, never persisted, masked on entry.
10. 710 on claritty and chat, 600 on config, 700 on all other shells: logical sandbox through standard Unix permissions, minimal enterprise requirement with high security ROI.
11. Agentic batch integrity enforced: any single unauthorized command kills the entire batch. No partial execution, no ambiguous state. Either everything runs clean or nothing runs.
12. Action trust model: every action is SHA-256 hashed and verified before execution. Code changes invalidate the hash. No action runs without explicit user trust.
13. Model context is explicitly user-controlled, command output never enters AI memory unless the user sends it.
14. Zero external dependencies eliminates supply chain risk entirely, no dependency chain to audit, poison, or drift.
15. The entire trust surface is four files. A system you can read completely is a system you can actually trust.

## Architecture

Claritty is built across four files. Each Python file uses a hash-based table of contents for rapid navigation. Sections are bounded by `#hash-start` and `#hash-end` markers, mapped to descriptions in the file header.

Core files:
- `claritty.py` — main shell, validation pipeline, execution, agent logic
- `chat.py` — AI conversation module, API abstraction, conversation buffer
- `config.json` — command whitelist, allowed directories, actions whitelist, configuration
- `actions.py` — user-defined actions dict, each entry contains code and man keys

### claritty.py

`a7f3k9`
imports
Standard library only, no external dependencies.

`b2m8n4`
parse_command
Splits raw input into program and argument tokens using shlex. No shell interpretation.

`c5q1p7`
dir and command whitelists
Loads allowed directories and command whitelist from config.json at startup.

`d9r6t3`
path resolution and validation
Resolves relative, absolute, and tilde paths. Checks resolved path against whitelist before any operation.

`f7x9z1`
validate_command
Checks program against whitelist, validates flags and arguments, enforces path rules. Single choke point for all execution.

`g3v5b6`
execute_command
Runs validated commands via subprocess.Popen with shell=False. Streams output line by line.

`l5m7n2`
session logging
TeeStream intercepts stdout and mirrors to shell.log. Disabled by default, intended for enterprise audit and SIEM use.

`e2w7q9`
print_footer
Prints exit code and timestamp range after every command execution.

`i1k4j7`
main_loop
Routes input to the appropriate mode handler. Manages mode state and cwd across the session.

`j6p8r2`
internal_cd
Changes working directory internally without subprocess. Validates destination against whitelist before updating cwd.

`m4n8k2`
variable mode
Captures command output into named session variables. Reusable in subsequent commands without pipes or redirects.

`t2x8v3`
load_actions
Locates and imports actions.py at runtime using importlib. Returns the module or None if not found. Called on every do invocation, picks up changes without restart.

`s5y1u6`
internal do
Validates action name, checks whitelist, hashes code value, compares against config, resolves any <<EOF arguments, executes via subprocess with arguments forwarded as argv.

`n6h9w4`
internal grep
Runs grep against variable contents or file paths. Validates paths before access.

`p8q4r7`
write function
Writes content to whitelisted paths. Validates destination before any disk operation.

`a9b1c2`
agent mode
Detects code blocks in AI responses, handles user consent flow, validates batch, executes with fail-fast logic. Routes do, write, and grep to internal handlers.

`c8d9e1`
current mode
Tracks active mode (shell, chat, var) as module-level state.

`k9t3w5`
entry point
Initializes TeeStream, starts main loop, ensures clean teardown on exit.

### chat.py

`a1b2c3`
imports
Standard library only, no external dependencies.

`d4e5f6`
api_template
Loads provider configuration from config.json. Single source of truth for supported providers and models.

`g7h8i9`
module variables
Session-scoped API keys and conversation buffer. No persistence between sessions.

`j1k2l3`
set_provider
Selects active AI provider from loaded config.

`m4n5o6`
set_model
Selects model for active provider.

`p7q8r9`
set_api_key
Accepts key via hidden input (getpass). Stored in memory only, never written to disk.

`s1t2u3`
api_key_check
Validates key is present before any API call. Fails cleanly if missing.

`v4w5x6`
send_prompt
Builds request with full conversation context, sends to provider API, stores prompt and response atomically in buffer.

`b3c4d5`
usage management
Tracks token usage per exchange if returned by provider.

`w8x9y1`
show_buffer
Displays conversation buffer with indices for revert reference.

`r5t6u7`
revert
Deletes buffer from specified index to end. Always targets even indices to keep prompt/response pairs intact.

`s4t5u6`
save_chat
Exports buffer to file in terminal display format. Appends .txt if no extension provided.

`e8f9g1`
eof mode
Accumulates multiline input between <<EOF and EOF markers, assembles into single prompt before sending.

`y7z8a9`
entry point
Module guard, not executed when imported by claritty.py.

### actions.py

Single file in the same directory as claritty.py. Contains one module-level dict named ACTIONS. Each key is the action name. Each value is a dict with two keys: code and man.

code — Python string executed via python3 -c. Arguments passed by the user are forwarded as sys.argv items.
man — plain English description sent to the agent as context when agent mode is enabled.

Actions support quoted strings and <<EOF heredoc blocks at any argument position. Use single quotes when content contains double quotes. Use <<EOF for multiline input. Each <<EOF token is resolved before execution.

### config.json

- `allowed_directories` — paths where commands may operate
- `command_whitelist` — permitted commands, flags, and argument rules including do
- `actions_whitelist` — maps each action name to the SHA-256 hash of its code value
- `api_template` — AI provider configuration

## For Users

Claritty is a restricted shell. This means:

- Only whitelisted commands can run. Commands not on the whitelist will be rejected with an explanation.
- All file operations are restricted to approved directories. You cannot read or write outside those boundaries.
- In agent mode, no AI-generated command runs without your explicit review and consent. The model cannot see or influence the consent confirmation.
- If a command is rejected, Claritty states the reason. Nothing fails silently.
- In enterprise deployments, session logging may be enabled. If so, all terminal output is recorded to a log file. Your administrator is responsible for informing you when logging is active.

## For Administrators

### Deployment

- Install claritty.py in a system location (e.g. /usr/local/bin) with 755 permissions, root owned.
- Set config.json to 600 permissions. Users cannot view or modify the whitelist.
- Set native shells (bash, sh, zsh) to 700 to prevent bypass.
- CONFIG_PATH in claritty.py must be set to the absolute path of config.json before distributing to users. Relative paths will fail.

### Logging

Session logging is disabled by default. To enable, set `enabled=True` in the TeeStream initialization in section `k9t3w5` of claritty.py.

When enabled, all terminal output is mirrored to shell.log in the working directory. The log path can be hardcoded to an absolute path by the administrator. This is intended for enterprise environments requiring audit trails and SIEM integration.

Administrator responsibilities when enabling logging:

- Inform users that their session activity is being recorded before they begin using the shell.
- Restrict access to shell.log using OS-level file permissions. The log file should not be readable by the user account running the shell.
- Define and document a log retention policy appropriate to your organization and applicable regulations.
- If forwarding logs to a SIEM, ensure the log pipeline itself is access-controlled and audited.
- Review logs only for legitimate security and operational purposes consistent with your organization's policy.

Failure to notify users of active logging may violate privacy obligations depending on jurisdiction and organizational policy.

### Config

config.json controls:
- `allowed_directories` — paths where commands may operate
- `command_whitelist` — permitted commands, flags, and argument rules
- `actions_whitelist` — trusted actions and their verified hashes
- `api_template` — AI provider configuration

### Actions

Actions extend Claritty with user-defined Python scripts. They bypass the command whitelist and directory whitelist by design. Trust is established explicitly via SHA-256 hash verification, not path scope. Review action code before hashing.

To add a new action:
1. Add an entry to ACTIONS in actions.py with code and man keys
2. Run `do hash` to compute the hash of the code string
3. Add the action name and hash to actions_whitelist in config.json
4. Call `do [name]` — hash check passes, action executes

Actions can accept arguments via sys.argv. Use single quotes for strings containing double quotes. Use <<EOF for multiline input.

The included hash action bootstraps the workflow. Its own hash must be computed manually the first time using python3 in the terminal, then added to config.json. After that, do hash handles all future hashing.

## Modes

Shell mode — default. Input runs through the validation pipeline before execution. Commands must be whitelisted, paths must be within allowed directories.

Chat mode — `:chat` toggles chat backend. All input is sent to the configured AI provider as conversation. `:shell` returns to shell mode.

Agent mode — `:agent` inside chat mode enables agentic execution. The AI receives the command whitelist and available actions as context automatically — you do not need to explain available commands to the agent. When the AI generates a code block, Claritty detects it and prompts for consent before execution.

Var mode — `:var` manages session variables. Variable output can be reused in subsequent commands without shell expansion risks.

## Agent Execution Flow

1. User enables agent with `:agent` inside chat mode
2. Command whitelist and action list injected into AI context automatically
3. User converses with AI normally
4. Code block detected in response, prompt: `y to execute, n to abort`
5. If multiple blocks detected, numbered selection after `y`
6. Selected block parsed into command list
7. Commands validated against whitelist, full list displayed with `[PASSED]` / `[FAILED]`
8. Any failure, batch rejected
9. All pass, 3-digit consent number displayed
10. User types number, batch executes sequentially
11. Batch halts on first failed command
12. The model never sees the consent number and cannot influence which batch runs

## Security Model

- `shell=False` throughout, no shell injection possible
- Whitelist validation before every execution
- Path validation restricts all operations to approved directories
- AI cannot trigger execution, physical keyboard input required at every consent step
- AI cannot see consent number
- Consent number is single-use per batch
- Batch halts on first failure, no cascading damage
- Actions verified by SHA-256 hash before every execution, code changes invalidate trust
- Model context is explicitly user-controlled, command output never enters AI memory unless the user sends it

Security features that belong to the OS such as user isolation, filesystem permissions, and process limits are handled at deployment, not in code.

## Variable System

Variables capture command output for reuse without pipes or redirects.

```
$FILES= ls ./
grep ".py" $FILES
```

Variables are session-scoped and cleared on exit. Managed via `:var` mode.

## Action System

Actions are pre-authored Python scripts stored in actions.py and executed via the do command.

```
do hash 'my string'
do hash <<EOF
multiline
content
EOF
```

Each action is verified by SHA-256 hash before execution. Any change to the code string invalidates the hash and rejects the action. Users and agents share the same action interface. The agent calls do [name] like any other command, subject to the same hash verification.

## Session Logging

TeeStream intercepts stdout at program startup. All terminal output is mirrored to shell.log when enabled. Disabled by default. See the Logging section under For Administrators for deployment requirements.

## Requirements

- Python 3.x
- No external dependencies
- API key required for chat and agent mode (Anthropic, OpenAI, or local llama.cpp)

## Supported AI Providers

- Anthropic (Claude)
- OpenAI (GPT)
- llama.cpp (local, no key required)