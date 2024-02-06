{
  description = "A very basic flake";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem( system:
      let 
        pkgs = import nixpkgs { inherit system; };
      in
      with pkgs; {
        devShells.default = mkShell {
          packages = [
            pulumi
            poetry
            python3
            awscli2

            terraform-ls
            zellij
          ];
      };}
    );
}
