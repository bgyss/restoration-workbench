{
  description = "VHS restoration toolchain";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forEachSystem = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      }));
    in {
      devShells = forEachSystem (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            cargo
            clang
            ffmpeg-full
            git
            mediainfo
            mise
            mkvtoolnix
            rustup
            sox
            uv
          ];

          shellHook = ''
            export UV_PROJECT_ENVIRONMENT="''${UV_PROJECT_ENVIRONMENT:-.venv}"
            export UV_CACHE_DIR="''${UV_CACHE_DIR:-.uv-cache}"
            export RUST_BACKTRACE="''${RUST_BACKTRACE:-1}"
            echo "VHS restoration shell: run 'mise run doctor' to verify tools."
          '';
        };
      });
    };
}

