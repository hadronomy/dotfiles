{ pkgs, ... }:
{
  enable = true;
  globalConfig.tools = {
    node = "lts";
    bun = "latest";
    deno = "latest";
  };
  settings.activate_aggresive = true;
}