## CloNIX flake.nix
# Author: Evan Floyd (Surge)
# Version: v1.2
#
# Defines nixos based generations for development shell and live iso environment

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

        pythonDeps = [ "urwid" "psutil" "httpx" "nuitka" ];
        pythonEnv = pkgs.python313.withPackages (ps: map (name: ps.${name}) pythonDeps);

        # Generated binary file
        clonix-bin = pkgs.stdenv.mkDerivation {
          pname = "clonix-bin";
          version = "0.2.0";
          src = ./.;

          nativeBuildInputs = [
            pythonEnv
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

        # Requirements file generator, to allow for development on other machines
        genRequirements = pkgs.writeShellScriptBin "gen-requirements" ''
          echo "I: Generating requirements.txt..."
          echo "${nixpkgs.lib.concatStringsSep "\n" pythonDeps}" > requirements.txt
          echo "I: Done."
        '';
      in
      {
        packages = {
          default = clonix-bin;

          clonix-iso = self.nixosConfigurations.cloner.config.system.build.isoImage;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];

          shellHook = ''
            echo "Entered clonix-bin development shell."
            echo "Available packages: urwid, psutil, pyparted, httpx, nuitka"
            ${genRequirements}/bin/gen-requirements
            '';
        };

        apps.default = {
          type = "app";
          program = "${clonix-bin}/bin/clonix-bin";
        };
      }
    ))
    // {
      # Following block creates the live ISO
      nixosConfigurations.cloner = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          ({ modulesPath, ... }: {
            imports = [ "${modulesPath}/installer/cd-dvd/iso-image.nix" ];
          })

          ./clonix-iso.nix

          # TODO: write binary and config file to the iso

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
    
