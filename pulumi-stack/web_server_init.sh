#!/bin/bash
echo "ec2-user ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ec2-user

echo "initializing nix"
# install nix package manager and skip conform
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --no-confirm

. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

# clone repo
echo "cloning web server repo"
nix profile install nixpkgs#git

git clone https://github.com/DeusFerrariis/rust-todo-web-app.git

cd rust-todo-web-app

export PUBLIC_TODO_API_URL=<API_URL>
export PORT=80

# build server
echo "building server"
nix develop --command npm install
nix develop --command npm run build

# prep server for run
cp package.json ./build/package.json
cp package-lock.json ./build/package-lock.json
nix develop --command npm ci --omit dev
cd build
nix develop --command npm install --omit dev
cd ..

# start server
echo "Starting web server"
nix develop --command node build
