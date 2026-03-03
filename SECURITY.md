# Security Policy

## Reporting a Vulnerability

Do not open a public GitHub issue for security vulnerabilities. Public disclosure before a fix is available puts all users at risk.

Report vulnerabilities privately through one of the following:

- GitHub: Contact the maintainer directly via GitHub profile
- LinkedIn: linkedin.com/in/cu5t05

Include in your report:

- A clear description of the vulnerability
- Steps to reproduce it
- Your assessment of the impact and severity
- Any proposed fix if you have one

You will receive acknowledgment as quickly as possible. Given this is a single-maintainer project, response times may vary but all reports are taken seriously.

---

## Scope

The following are in scope for security reports:

- Execution model bypasses — any path that allows code to execute without passing through the consent gate
- Whitelist circumvention — any technique that allows a non-whitelisted command or flag to execute
- Path validation bypasses — any technique that allows file operations outside whitelisted directories
- Hash verification bypasses — any technique that allows an action to execute with a mismatched or absent hash
- Injection vectors — any input that reaches subprocess without proper validation
- Session data leakage — any path by which API keys, conversation content, or command output is persisted or transmitted unexpectedly

---

## Out of Scope

- Social engineering attacks on the human operator
- Vulnerabilities in AI provider APIs (Anthropic, OpenAI, llama.cpp)
- OS-level vulnerabilities unrelated to Claritty's execution model
- Issues requiring physical access to the machine

---

## Disclosure Policy

Once a fix is available and released, coordinated public disclosure is encouraged. Credit will be given to the reporter unless anonymity is requested.
