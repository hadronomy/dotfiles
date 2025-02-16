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
> must live in `~/.dotfiles`

## Usage

There are two primary ways to apply this configuration. The first method is recommended for most users as it handles Home Manager installation if needed.

### 1. Using the Installation Script (Recommended)

This method uses a simple shell script to ensure Home Manager is installed and then applies the configuration directly from GitHub.

1.  **Download and run the installation script:**

    ```bash
    curl -L https://raw.githubusercontent.com/hadronomy/dotfiles/main/install.sh | bash
    ```

    **Important:** Replace `hadronomy/dotfiles` with your repository URL.

    This script will:

    *   Check if Home Manager is installed. If not, it will install it.
    *   Clone the dotfiles repository to `~/.dotfiles` (if it doesn't already exist).
    *   Run `home-manager switch --flake ~/.dotfiles -b backup --impure`.

    **Security Note:** It's always a good practice to review the contents of a script before running it, especially when piping directly from the internet. You can view the script at the URL provided.

### 2. Cloning and Applying Locally

If you prefer to clone the repository manually, you can do so and then apply the configuration.

1.  Clone the repository:

    ```bash
    git clone https://github.com/hadronomy/dotfiles ~/.dotfiles # Replace with your repository URL
    cd ~/.dotfiles
    ```

2.  Apply the Home Manager configuration:

    ```bash
    home-manager switch --flake . -b backup --impure
    ```

### Development

To enter a development shell with the tools needed to manage the dotfiles:

```bash
nix develop
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.
