-- https://github.com/mistricky/codesnap.nvim
return {
  {
    "mistricky/codesnap.nvim",
    build = "make",
    opts = {
      save_path = "~/pictures",
      watermark = "",
    },
  },
}
