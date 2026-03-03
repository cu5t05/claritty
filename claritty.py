#!/usr/bin/env python3
"""
TABLE OF CONTENTS
=================
a7f3k9 = imports
b2m8n4 = parse_command function
c5q1p7 = config path
d9r6t3 = path resolution and validation functions
f7x9z1 = validate_command function
g3v5b6 = execute_command function
l5m7n2 = session logging (TeeStream class) - disabled by default
e2w7q9 = print_footer
i1k4j7 = main_loop function
j6p8r2 = internal cd
m4n8k2 = variable mode
t2x8v3 = load_actions
s5y1u6 = internal do
n6h9w4 = internal grep
p8q4r7 = internal write
a9b1c2 = agent mode
c8d9e1 = current mode
k9t3w5 = entry point
"""

#a7f3k9-start
import os
import json
import sys
import shlex
import subprocess
import hashlib
import importlib.util
from datetime import datetime
import chat
import random
#a7f3k9-end

#b2m8n4-start
def parse_command(user_input):
    cleaned = user_input.strip()
    try:
        tokens = shlex.split(cleaned)
    except ValueError:
        print("!-Invalid command: unclosed quote-!")
        return None, []
    
    if not tokens:
        return None, []
    
    program = tokens[0]
    arguments = tokens[1:]
    return program, arguments
#b2m8n4-end

#c5q1p7-start
CONFIG_PATH = "/Users/you/your-work-dir/wherever-has/config.json"
with open(CONFIG_PATH, "r") as f:
    _config = json.load(f)

ALLOWED_DIRECTORIES = _config["allowed_directories"]
COMMAND_WHITELIST = _config["command_whitelist"]
#c5q1p7-end

#d9r6t3-start
def resolve_path(path_string, current_working_directory):
    # Expand ~ to home directory
    expanded = os.path.expanduser(path_string)
    
    # Convert relative to absolute
    if not os.path.isabs(expanded):
        absolute_path = os.path.join(current_working_directory, expanded)
    else:
        absolute_path = expanded
    
    # Normalize path
    normalized = os.path.normpath(absolute_path)
    
    # If path exists, resolve symlinks
    if os.path.exists(normalized):
        normalized = os.path.realpath(normalized)
    
    return normalized

def is_path_allowed(path_string, current_working_directory):
    normalized = resolve_path(path_string, current_working_directory)
    
    # Check if inside any allowed directory
    for allowed_dir in ALLOWED_DIRECTORIES:
        if normalized.startswith(allowed_dir):
            return True
    
    return False
#d9r6t3-end

#f7x9z1-start
def validate_command(program, arguments, current_working_directory):
    # Check command whitelist
    if program not in COMMAND_WHITELIST:
        return False, "Command not allowed"
    
    cmd_config = COMMAND_WHITELIST[program]
    has_path = False
    
    # Check each argument
    skip_next = False
    for arg in arguments:
        if skip_next:
            skip_next = False
            continue
        
        if arg.startswith("-"):
            # It's a flag - check allowed flags
            if arg == "-n" and program in ["head", "tail"]:
                skip_next = True
            if arg not in cmd_config["allowed_flags"]:
                return False, f"Argument not allowed: {arg}"
        elif arg.startswith(("/", "./", "~/", "../")):
            # It's a path - check directory whitelist
            if not is_path_allowed(arg, current_working_directory):
                return False, f"Path not allowed: {arg}"
            has_path = True
        else:
            # Not a flag or path - check if text allowed
            if not cmd_config["allows_text"]:
                return False, f"Invalid argument format: {arg}"
            # Text arguments allowed for this command
    
    # Check if path is required but missing
    if cmd_config["requires_path"] and not has_path:
        return False, "Command requires at least one path argument"
    
    return True, "OK"
#f7x9z1-end

