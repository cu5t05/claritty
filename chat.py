#!/usr/bin/env python3
"""
TABLE OF CONTENTS
=================
a1b2c3 = imports
d4e5f6 = config load
g7h8i9 = module variables
j1k2l3 = traverse
m4n5o6 = set_provider
p7q8r9 = set_model
s1t2u3 = set_api_key
v4w5x6 = api_key_check
b3c4d5 = check_rate_limit
w8x9y1 = send_prompt
r5t6u7 = show_buffer
s4t5u6 = revert_command
e8f9g1 = save_chat
k2l3m4 = entry point
"""

#a1b2c3-start
import os
import json
import getpass
import urllib.request
import time
from datetime import datetime
#a1b2c3-end

#d4e5f6-start
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_PATH, "r") as f:
    _config = json.load(f)

PROVIDERS = _config["api_template"]
#d4e5f6-end

#g7h8i9-start
api_keys             = {provider: None for provider in PROVIDERS.keys()}
current_provider     = None
current_model        = None
conversation_buffer  = []
last_called_ts       = 0
total_in             = 0
total_out            = 0
#g7h8i9-end

#j1k2l3-start
def traverse(data, path):
    """Walks a nested dict/list using a list of keys/indices as the path."""
    for key in path:
        data = data[key]
    return data
#j1k2l3-end

#m4n5o6-start
def set_provider():
    """Prompts user to select API provider from config."""
    global current_provider

    provider_list = list(PROVIDERS.keys())
    print("\nAvailable providers:")
    for i, provider in enumerate(provider_list, 1):
        print(f"  {i}. {provider}")

    try:
        choice = input("\nSelect provider number: ").strip()
        index  = int(choice) - 1

        if index < 0 or index >= len(provider_list):
            print("!-Invalid provider number-!")
            return

        current_provider = provider_list[index]

        if current_model:
            print(f"\n[CHAT - {current_provider.upper()}/{current_model}]")
        else:
            print(f"\n[CHAT - {current_provider.upper()}]")

    except ValueError:
        print("!-Invalid input-!")
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#m4n5o6-end

#p7q8r9-start
def set_model():
    """Prompts user to select model for current provider."""
    global current_model

    if current_provider is None:
        print("!-No provider selected. Use :set-provider first-!")
        return

    model_list = PROVIDERS[current_provider]["models"]
    print(f"\nAvailable models for {current_provider}:")
    for i, model in enumerate(model_list, 1):
        print(f"  {i}. {model}")

    try:
        choice = input("\nSelect model number: ").strip()
        index  = int(choice) - 1

        if index < 0 or index >= len(model_list):
            print("!-Invalid model number-!")
            return

        current_model = model_list[index]
        print(f"\n[CHAT - {current_provider.upper()}/{current_model}]")

    except ValueError:
        print("!-Invalid input-!")
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#p7q8r9-end

#s1t2u3-start
def set_api_key():
    """Prompts user to enter API key for current provider."""
    if current_provider is None:
        print("!-No provider selected. Use :set-provider first-!")
        return

    if current_provider == "local":
        print(f"!-No API key required for {current_provider}-!")
        return

    try:
        key = getpass.getpass(f"Enter API key for {current_provider}: ")
        api_keys[current_provider] = key
        print(f"API key stored for {current_provider}")

    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#s1t2u3-end

#v4w5x6-start
def api_key_check(provider):
    """Returns True if API key is set for provider, False otherwise."""
    return api_keys.get(provider) is not None
#v4w5x6-end

#b3c4d5-start
def check_rate_limit():
    """Returns True if rate limit allows next API call, False otherwise."""
    global last_called_ts

    if current_provider is None:
        return True

    config = PROVIDERS[current_provider]

    if "max_calls_per_minute" not in config or config["max_calls_per_minute"] is None:
        return True

    current_time    = time.time()
    time_since_last = current_time - last_called_ts
    min_interval    = 60.0 / config["max_calls_per_minute"]

    if time_since_last < min_interval:
        wait_time = min_interval - time_since_last
        print(f"!-Rate limit: Wait {wait_time:.1f}s-!")
        return False

    return True
#b3c4d5-end

#w8x9y1-start
def send_prompt(prompt):
    """Sends prompt with full conversation history to configured API."""
    global last_called_ts, total_in, total_out

    # Validate
    if current_provider is None:
        print("!-No provider selected-!")
        return
    if current_model is None:
        print("!-No model selected-!")
        return
    if current_provider != "local" and not api_key_check(current_provider):
        print("!-No API key configured-!")
        return
    if not check_rate_limit():
        return

    try:
        config = PROVIDERS[current_provider]

        # Build messages array inline from buffer
        messages = []
        for entry in conversation_buffer:
            messages.append({"role": "user",      "content": entry["prompt"]})
            messages.append({"role": "assistant",  "content": entry["text"]})
        messages.append({"role": "user", "content": prompt})

        # Build request body from config template
        request_body             = json.loads(json.dumps(config["request_format"]))
        request_body["model"]    = current_model
        request_body["messages"] = messages
        body_bytes               = json.dumps(request_body).encode("utf-8")

        # Build urllib request
        req = urllib.request.Request(
            config["url"],
            data=body_bytes,
            headers={"Content-Type": "application/json"}
        )

        if "optional_headers" in config:
            for k, v in config["optional_headers"].items():
                req.add_header(k, v)

        if config["auth_header"] is not None:
            auth_value = api_keys[current_provider]
            if "auth_prefix" in config:
                auth_value = config["auth_prefix"] + auth_value
            req.add_header(config["auth_header"], auth_value)

        # Send
        prompt_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        with urllib.request.urlopen(req) as response:
            response_json = json.loads(response.read().decode("utf-8"))

        response_time  = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        last_called_ts = time.time()

        # Extract via config paths
        text    = traverse(response_json, config["response_path"])
        in_tok  = traverse(response_json, config["input_token_path"])
        out_tok = traverse(response_json, config["output_token_path"])

        # Build clean entry
        entry = {
            "prompt":        prompt,
            "response":      response_json,
            "text":          text,
            "in_tok":        in_tok,
            "out_tok":       out_tok,
            "provider":      current_provider,
            "model":         current_model,
            "prompt_time":   prompt_time,
            "response_time": response_time
        }

        conversation_buffer.append(entry)
        total_in  += in_tok
        total_out += out_tok

        # Display
        buffer_index = len(conversation_buffer) - 1
        print("---output---")
        print(text)
        print(f"[exit: 0] buffer[{buffer_index}] [{current_provider}/{current_model}]")
        print(f"in:{in_tok} out:{out_tok}")
        print(f"total_in:{total_in} total_out:{total_out}")
        print(f"[{prompt_time} - {response_time}]")
        print("------------")
        print("\n")
        print("\n")
        print("\n")
        print("\n")

        return entry

    except urllib.error.HTTPError as e:
        print(f"!-HTTP Error {e.code}-!")
        print(e.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"!-Connection Error: {e.reason}-!")
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#w8x9y1-end

