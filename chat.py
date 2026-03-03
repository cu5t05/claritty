#!/usr/bin/env python3
"""
TABLE OF CONTENTS
=================
a1b2c3 = imports
d4e5f6 = config path
g7h8i9 = module variables
j1k2l3 = set_provider function
m4n5o6 = set_model function
p7q8r9 = set_api_key function
s1t2u3 = api_key_check function
v4w5x6 = send_prompt function
b3c4d5 = usage management
w8x9y1 = show_buffer
r5t6u7 = revert function
s4t5u6 = save_chat function
e8f9g1 = eof mode
y7z8a9 = entry point
"""

#a1b2c3-start
import os
import json
import getpass
import urllib.request
import urllib.parse
from datetime import datetime
#a1b2c3-end

#d4e5f6-start
CONFIG_PATH = "/Users/you/your-work-dir/wherever-has/config.json"
with open(CONFIG_PATH, "r") as f:
    _config = json.load(f)

PROVIDERS = _config["api_template"]
#d4e5f6-end

#g7h8i9-start
# Module variables
api_keys = {provider: None for provider in PROVIDERS.keys()}
current_provider = None
current_model = None
conversation_buffer = []
#g7h8i9-end

#j1k2l3-start
def set_provider():
    """Prompts user to select API provider from config"""
    global current_provider
    
    provider_list = list(PROVIDERS.keys())
    print("\nAvailable providers:")
    for i, provider in enumerate(provider_list, 1):
        print(f"{i}. {provider}")
    
    try:
        choice = input("\nSelect provider number: ").strip()
        index = int(choice) - 1
        
        if index < 0 or index >= len(provider_list):
            print("!-Invalid provider number-!")
            return
        
        current_provider = provider_list[index]
        
        # Display header with current settings
        if current_model:
            print(f"\n[CHAT - {current_provider.upper()}/{current_model}]")
        else:
            print(f"\n[CHAT - {current_provider.upper()}]")
    
    except ValueError:
        print("!-Invalid input-!")
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#j1k2l3-end

#m4n5o6-start
def set_model():
    """Prompts user to select model for current provider"""
    global current_model
    
    if current_provider is None:
        print("!-No provider selected. Use set_provider first-!")
        return
    
    model_list = PROVIDERS[current_provider]["models"]
    print(f"\nAvailable models for {current_provider}:")
    for i, model in enumerate(model_list, 1):
        print(f"{i}. {model}")
    
    try:
        choice = input("\nSelect model number: ").strip()
        index = int(choice) - 1
        
        if index < 0 or index >= len(model_list):
            print("!-Invalid model number-!")
            return
        
        current_model = model_list[index]
        print(f"\n[CHAT - {current_provider.upper()}/{current_model}]")
    
    except ValueError:
        print("!-Invalid input-!")
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#m4n5o6-end

#p7q8r9-start
def set_api_key():
    """Prompts user to enter API key for current provider"""
    if current_provider is None:
        print("!-No provider selected. Use set_provider first-!")
        return
    
    # Skip key prompt for llamacpp (no auth required)
    if current_provider == "llamacpp":
        print(f"!-No API key required for {current_provider}-!")
        return
    
    try:
        key = getpass.getpass(f"Enter API key for {current_provider}: ")
        api_keys[current_provider] = key
        print(f"API key stored for {current_provider}")
    
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#p7q8r9-end

#s1t2u3-start
def api_key_check(provider):
    """Returns True if API key is set for provider, False otherwise"""
    return api_keys.get(provider) is not None
#s1t2u3-end

