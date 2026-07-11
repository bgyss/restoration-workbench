# Threat model

The workbench handles user-selected media and optional third-party model code. The source is
immutable and is never used as an output directory. The primary assets are source bytes, derived
media, approval decisions, model provenance, and private paths.

Controls in the core are: resolved allowlisted workspaces, symlink/traversal rejection, explicit
argument arrays, no workflow-supplied executables, deterministic candidate hashes, persisted
chunk state, collision refusal, and a separate human approval object. Future network/model
installation operations must remain outside the media execution API and require explicit user
authorization.

Residual risks include malicious codecs, resource exhaustion, compromised optional model
environments, and an untrusted ComfyUI host. Run media tools in a constrained process/container,
set file/time/resource limits, keep optional adapters out of the base environment, and treat model
outputs as experimental until sample review passes.

