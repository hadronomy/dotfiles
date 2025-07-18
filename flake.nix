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

      # NOTE: Change this to $HOME
      dotfilesDir = "/home/hadronomy/.dotfiles";

      repoUrl = "https://github.com/hadronomy/dotfiles";
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

      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          cloneDotfiles = pkgs.writeShellScriptBin "clone-dotfiles"
            ''
              if [ ! -d "${dotfilesDir}" ]; then
                echo "Cloning dotfiles repository..."
                mkdir -p $(dirname "${dotfilesDir}")
                git clone --depth 1 ${repoUrl} "${dotfilesDir}"
              else
                echo "Dotfiles repository already exists."
              fi
            '';

          apply = pkgs.writeShellScriptBin "apply-dotfiles"
            ''
              ${self.packages.${system}.cloneDotfiles}/bin/clone-dotfiles
              home-manager switch --flake ${dotfilesDir} -b backup --impure
            '';
        });

      defaultPackage = forAllSystems (system: self.packages.${system}.apply);

      homeConfigurations.hadronomy = home-manager.lib.homeManagerConfiguration {
        inherit pkgs;
        extraSpecialArgs = {
          inherit flakePkgs;
          disableCustomSSHAgent = false;
        } // inputs;

        modules = [
          ./home
          catppuccin.homeModules.catppuccin
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
            self.packages.${system}.apply
            (writeScriptBin "dot-clean" ''
              nix-collect-garbage -d --delete-older-than 30d
            '')
            (writeScriptBin "dot-sync" ''
              cd "${dotfilesDir}"
              git pull --rebase origin main
              nix flake update
              dot-clean
              dot-apply
            '')
            (writeScriptBin "dot-apply" ''
              ${self.packages.${system}.apply}/bin/apply-dotfiles
            '')
          ];
        };
      });
    };
}
