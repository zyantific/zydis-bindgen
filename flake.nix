{
  description = "zydis-bindgen dev shell";

  outputs = { self, nixpkgs }: let
    systems = [ "aarch64-linux" "x86_64-linux" "aarch64-darwin" "x86_64-darwin" ];
    forEachSystem = subkey: perSysClosure: builtins.listToAttrs (builtins.map (system: { 
      name = system; 
      value = perSysClosure system; 
    }) systems);

    shellForSystem = system: let
      pkgs = import nixpkgs { inherit system; };
      lib = pkgs.lib;
    in pkgs.mkShell {
      packages = [ (pkgs.python3.withPackages (p: [ p.libclang ])) ];
    };
  in {
    devShell = forEachSystem "default" shellForSystem;
  };
}
