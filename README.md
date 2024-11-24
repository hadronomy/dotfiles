<div align="center">
  <img src="/.github/images/github-header-image.webp" alt="GitHub Header Image" width="auto" />
  
  <!-- MIT License -->
  <a href="https://github.com/hadronomy/dotfiles/blob/main/LICENSE.txt">
    <img
      alt="Content License"
      src="https://img.shields.io/github/license/hadronomy/dotfiles?style=for-the-badge&logo=starship&color=ee999f&logoColor=D9E0EE&labelColor=302D41"
    />
  </a>

  <!-- GitHub Repo Stars -->
  <a href="https://github.com/hadronomy/dotfiles/stargazers">
    <img
      alt="Stars"
      src="https://img.shields.io/github/stars/hadronomy/dotfiles?style=for-the-badge&logo=starship&color=c69ff5&logoColor=D9E0EE&labelColor=302D41"
    />
  </a>
  <p></p>
  <span>
    Just my dotfiles, nothing special.
  </span>
  <p></p>
  <a href="#requirements">Requirements</a> •
  <a href="#usage">Usage</a> •
  <a href="#license">License</a>
  <hr />

</div>

## Requirements

- [nix](https://nixos.org/)

> [!WARNING]
> For the **neovim** configuration to work the repository
> or must live in `~/.dotfiles`

## Usage

After clonning the repo `cd` into it and run the following command:

```bash
home-manager switch --flake . -b backup
```

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