#g3v5b6-start
def execute_command(program, arguments, current_working_directory):
    # Build command list
    cmd = [program] + arguments
    
    # Execute with shell=False
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd=current_working_directory
    )
    
    try:
        # Stream output line by line
        for line in process.stdout:
            print(line.decode(), end='')
        
        # Get any errors
        stderr = process.stderr.read().decode()
        
        # Wait for completion
        returncode = process.wait()
        
        return returncode, stderr
    
    except KeyboardInterrupt:
        # User pressed Ctrl+C - terminate the process
        process.terminate()
        process.wait()
        raise
#g3v5b6-end

#l5m7n2-start
class TeeStream:
    def __init__(self, file_path, enabled=False):
        self.terminal = sys.stdout
        self.enabled = enabled
        self.log_file = None
        
        if self.enabled:
            self.log_file = open(file_path, 'a')
    
    def write(self, message):
        self.terminal.write(message)
        if self.enabled and self.log_file:
            self.log_file.write(message)
    
    def flush(self):
        self.terminal.flush()
        if self.enabled and self.log_file:
            self.log_file.flush()
    
    def close(self):
        if self.log_file:
            self.log_file.close()
#l5m7n2-end

#e2w7q9-start
def print_footer(exit_code, start_time):
    end_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[exit: {exit_code}]")
    print(f"[{start_time} - {end_time}]")
    print("------------")
    print("\n")
#e2w7q9-end

