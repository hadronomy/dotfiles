{ pkgs, ...}:
let
  email = "17086478+Hadronomy@users.noreply.github.com";
  name = "Pablo Hernández";
in {
  programs.git = {
    enable = true;
    extraConfig = {
      color.ui = true;
      core.editor = "nvim";
      core.autocrlf = "input";
      credential.helper = "store";
      github.user = name;
      push.autoSetupRemote = true;
      init.defaultBranch = "main";
      # ssh signing
      user.signingkey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP7/sbN2cf0osvvjA7Z0+ymkcsO6mdnrPMe4drvM5lGa";
      gpg.format = "ssh";
      commit.gpgsign = true;
      gpg."ssh".program = "${pkgs._1password-gui}/bin/op-ssh-sign";
    };
    userEmail = email;
    userName = name;
  };
}