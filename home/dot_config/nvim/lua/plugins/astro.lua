return {
  {
    "echasnovski/mini.icons",
    opts = {
      file = {
        [".astro"] = { glyph = "", hl = "MiniIconsOrange" },
      },
    },
  },
  {
    "nvim-treesitter/nvim-treesitter",
    opts = {
      ensure_installed = {
        "astro",
        "typescript",
        "tsx",
        "javascript",
        "markdown",
      },
    },
  },
}