#i1k4j7-start
def main_loop():
    """
    MAIN LOOP SUBSECTIONS
    =====================
    q1w2e3 = variable assignment handler
    h3k7m1 = do handler
    r4t5y6 = internal grep handler
    u7i8o9 = internal write handler
    a2s3d4 = variable substitution handler
    f5g6h7 = internal cd handler
    j8k9l0 = normal command execution handler
    """
    
    global current_mode
    cwd = os.getcwd()
    eof_mode = False
    eof_array = []

    while True:
        try:
            user_input = input()
        except (EOFError, KeyboardInterrupt):
            print("\n[shell terminated]")
            break
        
        if user_input == ":quit":
            print("[shell terminated]")
            break
        
        # mode switches
        if user_input == ":shell":
            current_mode = "shell"
            print("[SHELL]\n")
            eof_mode = False
            eof_array = []
            continue
        
        if user_input == ":chat":
            current_mode = "chat"
            if not hasattr(main_loop, "chat_counter"):
                main_loop.chat_counter = 0
            main_loop.chat_counter += 1
            if main_loop.chat_counter == 1:
                print(chat.CHAT_HELP)
            else:
                if getattr(main_loop, "agent_enabled", False):
                    print("[CHAT - AGENT ENABLED]\n")
                else:
                    print("[CHAT]\n")
            continue

        if user_input == ":agent":
            if current_mode != "chat":
                print("!-Agent requires chat mode-!")
            else:
                main_loop.agent_enabled = not getattr(main_loop, "agent_enabled", False)
                if main_loop.agent_enabled:
                    print("!-Agent enabled. :agent again to disable-!")
                    tool_list = str(COMMAND_WHITELIST)
                    actions_module = load_actions()
                    if actions_module is not None:
                        action_list = "\n".join(
                            f"{name}: {entry['man']}"
                            for name, entry in actions_module.ACTIONS.items()
                        )
                    else:
                        action_list = "None"
                    chat.send_prompt(f"{_config.get('agent_instructions', '')}\n\nThe following tools are available to you:\n\n{tool_list}\n\nThe following actions are available and can be used via 'do' command:\n\n{action_list}\n\nOnly use these commands when generating code blocks for execution.")
                else:
                    print("!-Agent disabled-!")
            continue
        
        if user_input == ":var":
            current_mode = "var"
            print("[VAR]\n")
            if not VARIABLES:
                print("No variables defined\n")
            else:
                for vname, value in VARIABLES.items():
                    display_name = vname[:12]
                    display_value = value.replace("\n", "\\n")[:60]
                    if len(value.replace("\n", "\\n")) > 60:
                        display_value += "..."
                    print(f"${display_name:<12} {display_value}")
                print()
            print("clear [name] - remove specific variable")
            print("clear all    - remove all variables")
            print(":shell       - return to shell\n")
            continue
        
        # chat backend
        if current_mode == "chat":

            if user_input == ":set-provider":
                chat.set_provider()
                continue

            if user_input == ":set-model":
                chat.set_model()
                continue

            if user_input == ":set-key":
                chat.set_api_key()
                continue

            if user_input == ":buffer":
                chat.show_buffer()
                continue

            if user_input.startswith(":revert"):
                chat.revert_command(user_input)
                continue

            if user_input == ":chat-clear":
                chat.conversation_buffer.clear()
                print("!-Buffer cleared-!")
                continue

            if user_input.startswith(":save"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("!-Usage: :save [filepath]-!")
                    continue
                exit_code, result = chat.save_chat(parts[1])
                if exit_code == 0:
                    print(f"Saved to {result}")
                else:
                    print(f"!-{result}-!")
                continue

            eof_mode, eof_array, prompt = chat.handle_eof(user_input, eof_mode, eof_array)
            if prompt is not None:
                response = chat.send_prompt(prompt)
                if getattr(main_loop, "agent_enabled", False) and response:
                    run_agent(response, cwd)
            continue
        
        # var backend
        if current_mode == "var":
        
            if user_input == "clear all":
                VARIABLES.clear()
                print("All variables cleared\n")
                continue
        
            if user_input.startswith("clear "):
                var_name = user_input[6:].strip().lstrip("$")
                if var_name in VARIABLES:
                    del VARIABLES[var_name]
                    print(f"Variable ${var_name} cleared\n")
                else:
                    print(f"Variable ${var_name} not found\n")
                continue
        
            print("Unknown command\n")
            continue
        
        #q1w2e3-start
        success, var_name, command_string, error_msg = parse_variable_assignment(user_input)
        
        if not success and error_msg:
            print(f"!-{error_msg}-!")
            print("\n")
            continue
        
        if var_name is not None:
            start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            program, arguments = parse_command(command_string)
            
            if program is None:
                continue
            
            valid, error_msg = validate_command(program, arguments, cwd)
            
            if not valid:
                print(f"!-{error_msg}-!")
                print_footer(1, start_time)
                continue
            
            cmd = [program] + arguments
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                cwd=cwd
            )
            
            stdout, stderr = process.communicate()
            output = stdout.decode().strip()
            
            VARIABLES[var_name] = output
            
            print(f"Variable ${var_name} assigned")
            print_footer(process.returncode, start_time)
            continue
        #q1w2e3-end
        
        program, arguments = parse_command(user_input)

        if program is None:
            continue

        #h3k7m1-start
        if program == "do":
            start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            if len(arguments) < 1:
                print("!-do requires an action name-!")
                print_footer(1, start_time)
                continue
            returncode = do(arguments[0], arguments[1:], cwd)
            print_footer(returncode, start_time)
            continue
        #h3k7m1-end
        
        #r4t5y6-start
        if program == "grep":
            if len(arguments) < 2:
                start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print("!-grep requires pattern and target-!")
                print_footer(1, start_time)
                continue
            
            grep_flags = []
            pattern = None
            target = None
            for arg in arguments:
                if arg.startswith("-"):
                    grep_flags.append(arg)
                elif pattern is None:
                    pattern = arg
                elif target is None:
                    target = arg
                else:
                    start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    print("!-grep accepts only pattern and target-!")
                    print_footer(1, start_time)
                    continue

            if pattern is None or target is None:
                start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print("!-grep requires pattern and target-!")
                print_footer(1, start_time)
                continue

            if target.startswith("$"):
                var_name = target[1:]
                if var_name not in VARIABLES:
                    start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"!-Undeclared variable: ${var_name}-!")
                    print_footer(1, start_time)
                    continue
                target = VARIABLES[var_name]
            
            is_path = target.startswith(("./", "/", "~/", "../"))
            
            if not is_path:
                start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print("---output---")
                
                exit_code, error_msg = internal_grep(pattern, target, grep_flags)
                
                if error_msg:
                    print(f"!-{error_msg}-!")
                
                print_footer(exit_code, start_time)
                continue
        #r4t5y6-end
        
        #u7i8o9-start
        if program == "write":
            if len(arguments) < 2:
                start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print("!-write requires content and file path-!")
                print_footer(1, start_time)
                continue
            
            content_arg = None
            target_path = None
            line_spec = None

            i = 0
            while i < len(arguments):
                arg = arguments[i]
                if arg.startswith("-"):
                    if arg == "-n":
                        if i + 1 < len(arguments):
                            line_spec = arguments[i + 1]
                            i += 2
                        else:
                            start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                            print("!--n flag requires line specification-!")
                            print_footer(1, start_time)
                            continue
                    else:
                        start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                        print(f"!-Unknown flag: {arg}-!")
                        print_footer(1, start_time)
                        continue
                elif content_arg is None:
                    content_arg = arg
                    i += 1
                elif target_path is None:
                    target_path = arg
                    i += 1
                else:
                    start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    print("!-write accepts only content and file path-!")
                    print_footer(1, start_time)
                    continue

            if content_arg is None or target_path is None:
                start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print("!-write requires content and file path-!")
                print_footer(1, start_time)
                continue
            
            if content_arg == "<<EOF":
                heredoc_lines = []
                while True:
                    line = input()
                    if line == "EOF":
                        break
                    heredoc_lines.append(line)
                content = '\n'.join(heredoc_lines)
            elif content_arg.startswith("$"):
                var_name = content_arg[1:]
                if var_name not in VARIABLES:
                    start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"!-Undeclared variable: ${var_name}-!")
                    print_footer(1, start_time)
                    continue
                content = VARIABLES[var_name]
            else:
                content = content_arg
            
            start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            exit_code, error_msg = internal_write(content, target_path, line_spec, cwd)
            
            if error_msg:
                print(f"!-{error_msg}-!")
            else:
                print("File written successfully")
            
            print_footer(exit_code, start_time)
            continue
        #u7i8o9-end

        #a2s3d4-start
        try:
            arguments = substitute_variables(arguments)
        except ValueError as e:
            start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"!-{str(e)}-!")
            print_footer(1, start_time)
            continue
        #a2s3d4-end

        start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        #f5g6h7-start
        if program == "cd":
            success, message, new_path = internal_cd(arguments, cwd)
            
            if success:
                cwd = new_path
                print(message)
                print_footer(0, start_time)
            else:
                print(message)
                print_footer(1, start_time)
            
            continue
        #f5g6h7-end
        
        #j8k9l0-start
        valid, error_msg = validate_command(program, arguments, cwd)
        
        if not valid:
            print(f"!-{error_msg}-!")
            print_footer(1, start_time)
            continue
        
        print("---output---")
        
        try:
            returncode, stderr = execute_command(program, arguments, cwd)
            print_footer(returncode, start_time)
        
        except KeyboardInterrupt:
            print("\n!-Command stopped by user-!")
            print_footer(130, start_time)
        #j8k9l0-end
