{ lib, config, ... }:
with lib;
let
  isWSL = builtins.getEnv "WSL_DISTRO_NAME" != "";
  disableSSHAgent = config.extraSpecialArgs.disableCustomSSHAgent or false;
in
{
  # TODO: Improve this with home-manager modules adding the wslConfig option to the git module
  # something like what catppuccin/nix does
  programs.git = {
    enable = true;
    ignores = import ./gitignore_global.nix;
    iniContent = {
      gpg = {
        format = mkForce "ssh";
      };
    };
    extraConfig = {
      user = {
        name = "Pablo Hernández";
        email = "17086478+hadronomy@users.noreply.github.com";
        signingkey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP7/sbN2cf0osvvjA7Z0+ymkcsO6mdnrPMe4drvM5lGa";
      };
      core = {
        editor = "nvim";
        autocrlf = "input";
        sshCommand = mkIf (isWSL) "ssh.exe";
        attributesFile = "~/.gitattributes";
      };
      init = {
        defaultBranch = "main";
      };
      gpg.ssh = mkIf (!disableSSHAgent) (
        if isWSL then
        {
          program = "/mnt/c/Users/pablo/AppData/Local/1Password/app/8/op-ssh-sign-wsl";
        }
        else
        {
          program = "/opt/1Password/op-ssh-sign";
        }
      );
      commit = {
        gpgsign = true;
      };
      merge = {
        conflictstyle = "diff3";
      };
      diff = {
        colorMoved = "default";
      };
      filter = {
        lfs = {
          clean = "git-lfs clean -- %f";
          smudge = "git-lfs smudge -- %f";
          process = "git-lfs filter-process";
          required = true;
        };
      };
    };
    delta = {
      enable = true;
      options = {
        navigate = true;
        sideBySide = true;
        lineNumbers = true;
        hyperlinks = true;
        hyperlinksFileLinkFormat = mkIf (isWSL) "vscode://file//wsl.localhost/Arch{path}:{line}";
        dark = true;
      };
    };
    aliases = {
      fixup = "!git log -n 50 --pretty=format:\"%h %s\" --no-merges | fzf | cut -c -7 | xargs -o git commit --fixup";
      squash-all = "!f(){ git reset $(git commit-tree \"HEAD^{tree}\" \"$@\");};f";
    };
  };
}