#r5t6u7-start
def show_buffer():
    """Displays conversation buffer with truncated prompts and responses."""
    if not conversation_buffer:
        print("!-Buffer empty-!")
        return

    for i, entry in enumerate(conversation_buffer):
        prompt = entry["prompt"][:30] + "..." if len(entry["prompt"]) > 30 else entry["prompt"]
        text   = entry["text"].replace("\n", " ")
        text   = text[:30] + "..." if len(text) > 30 else text
        print(f"[{i}] [{entry['provider']}/{entry['model']}] {prompt} | {text}")
#r5t6u7-end

#s4t5u6-start
def revert_command(user_input):
    """Reverts conversation buffer to specified index. Use -1 to clear all."""
    global conversation_buffer

    parts = user_input.split()

    if len(parts) != 2:
        print("!-Usage: :revert [index] | :revert -1 to clear all-!")
        return

    try:
        index = int(parts[1])
    except ValueError:
        print("!-Invalid index: must be integer-!")
        return

    if index == -1:
        conversation_buffer.clear()
        print("!-Buffer cleared-!")
        return

    if index < 0 or index >= len(conversation_buffer):
        print(f"!-Invalid index: must be -1 to clear all, or 0 to {len(conversation_buffer) - 1}-!")
        return

    del conversation_buffer[index + 1:]
    print(f"!-Context reverted to [{index}]-!")
#s4t5u6-end

#e8f9g1-start
def save_chat(filepath):
    """Saves conversation buffer to file in terminal display format."""
    if not conversation_buffer:
        return 1, "Buffer is empty"

    if "." not in os.path.basename(filepath):
        filepath += ".txt"

    try:
        with open(filepath, "w") as f:
            for i, entry in enumerate(conversation_buffer):
                f.write(entry["prompt"] + "\n")
                f.write("---output---\n")
                f.write(entry["text"] + "\n")
                f.write(f"[exit: 0] buffer[{i}] [{entry['provider']}/{entry['model']}]\n")
                f.write(f"in:{entry['in_tok']} out:{entry['out_tok']}\n")
                f.write(f"[{entry['prompt_time']} - {entry['response_time']}]\n\n")
        return 0, filepath

    except OSError as e:
        return 1, f"Failed to write file: {str(e)}"
#e8f9g1-end

#k2l3m4-start
CHAT_HELP = """CHAT.PY - AI CONVERSATION MODULE
=================================
Commands:
  :set-provider          Select API provider
  :set-model             Select model for current provider
  :set-key               Enter API key (masked, not needed for local)
  :buffer                Show conversation buffer
  :revert [index]        Clear buffer from index to end
  :revert -1             Clear entire buffer
  :save [filepath]       Export conversation buffer to file
  :quit                  Exit chat

Workflow:
  :set-provider → pick number
  :set-model    → pick number
  :set-key      → paste key (skip for local)
  Type prompt   → type EOF on its own line to send

[CHAT - PLEASE SET A PROVIDER]
"""

if __name__ == "__main__":
    print(CHAT_HELP)
    eof_array = []

    while True:
        try:
            user_input = input().strip()

            if not user_input:
                continue

            if   user_input == ":quit":
                break
            elif user_input == ":set-provider":
                set_provider()
            elif user_input == ":set-model":
                set_model()
            elif user_input == ":set-key":
                set_api_key()
                print("<<EOF")
                continue
            elif user_input == ":buffer":
                show_buffer()
            elif user_input.startswith(":revert "):
                revert_command(user_input)
            elif user_input.startswith(":save "):
                code, result = save_chat(user_input[6:].strip())
                if code == 0:
                    print(f"Saved to {result}")
                else:
                    print(f"!-{result}-!")
            elif user_input.startswith(":"):
                print(f"!-Unknown command: {user_input}-!")
            elif user_input == "EOF":
                if eof_array:
                    send_prompt("\n".join(eof_array))
                    eof_array.clear()
            else:
                eof_array.append(user_input)

            if not eof_array:
                print("<<EOF")

        except KeyboardInterrupt:
            if eof_array:
                eof_array.clear()
                print("\n!-Input cancelled-!")
            else:
                print("\n!-Use :quit to exit-!")
            print("<<EOF")
        except EOFError:
            break
#k2l3m4-end