#i1k4j7-end

#j6p8r2-start
def internal_cd(arguments, current_working_directory):
    # Validate argument count
    if len(arguments) != 1:
        return False, "cd requires exactly one path argument", None
    
    target_path = arguments[0]
    resolved_path = resolve_path(target_path, current_working_directory)
    
    # Check if path exists
    if not os.path.exists(resolved_path):
        return False, "Directory does not exist", None
    
    # Check if it's a directory
    if not os.path.isdir(resolved_path):
        return False, "Not a directory", None
    
    # Validate against whitelist
    if not is_path_allowed(target_path, current_working_directory):
        return False, "Directory not in allowed whitelist", None
    
    return True, resolved_path, resolved_path
#j6p8r2-end

#m4n8k2-start
VARIABLES = {}

def parse_variable_assignment(user_input):
    """Check if input is a variable assignment like $VAR= command"""
    stripped = user_input.strip()
    
    if not stripped.startswith("$"):
        return True, None, None, None
    
    if "=" not in stripped:
        return False, None, None, "Invalid variable assignment syntax"
    
    # Split on first = only
    parts = stripped.split("=", 1)
    var_name = parts[0][1:].strip()  # Remove $ prefix
    command_string = parts[1].strip()
    
    if not var_name or not command_string:
        return False, None, None, "Invalid variable assignment syntax"
    
    return True, var_name, command_string, None

