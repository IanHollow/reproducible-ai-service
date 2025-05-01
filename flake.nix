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
            python-pkg = pkgs.python312;

          in
          pkgs.mkShell {
            buildInputs = [
              # Python
              (python-pkg.withPackages (
                ps: with ps; [
                  pip
                  black

                  fastapi
                  uvicorn
                  uvicorn.optional-dependencies.standard
                  transformers
                  torch
                  python-dotenv
                  huggingface-hub
                  huggingface-hub.optional-dependencies.hf_xet
                  prometheus-client
                  jinja2
                  slowapi
                  pytest
                  httpx
                ]
              ))

              # Docker/Podman
              pkgs.podman
            ];
          };
      });
    };
}
