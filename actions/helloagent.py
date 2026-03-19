import sys
import json
import urllib.request

context = json.loads(sys.argv[1])

request_body = json.loads(json.dumps(context["request_format"]))
request_body["model"] = context["model"]
request_body["messages"] = [{"role": "user", "content": "hi"}]
body_bytes = json.dumps(request_body).encode("utf-8")

req = urllib.request.Request(
    context["endpoint"],
    data=body_bytes,
    headers={"Content-Type": "application/json"}
)

if context["auth_header"]:
    auth_value = context["key"]
    if context["auth_prefix"]:
        auth_value = context["auth_prefix"] + auth_value
    req.add_header(context["auth_header"], auth_value)

with urllib.request.urlopen(req) as response:
    response_json = json.loads(response.read().decode("utf-8"))

def traverse(data, path):
    for key in path:
        data = data[key]
    return data
in_tok = traverse(response_json, context["input_token_path"])
out_tok = traverse(response_json, context["output_token_path"])

text = traverse(response_json, context["response_path"])
print("---output---")
print(f"provider: {context['provider']}")
print(f"model:    {context['model']}")
print(f"in:{in_tok} out:{out_tok}")
print(f"response: {text}")