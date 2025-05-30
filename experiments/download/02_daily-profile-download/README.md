# Notes


## config

- target device is pixel 8 running `BP1A.250305.019`, maps to `android-15.0.0_r20` according to <https://source.android.com/docs/setup/reference/build-numbers>
    - in `device.properties` as `sp_pixel8`
- apkeep with patches available in PATH as `apkeep-fork`
- target folder is: `/mnt/SecPrivSt1/playstorescraper/2025-03-aot-scrapes`

## general setup notes

```console
# install convenience functions
$ sudo apt install trash-cli direnv neovim build-essential tmux parallel btop libssl-dev sshfs pkg-config

# set up convenience (vimplug for .config/nvim)
$ sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
       https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
# then run :PlugInstall in nvim
$ nvim 

# install rust and tools
$ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
$ cargo install du-dust just lsd tealdeer choose hx cargo-updater

# install uv for python
$ curl -LsSf https://astral.sh/uv/install.sh | sh

# set up keys and makefile for mounting the storage server
$ sudo mkdir -p /mnt/SecPrivSt1/playstorescraper
$ sudo mkdir -p /mnt/SecPrivSt1/oatmeal
$ sudo chown -R jakob:jakob /mnt/SecPrivSt1/
```
