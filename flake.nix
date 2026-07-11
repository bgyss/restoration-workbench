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
      devShells = forEachSystem (pkgs:
        let
          deepFilterCli = pkgs.deepfilternet.overrideAttrs (_old: {
            pname = "deep-filter";
            buildAndTestSubdir = "libDF";
            cargoBuildFeatures = "bin tract wav-utils transforms";
            cargoCheckFeatures = "bin tract wav-utils transforms";
            postInstall = "";
          });
        in {
        default = pkgs.mkShell {
          packages = with pkgs; [
            cargo
            clang
            deepFilterCli
            deepfilternet
            ffmpeg
            git
            mediainfo
            mise
            mkvtoolnix
            python312Packages.pytest
            ruff
            rustup
            sox
            uv
          ];

          shellHook = ''
            export UV_PROJECT_ENVIRONMENT="''${UV_PROJECT_ENVIRONMENT:-.venv}"
            export UV_CACHE_DIR="''${UV_CACHE_DIR:-.uv-cache}"
            export RUST_BACKTRACE="''${RUST_BACKTRACE:-1}"
            export LADSPA_PATH="${pkgs.deepfilternet}/lib/ladspa''${LADSPA_PATH:+:$LADSPA_PATH}"
            echo "VHS restoration shell: run 'mise run doctor' to verify tools."
          '';
          };
      });
    };
}