#v4w5x6-start
def send_prompt(prompt):
    """Sends prompt to configured API and prints raw JSON response"""
    
    # Validate configuration
    if current_provider is None:
        print("!-No provider selected-!")
        return
    
    if current_model is None:
        print("!-No model selected-!")
        return
    
    # Check API key requirement
    if current_provider != "llamacpp" and not api_key_check(current_provider):
        print("!-No API key configured-!")
        return
    
    # Check rate limit
    if not check_rate_limit():
        return
    
    # Check token limit (warning only, doesn't block)
    check_token_limit()
    
    try:
        # Get provider config
        config = PROVIDERS[current_provider]
        
        # Build context messages from buffer
        context_messages = []
        for entry in conversation_buffer:
            # Add user message
            context_messages.append({
                "role": "user",
                "content": entry["prompt"]
            })
            
            # Extract and add assistant message
            response_json = entry["response"]
            response_text = ""
            if "content" in response_json and len(response_json["content"]) > 0:
                response_text = response_json["content"][0].get("text", "")
            
            context_messages.append({
                "role": "assistant",
                "content": response_text
            })
        
        # Add current prompt
        context_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Build request body with context
        request_body = json.loads(json.dumps(config["request_format"]))
        request_body["model"] = current_model
        request_body["messages"] = context_messages
        
        # Encode body to bytes
        body_bytes = json.dumps(request_body).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            config["url"],
            data=body_bytes,
            headers={'Content-Type': 'application/json'}
        )
        
        # Add optional headers if specified
        if "optional_headers" in config:
            for header_name, header_value in config["optional_headers"].items():
                req.add_header(header_name, header_value)
        
        # Add auth header if required
        if config["auth_header"] is not None:
            auth_value = api_keys[current_provider]
            if "auth_prefix" in config:
                auth_value = config["auth_prefix"] + auth_value
            req.add_header(config["auth_header"], auth_value)
        
        # Capture prompt timestamp
        prompt_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Send request
        with urllib.request.urlopen(req) as response:
            response_bytes = response.read()
            response_text = response_bytes.decode('utf-8')
            response_json = json.loads(response_text)
            
            # Capture response timestamp
            response_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

            # Update usage tracking
            update_usage(response_json)
            
            # Store exchange in buffer
            entry = {
                "prompt": prompt,
                "response": response_json,
                "prompt_time": prompt_time,
                "response_time": response_time
            }
            conversation_buffer.append(entry)

            ## Extract response text
            response_text = ""
            if "choices" in response_json:
                # OpenAI/llamacpp style
                try:
                    response_text = response_json["choices"][0]["message"]["content"]
                except Exception as e:
                    print("Response parse error (OpenAI):", e)
            elif "content" in response_json and isinstance(response_json["content"], list) and len(response_json["content"]) > 0:
                # Anthropic style
                try:
                    response_text = response_json["content"][0].get("text", "")
                except Exception as e:
                    print("Response parse error (Anthropic):", e)
            elif "error" in response_json:
                print("API Error:", response_json["error"].get("message", "Unknown error"))

            # Format and display response
            buffer_index = len(conversation_buffer) - 1
            print("---output---")
            print(response_text)
            print(f"[exit: 0] buffer[{buffer_index}]")
            print(f"[{entry['prompt_time']} - {entry['response_time']}]")
            print("------------")
            print("\n")

            return response_text
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"!-HTTP Error {e.code}-!")
        print(error_body)
    
    except urllib.error.URLError as e:
        print(f"!-Connection Error: {e.reason}-!")
    
    except KeyboardInterrupt:
        print("\n!-Cancelled-!")
#v4w5x6-end

#b3c4d5-start
# Usage management
import time

# Module variables for usage tracking
last_called_timestamp = 0
cumulative_tokens = 0
warning_shown = False

def check_rate_limit():
    """Checks if rate limit allows next API call"""
    global last_called_timestamp
    
    if current_provider is None:
        return True
    
    config = PROVIDERS[current_provider]
    
    # Skip rate limit check if not configured
    if "max_calls_per_minute" not in config or config["max_calls_per_minute"] is None:
        return True
    
    current_time = time.time()
    time_since_last = current_time - last_called_timestamp
    min_interval = 60.0 / config["max_calls_per_minute"]
    
    if time_since_last < min_interval:
        wait_time = min_interval - time_since_last
        print(f"!-Rate limit: Wait {wait_time:.1f} seconds-!")
        return False
    
    return True

def check_token_limit():
    """Checks token usage and shows warning if threshold exceeded"""
    global warning_shown
    
    if current_provider is None:
        return True
    
    config = PROVIDERS[current_provider]
    
    # Skip token limit check if not configured
    if "token_limit_warning" not in config or config["token_limit_warning"] is None:
        return True
    
    if cumulative_tokens >= config["token_limit_warning"] and not warning_shown:
        warning_shown = True
        print(f"!-Warning: Token limit reached ({cumulative_tokens} tokens)-!")
        print("Next call will proceed. Use responsibly.")
        return False
    
    if warning_shown:
        warning_shown = False
    
    return True

def update_usage(response_json):
    """Updates usage tracking after successful API call"""
    global last_called_timestamp, cumulative_tokens
    
    # Update timestamp
    last_called_timestamp = time.time()
    
    # Extract and accumulate tokens if available
    if "usage" in response_json and "output_tokens" in response_json["usage"]:
        output_tokens = response_json["usage"]["output_tokens"]
        cumulative_tokens += output_tokens
#b3c4d5-end

