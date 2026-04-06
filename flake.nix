{
  description = "Nix-packaged multi-repo fleet triage and review tooling";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system:
          f {
            pkgs = import nixpkgs { inherit system; };
          });
    in
    {
      formatter = forAllSystems ({ pkgs }: pkgs.nixfmt-rfc-style);

      packages = forAllSystems ({ pkgs }: {
        default = pkgs.writeShellApplication {
          name = "repo-fleet";
          runtimeInputs = [ pkgs.python3 ];
          text = ''
            exec ${pkgs.python3}/bin/python ${./src/repo_fleet_cli.py} "$@"
          '';
        };
      });

      apps = forAllSystems ({ pkgs }: {
        default = {
          type = "app";
          program = "${self.packages.${pkgs.system}.default}/bin/repo-fleet";
        };
      });

      devShells = forAllSystems ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            git
            gh
            jq
            nixfmt-rfc-style
            python3
            ripgrep
          ];
        };
      });
    };
}
