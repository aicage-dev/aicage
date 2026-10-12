# Internal: How-To produce screenshots

This **internal** document shows how to reproduce the screenshots.

I am on Nobara/Fedora, things might differ on other setups.

Open `konsole` and the wiki on Github. Resize `konsole` to width of wiki pages.

## Demo setup and cleanup

### Setup: Create demo user

```shell
sudo useradd -m demo
sudo usermod -aG docker demo
# copy to demo user home
sudo cp -r ~/.ssh /home/demo/
sudo cp -r ~/.gnupg /home/demo/
sudo cp -r ~/.gitconfig /home/demo/
sudo chown -R demo:demo /home/demo/.ssh
sudo chown -R demo:demo /home/demo/.gnupg
sudo chown -R demo:demo /home/demo/.gitconfig
```

### Setup: One time setup of demo user

```shell
# login as demo user
sudo -iu demo
```

then as demo user run:

```shell
# install aicage for demo user
pipx install aicage

# dummy host in bash prompt
export PROMPT_USERHOST='\u@my-fedora'
echo "PROMPT_USERHOST='\u@my-fedora'" >> ~/.bashrc

# setup project folder (use random small repo so ssh is used later)
git clone git@github.com:aicage/aicage-image-util.git ~/development/my-project

# exit demo user session
exit
```

### Cleanup: Remove demo user including his home

```shell
sudo userdel -r demo
```

## Screenshots

### First use screenshot with `--menu none`

> Optional: Prune Docker or remove images to screenshot image pulling

```shell
# login as demo user
sudo -iu demo
```

then as demo user run:

```shell
# cd to project folder
cd development/my-project/

# start agent codex in aicage
aicage --menu none codex

# exit demo user session
exit
```

### Second use screenshot with config questions

```shell
# login as demo user
sudo -iu demo
```

then as demo user run:

```shell
# cd to project folder
cd development/my-project/

# (optional) show config
# aicage --config info

# cleanup config
aicage --config remove

# start agent codex in aicage
aicage codex

# exit demo user session
exit
```
