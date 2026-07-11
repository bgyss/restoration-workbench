# MCP integration boundary

`comfyui_restoration.stdio_server` is a minimal local transport for a future MCP adapter. It
accepts one JSON request per line and returns one structured response per line. An MCP server can
wrap this process, expose the operation schemas from `comfyui_restoration.agent.OPERATIONS`, and
retain its own authentication/session policy without importing ComfyUI internals.

The transport does not expose shell execution, Python evaluation, network fetches, model downloads,
node installation, or publication. The service still enforces workspace containment, idempotency,
candidate hashes, and a recorded visual human review before full execution. Secure signed
attestation is a future stretch goal. Run it with a dedicated workspace:

```sh
python scripts/agent_stdio.py /path/to/restricted-workspace
```

The workspace path is an operator configuration, not a workflow-supplied executable or command.
