return {
  {
    "nvim-treesitter/nvim-treesitter",
    config = function()
      -- setup treesitter with config
    end,
    dependencies = {
      -- NOTE: additional parser
      {
        "nushell/tree-sitter-nu",
        ft = "nu",
      },
    },
    build = ":TSUpdate",
  },
}
