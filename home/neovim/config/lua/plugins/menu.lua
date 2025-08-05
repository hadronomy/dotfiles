return {
  { "nvzone/volt", lazy = true },
  {
    "nvzone/menu",
    lazy = true,
    keys = {
      {
        "<leader>m",
        function()
          require("menu").open("default")
        end,
        desc = "Open Menu",
      },
    }
  },
}