#w8x9y1-start
def show_buffer():
    """Displays conversation buffer with truncated prompts and responses"""
    if len(conversation_buffer) == 0:
        print("!-Buffer empty-!")
        return
    
    for i, entry in enumerate(conversation_buffer):
        prompt = entry["prompt"]
        if len(prompt) > 30:
            prompt = prompt[:30] + "..."
        
        # Extract response text from response_json
        response_json = entry["response"]
        response_text = ""
        if "content" in response_json and len(response_json["content"]) > 0:
            response_text = response_json["content"][0].get("text", "")
            response_text = response_text.replace("\n", " ")
            
        if len(response_text) > 30:
            response_text = response_text[:30] + "..."
        
        print(f"[{i}] {prompt} | {response_text}")
#w8x9y1-end

#r5t6u7-start
def revert_command(user_input):
    """Reverts conversation buffer to specified index"""
    global conversation_buffer
    
    parts = user_input.split()
    
    if len(parts) != 2:
        print("!-Usage: :revert [index]-!")
        return
    
    try:
        index = int(parts[1])
    except ValueError:
        print("!-Invalid index: must be integer-!")
        return
    
    if index < 0 or index >= len(conversation_buffer):
        print(f"!-Invalid index: must be 0 to {len(conversation_buffer) - 1}-!")
        return
    
    del conversation_buffer[index + 1:]
    print(f"!-Context reverted to [{index}]-!")
#r5t6u7-end

#s4t5u6-start
def save_chat(filepath):
    """Saves conversation buffer to file in terminal display format"""
    if not conversation_buffer:
        return 1, "Buffer is empty"
    
    # Append .txt if no extension provided
    if '.' not in os.path.basename(filepath):
        filepath = filepath + ".txt"
    
    try:
        with open(filepath, 'w') as f:
            for index, entry in enumerate(conversation_buffer):
                # Extract response text from stored JSON
                response_json = entry["response"]
                response_text = ""
                if "content" in response_json and len(response_json["content"]) > 0:
                    response_text = response_json["content"][0].get("text", "")
                
                # Write exchange in terminal display format
                f.write(entry["prompt"] + "\n")
                f.write("---output---\n")
                f.write(response_text + "\n")
                f.write(f"[exit: 0] buffer[{index}]\n")
                f.write(f"[{entry['prompt_time']} - {entry['response_time']}]\n")
                f.write("\n\n")
        
        return 0, filepath
    
    except OSError as e:
        return 1, f"Failed to write file: {str(e)}"
#s4t5u6-end

#e8f9g1-start
def handle_eof(user_input, eof_mode, eof_array):
    if "<<EOF" in user_input:
        parts = user_input.split("<<EOF", 1)
        if parts[0].strip():
            eof_array.append(parts[0].strip())
        return True, eof_array, None

    if eof_mode:
        if user_input == "EOF":
            prompt = "\n".join(eof_array)
            eof_array.clear()
            return False, eof_array, prompt
        else:
            eof_array.append(user_input)
            return True, eof_array, None

    return False, eof_array, user_input
#e8f9g1-end

#y7z8a9-start
CHAT_HELP = """CHAT.PY - AI CONVERSATION MODULE
Commands:
:set-provider - Select API provider (anthropic/openai/llamacpp)
:set-model - Select model from current provider
:set-key - Enter API key (hidden input, not needed for llamacpp)
:buffer - Show conversation buffer indices
:revert [index] - Clear buffer from index to end
:save [filepath] - Export conversation buffer to file
:shell - Return to shell
Workflow:
Run :set-provider and pick a number
Run :set-model and pick a number
Run :set-key and paste your API key (or skip for llamacpp)
Type your prompt and press enter
For multiline input, type <<EOF, paste content, then EOF on its own line
Any text without colon prefix sends as prompt to API.
[CHAT - PLEASE SET A PROVIDER]"""

if __name__ == "__main__":
    print(CHAT_HELP)
    eof_mode = False
    eof_array = []

    while True:
        try:
            user_input = input().strip()

            if user_input == ":quit":
                break
            elif user_input == ":set-provider":
                set_provider()
            elif user_input == ":set-model":
                set_model()
            elif user_input == ":set-key":
                set_api_key()
            elif user_input == ":buffer":
                show_buffer()
            elif user_input.startswith(":revert "):
                revert_command(user_input)
            elif user_input.startswith(":"):
                print(f"!-Unknown command: {user_input}-!")
            else:
                eof_mode, eof_array, prompt = handle_eof(user_input, eof_mode, eof_array)
                if prompt is not None:
                    send_prompt(prompt)

        except KeyboardInterrupt:
            if eof_mode:
                print("\n!-EOF collection cancelled-!")
                eof_array.clear()
                eof_mode = False
            else:
                print("\n!-Use :quit to exit-!")
        except EOFError:
            break
#y7z8a9-end