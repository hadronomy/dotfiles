{ ... }:
{
  programs.hadronomy.macchina = {
    enable = true;
    theme = {
      spacing = 1;
      padding = 0;
      hide_ascii = false;
      prefer_small_ascii = true;
      separator = "λ";
      separator_color = "White";
      palette = {
        type = "Dark";
        visible = true;
        glyph = " ⬤ ";
      };
      box = {
        title = " hadronomy ";
        border = "rounded";
        visible = true;
        inner_margin = {
          x = 3;
          y = 1;
        };
      };
      randomize = {
        key_color = false;
        separator_color = false;
      };
      keys = {
        host = "User/Hostname";
        kernel = "Kernel";
        battery = "Battery Info";
        os = "Operating System";
        de = "Desktop Environment";
        wm = "Window Manager";
        distro = "Distribution";
        terminal = "Terminal Emulator";
        shell = "Shell";
        packages = "Packages (mgr)";
        uptime = "Uptime";
        memory = "Memory";
        machine = "Machine";
        local_ip = "Local IP";
        backlight = "Brightness";
        resolution = "Resolution";
        cpu_load = "CPU Load";
        cpu = "Processor (cores)";
        gpu = "Graphics Processor";
        disk_space = "Disk Space";
      };
    };
  };
}
