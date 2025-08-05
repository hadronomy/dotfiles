{ pkgs, ... }:
{
  programs.gh = {
    enable = true;
    settings = {
      aliases = {
        clone = "repo clone";
        co = "pr checkout";
        v = "repo view --web";
        pv = "pr view --web";
        pr = "pr create --web";
      };
      editor = "nvim";
      git_protocol = "ssh";
    };
    extensions = with pkgs; [
      gh-dash
    ];
  };
}
