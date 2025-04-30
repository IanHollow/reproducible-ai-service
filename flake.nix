{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
  };
  outputs =
    { nixpkgs, systems, ... }@inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      devShells = forEachSystem (system: {
        default =
          let
            pkgs = import nixpkgs {
              inherit system;
              config = {
                allowUnfree = true;
              };
            };

            # define python with packages
            python-pkg = pkgs.python3;
            my-python = python-pkg.withPackages (
              ps: with ps; [
                pip
                black

                fastapi
                uvicorn
                transformers
                torch
              ]
            );

            # Make a library path
            lib-path = pkgs.lib.makeLibraryPath (
              with pkgs;
              [
                stdenv.cc.cc.lib # libstdc++.so.6
                zlib # libz.so.1
              ]
            );
          in
          pkgs.mkShell {
            buildInputs = [
              # Python
              my-python
            ];

            shellHook = ''
              # Augment the dynamic linker path
              export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:${lib-path}"

              # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
              # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
              export PIP_PREFIX=$(${pkgs.coreutils}/bin/pwd)/_build/pip_packages
              export PYTHONPATH="$PIP_PREFIX/${my-python.sitePackages}:${my-python}/${my-python.sitePackages}:$PYTHONPATH"
              export PATH="$PIP_PREFIX/bin:$PATH"
              unset SOURCE_DATE_EPOCH

              pip install -r requirements.txt
            '';
          };
      });
    };
}
