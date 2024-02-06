#!/bin/bash
echo "ec2-user ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ec2-user

# install nix package manager and skip conform
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --no-confirm

. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

# clone repo
nix profile install nixpkgs#git

git clone https://github.com/DeusFerrariis/rust-todo-api-server.git 

cd rust-todo-api-server

echo "
  [global]
  address = \"0.0.0.0\"
  port=80
" > Rocket.toml

# add port config
ROCKET_PORT=80

# start server
nix develop --command cargo run
