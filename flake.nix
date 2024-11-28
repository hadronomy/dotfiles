{
  description = "hadronomy's nix home-manager config";

  inputs = {
    # Nixpkgs
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";

    # Home Manager
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Nix User Repository
    nur.url = "github:nix-community/NUR";

    nix-index-database = {
      url = "github:Mic92/nix-index-database";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    bash-env-json = {
      url = "github:tesujimath/bash-env-json/main";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    bash-env-nushell = {
      url = "github:tesujimath/bash-env-nushell/main";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.bash-env-json.follows = "bash-env-json";
    };

    catppuccin.url = "github:catppuccin/nix";
    mise.url = "github:jdx/mise";
  };

  outputs =
    { self, ... }@inputs:
    with inputs;
    let
      inherit (self) outputs;

      system = "x86_64-linux";
      systems = [
        "x86_64-linux"
      ];

      pkgs = import nixpkgs {
        system = "x86_64-linux";
        config = {
          allowUnfree = true;
          permittedInsecurePackages = [
            "electron-25.9.0"
          ];
        };
      };

      flakePkgs = {
        bash-env-json = bash-env-json.packages.${system}.default;
        bash-env-nushell = bash-env-nushell.packages.${system}.default;
        mise = mise.packages.${system}.default;
      };

      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt-rfc-style);

      overlays.additions = final: _prev: import ./packages final.pkgs;

      overlays.unstable = final: prev: {
        unstable = import nixpkgs-unstable {
          system = prev.system;
          config.allowUnfree = prev.config.allowUnfree;
        };
      };

      nixpkgs.overlays = [
        self.overlays.unstable
        nur.overlay
      ];

      packages = forAllSystems (system: import ./packages nixpkgs.legacyPackages.${system});

      homeConfigurations.hadronomy = home-manager.lib.homeManagerConfiguration {
        inherit pkgs;
        extraSpecialArgs = {
          inherit flakePkgs;
        } // inputs;

        modules = [
          ./home
          catppuccin.homeManagerModules.catppuccin
        ] ++ builtins.attrValues self.homeManagerModules;
      };

      homeManagerModules = builtins.listToAttrs (
        map (name: {
          inherit name;
          value = import (./modules/hm + "/${name}");
        }) (builtins.attrNames (builtins.readDir ./modules/hm))
      );

      devShells = forAllSystems (system: {
        inherit pkgs;
        default = pkgs.mkShellNoCC {
          buildInputs = with pkgs; [
            (writeScriptBin "dot-clean" ''
              nix-collect-garbage -d --delete-older-than 30d
            '')
            (writeScriptBin "dot-sync" ''
              git pull --rebase origin main
              nix flake update
              dot-clean
              dot-apply
            '')
            (writeScriptBin "dot-apply" ''
              if test $(uname -s) == "Linux"; then
                home-manager switch --flake .
              fi
            '')
          ];
        };
      });
    };
}
