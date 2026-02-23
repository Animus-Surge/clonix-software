{
  description = "egr-cloner tui implementation";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }: 
    (utils.lib.eachDefaultSystem (system:
      let 
        pkgs = import nixpkgs { inherit system; };

        clonix-bin = pkgs.stdenv.mkDerivation {
          pname = "clonix-bin";
          version = "0.2.0";
          src = ./.;

          nativeBuildInputs = [
            (pkgs.python313.withPackages (ps: with ps; [ urwid psutil nuitka ]))
            pkgs.ccache
          ];

          buildPhase = ''
            export HOME=$TMPDIR
            python3 -m nuitka --onefile --standalone main.py -o clonix-bin
          '';

          installPhase = ''
            mkdir -p $out/bin
            cp clonix-bin $out/bin/
          '';
        };
      in
      {
        packages = {
          default = clonix-bin;

          clonix-iso = self.nixosConfigurations.cloner.config.system.build.isoImage;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ (pkgs.python313.withPackages (ps: with ps; [ urwid psutil pyparted nuitka ] )) ];

          shellHook = ''
            echo "Entered clonix-bin development shell."
            echo "Available packages: urwid, psutil, pyparted, nuitka"
            '';
        };

        apps.default = {
          type = "app";
          program = "${clonix-bin}/bin/clonix-bin";
        };
      }
    ))
    // {
      nixosConfigurations.cloner = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          ({ modulesPath, ... }: {
            imports = [ "${modulesPath}/installer/cd-dvd/iso-image.nix" ];
          })

          ./cloner-config.nix

          {
            isoImage.makeEfiBootable = true;
            isoImage.makeUsbBootable = true;

            system.nixos.label = "clonix";
            isoImage.volumeID = "CLONIX";
          }
        ];
      };
    };
  
}
    