def substitute_variables(arguments):
    """Replace $VAR references with stored values"""
    new_arguments = []
    
    for arg in arguments:
        if arg.startswith("$"):
            var_name = arg[1:]
            if var_name in VARIABLES:
                new_arguments.append(VARIABLES[var_name])
            else:
                raise ValueError(f"Undeclared variable: ${var_name}")
        else:
            new_arguments.append(arg)
    
    return new_arguments
#m4n8k2-end

#t2x8v3-start
def load_actions():
    actions_dir = os.path.dirname(os.path.abspath(__file__))
    actions_path = os.path.join(actions_dir, "actions.py")

    if not os.path.isfile(actions_path):
        return None

    spec = importlib.util.spec_from_file_location("actions", actions_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
#t2x8v3-end

#s5y1u6-start
def do(action_name, arguments, cwd):
    # STEP 1 - load actions module
    actions_module = load_actions()
    if actions_module is None:
        print("!-actions.py not found-!")
        return 1

    # STEP 2 - look up action by name
    if action_name not in actions_module.ACTIONS:
        print(f"!-Unknown action: {action_name}-!")
        return 1
    action = actions_module.ACTIONS[action_name]

    # STEP 3 - check actions_whitelist in config
    if action_name not in _config.get("actions_whitelist", {}):
        print(f"!-Action not in whitelist: {action_name}-!")
        return 1

    # STEP 4 - hash code value
    code_string = action["code"]
    code_bytes = code_string.encode("utf-8")
    computed_hash = hashlib.sha256(code_bytes).hexdigest()

    # STEP 5 - compare against config hash
    expected_hash = _config["actions_whitelist"][action_name]
    if computed_hash != expected_hash:
        print(f"!-Hash mismatch, action rejected: {action_name}-!")
        return 1

    # STEP 6 - resolve any <<EOF arguments
    resolved = []
    for arg in arguments:
        if arg == "<<EOF":
            heredoc_lines = []
            while True:
                line = input()
                if line == "EOF":
                    break
                heredoc_lines.append(line)
            resolved.append('\n'.join(heredoc_lines))
        else:
            resolved.append(arg)
    arguments = resolved

    # STEP 7 - execute
    process = subprocess.Popen(
        ["python3", "-c", code_string] + arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd=cwd
    )
    for line in process.stdout:
        print(line.decode(), end="")
    stderr_output = process.stderr.read().decode()
    if stderr_output:
        print(stderr_output)
    return process.wait()
#s5y1u6-end

#n6h9w4-start
def internal_grep(pattern, target_text, flags):
    # Validate pattern
    if not pattern:
        return 1, "Pattern cannot be empty"
    
    # Validate target text
    if not target_text:
        return 1, "Variable content is empty"
    
    # Validate flags
    allowed_flags = ["-i", "-v", "-n"]
    for flag in flags:
        if flag not in allowed_flags:
            return 1, f"Flag not allowed: {flag}"
    
    # Process flags
    case_insensitive = "-i" in flags
    invert_match = "-v" in flags
    show_line_numbers = "-n" in flags
    
    # Prepare search
    lines = target_text.split("\n")
    search_pattern = pattern.lower() if case_insensitive else pattern
    matches_found = 0
    
    # Search line by line
    for index, line in enumerate(lines, start=1):
        search_line = line.lower() if case_insensitive else line
        
        # Check match
        pattern_found = search_pattern in search_line
        is_match = (not pattern_found) if invert_match else pattern_found
        
        if is_match:
            matches_found += 1
            if show_line_numbers:
                print(f"{index}:{line}")
            else:
                print(line)
    
    # Return exit code
    return 0 if matches_found > 0 else 1, ""
#n6h9w4-end

#p8q4r7-start
def internal_write(content, file_path, line_spec, current_working_directory):
    # Validate inputs
    if not content:
        return 1, "Variable content is empty"
    
    if not file_path:
        return 1, "File path is required"
    
    # Resolve and validate path
    resolved_path = resolve_path(file_path, current_working_directory)
    
    if not is_path_allowed(file_path, current_working_directory):
        return 1, f"Path not allowed: {file_path}"
    
    # Determine mode
    if line_spec is None:
        # CREATE MODE - write new file
        try:
            with open(resolved_path, 'w') as f:
                f.write(content)
            return 0, ""
        except Exception as e:
            return 1, f"Failed to write file: {str(e)}"
    
    else:
        # EDIT MODE - modify existing file
        # Parse line specification
        if '-' in line_spec:
            parts = line_spec.split('-')
            if len(parts) != 2:
                return 1, "Invalid line range format (use N or N-M)"
            try:
                start_line = int(parts[0])
                end_line = int(parts[1])
            except ValueError:
                return 1, "Line numbers must be integers"
        else:
            try:
                start_line = int(line_spec)
                end_line = start_line
            except ValueError:
                return 1, "Line number must be an integer"
        
        # Validate line numbers
        if start_line < 1 or end_line < 1:
            return 1, "Line numbers must be greater than 0"
        
        if start_line > end_line:
            return 1, "Start line must be less than or equal to end line"
        
        # Check file exists
        if not os.path.exists(resolved_path):
            return 1, f"File not found: {file_path}"
        
        # Read existing file
        try:
            with open(resolved_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            return 1, f"Failed to read file: {str(e)}"
        
        # Validate line numbers within bounds
        if start_line > len(lines):
            return 1, f"Start line {start_line} exceeds file length {len(lines)}"
        
        if end_line > len(lines):
            return 1, f"End line {end_line} exceeds file length {len(lines)}"
        
        # Build new file content
        new_lines = content.split('\n')
        
        # Preserve newlines for content lines except the last one
        formatted_new_lines = [line + '\n' for line in new_lines[:-1]]
        if new_lines[-1]:  # Add last line with newline if not empty
            formatted_new_lines.append(new_lines[-1] + '\n')
        
        # Construct new file (line numbers are 1-indexed, list is 0-indexed)
        result = lines[:start_line-1] + formatted_new_lines + lines[end_line:]
        
        # Write back to file
        try:
            with open(resolved_path, 'w') as f:
                f.writelines(result)
            return 0, ""
        except Exception as e:
            return 1, f"Failed to write file: {str(e)}"
#p8q4r7-end

#a9b1c2-start
def extract_code_blocks(response_text):
    blocks = []
    search_start = 0

    while True:
        open_pos = response_text.find("```", search_start)
        if open_pos == -1:
            break

        close_pos = response_text.find("```", open_pos + 3)
        if close_pos == -1:
            break

        block = response_text[open_pos + 3:close_pos]

        lines = block.split("\n")
        if lines and not lines[0].strip().startswith((" ", "\t")) and " " not in lines[0].strip():
            lines = lines[1:]

        cleaned = "\n".join(lines).strip()
        if cleaned:
            blocks.append(cleaned)

        search_start = close_pos + 3

    return blocks

def parse_commands(block_text):
    lines = block_text.split("\n")
    commands = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            if "<<EOF" in stripped:
                heredoc_lines = []
                i += 1
                while i < len(lines):
                    if lines[i].strip() == "EOF":
                        break
                    heredoc_lines.append(lines[i].strip())
                    i += 1
                content = '\n'.join(heredoc_lines)
                command = stripped.replace("<<EOF", shlex.quote(content))
                commands.append(command)
            else:
                commands.append(stripped)
        i += 1
    return commands

BLOCKED_SYMBOLS = {"|", ">", ">>", "<", "&&", "||", ";"}

def validate_batch(commands, cwd):
    results = []
    for cmd in commands:
        # pass variable assignments
        success, var_name, command_string, error_msg = parse_variable_assignment(cmd)
        if var_name is not None:
            results.append({"command": cmd, "status": "PASSED", "reason": "OK"})
            continue

        program, arguments = parse_command(cmd)
        if program is None:
            results.append({"command": cmd, "status": "FAILED", "reason": "Parse error"})
            continue

        # block cd
        if program == "cd":
            results.append({"command": cmd, "status": "FAILED", "reason": "cd not permitted in agent mode"})
            continue

        # block shell operators
        if any(sym in cmd for sym in BLOCKED_SYMBOLS):
            results.append({"command": cmd, "status": "FAILED", "reason": "Pipes, redirects, and chaining not permitted"})
            continue

        # check program is whitelisted
        if program not in COMMAND_WHITELIST:
            results.append({"command": cmd, "status": "FAILED", "reason": "Command not allowed"})
            continue

        # pass commands with variable references, resolved at execution time
        if any(a.startswith("$") for a in arguments):
            results.append({"command": cmd, "status": "PASSED", "reason": "OK"})
            continue

        # standard whitelist validation
        valid, reason = validate_command(program, arguments, cwd)
        if valid:
            results.append({"command": cmd, "status": "PASSED", "reason": "OK"})
        else:
            results.append({"command": cmd, "status": "FAILED", "reason": reason})
    return results

def generate_consent_number():
    return str(random.randint(100, 999))

def run_agent(response_text, cwd):
    # scan for all code blocks
    blocks = extract_code_blocks(response_text)
    if not blocks:
        return

    # code detected, ask user
    print("!-Code detected. y to execute, n to abort-!")
    print("")
    while True:
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n!-Agent aborted-!")
            return None
        if confirm == "y":
            break
        elif confirm == "n":
            return None
        else:
            print("!-y or n only-!")

    # select block if multiple
    if len(blocks) == 1:
        selected_block = blocks[0]
    else:
        print(f"!-{len(blocks)} code blocks detected. Select one:-!")
        print("")
        for i, block in enumerate(blocks):
            print(f"{i+1}.")
            for line in block.split("\n"):
                print(f"   {line}")
        print("")
        while True:
            try:
                selection = input().strip()
            except (EOFError, KeyboardInterrupt):
                print("\n!-Agent aborted-!")
                return None
            try:
                index = int(selection) - 1
                if 0 <= index < len(blocks):
                    selected_block = blocks[index]
                    break
                else:
                    print(f"!-Enter 1 to {len(blocks)}-!")
            except ValueError:
                print(f"!-Enter 1 to {len(blocks)}-!")

    # parse commands
    commands = parse_commands(selected_block)

    # check cap
    if len(commands) > 10:
        print("!-10 commands max per batch-!")
        return

    # validate batch
    results = validate_batch(commands, cwd)

    # display full numbered list
    for i, result in enumerate(results):
        print(f"{i+1}. {result['command']} [{result['status']}] {result['reason']}")

    # abort if any failed
    if any(r["status"] == "FAILED" for r in results):
        print("!-Batch rejected. Failed commands present-!")
        return

    # consent gate
    consent_number = generate_consent_number()
    print(f"Type {consent_number} to execute:")
    try:
        user_number = input().strip()
    except (EOFError, KeyboardInterrupt):
        print("\n!-Agent aborted-!")
        return

    if user_number != consent_number:
        print("!-Consent mismatch. Batch aborted-!")
        return

    # execute batch
    command_queue = [r["command"] for r in results]
    batch_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    returncode = 0
    try:
        while len(command_queue) > 0:
            cmd = command_queue.pop(0)
            print(f"[EXECUTING]")
            print(cmd)

            # variable assignment - call parse_variable_assignment, execute via subprocess, store result
            success, var_name, command_string, error_msg = parse_variable_assignment(cmd)
            if var_name is not None:
                program, arguments = parse_command(command_string)
                if program is None:
                    print(f"!-Parse error in variable assignment-!")
                    returncode = 1
                    command_queue.clear()
                    print(f"!-Batch halted at failed command-!")
                    break
                sub_process = subprocess.Popen(
                    [program] + arguments,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    cwd=cwd
                )
                stdout, stderr = sub_process.communicate()
                VARIABLES[var_name] = stdout.decode().strip()
                print(f"Variable ${var_name} assigned")
                returncode = sub_process.returncode

            else:
                program, arguments = parse_command(cmd)

                # substitute variables in arguments
                try:
                    arguments = substitute_variables(arguments)
                except ValueError as e:
                    print(f"!-{str(e)}-!")
                    returncode = 1
                    command_queue.clear()
                    print(f"!-Batch halted at failed command-!")
                    break

                # internal do
                if program == "do":
                    if len(arguments) < 1:
                        print("!-do requires an action name-!")
                        returncode = 1
                    else:
                        returncode = do(arguments[0], arguments[1:], cwd)

                # internal write
                elif program == "write":
                    content_arg = None
                    target_path = None
                    line_spec = None
                    i = 0
                    while i < len(arguments):
                        if arguments[i] == "-n" and i + 1 < len(arguments):
                            line_spec = arguments[i + 1]
                            i += 2
                        elif content_arg is None:
                            content_arg = arguments[i]
                            i += 1
                        elif target_path is None:
                            target_path = arguments[i]
                            i += 1
                        else:
                            i += 1
                    exit_code, error_msg = internal_write(content_arg, target_path, line_spec, cwd)
                    if error_msg:
                        print(f"!-{error_msg}-!")
                    else:
                        print("File written successfully")
                    returncode = exit_code

                # internal grep
                elif program == "grep":
                    grep_flags = []
                    pattern = None
                    target = None
                    for arg in arguments:
                        if arg.startswith("-"):
                            grep_flags.append(arg)
                        elif pattern is None:
                            pattern = arg
                        elif target is None:
                            target = arg
                    if target and not target.startswith(("./", "/", "~/", "../")):
                        print("---output---")
                        exit_code, error_msg = internal_grep(pattern, target, grep_flags)
                        if error_msg:
                            print(f"!-{error_msg}-!")
                        returncode = exit_code
                    else:
                        valid, error_msg = validate_command(program, arguments, cwd)
                        if not valid:
                            print(f"!-{error_msg}-!")
                            returncode = 1
                        else:
                            print("---output---")
                            returncode, stderr = execute_command(program, arguments, cwd)

                # all other whitelisted commands
                else:
                    valid, error_msg = validate_command(program, arguments, cwd)
                    if not valid:
                        print(f"!-{error_msg}-!")
                        returncode = 1
                    else:
                        print("---output---")
                        returncode, stderr = execute_command(program, arguments, cwd)

            print("")
            if returncode != 0:
                command_queue.clear()
                print(f"!-Batch halted at failed command-!")
                break
    except KeyboardInterrupt:
        command_queue.clear()
        print("\n!-Batch interrupted-!")
        returncode = 130
    finally:
        print_footer(returncode, batch_start)
#a9b1c2-end

#c8d9e1-start
current_mode = "shell"
#c8d9e1-end

#k9t3w5-start
if __name__ == "__main__":
    cwd = os.getcwd()
    log_file_path = os.path.join(cwd, "shell.log")
    
    session_log = TeeStream(log_file_path, enabled=False)
    sys.stdout = session_log
    
    print("[SHELL]\n")
    
    try:
        main_loop()
    finally:
        session_log.close()
#k9t3w5-end