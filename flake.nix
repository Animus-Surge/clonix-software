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

    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, utils, nixos-generators }: 
    (utils.lib.eachDefaultSystem (system:
      let 
        pkgs = import nixpkgs { inherit system; };

        pythonDeps = [ "urwid" "psutil" "httpx" "nuitka" "qrcode" "fusepy" "pytest" ];
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
          CURRENT_DEPS="${nixpkgs.lib.concatStringsSep "\n" pythonDeps}"

          if [ ! -f requirements.txt ]; then
            echo "I: Generating requirements.txt..."
            echo "$CURRENT_DEPS" > requirements.txt
            echo "I: Done."
          else
            if ! echo "$CURRENT_DEPS" | cmp -s - requirements.txt; then
              echo "I: Generating requirements.txt..."
              echo "$CURRENT_DEPS" > requirements.txt
              echo "I: Done."
            fi
          fi
        '';
      in
      {
        packages = {
          default = clonix-bin;

          clonix-iso = self.clonix-iso.config.system.build.isoImage;
          clonix-pxe = pkgs.symlinkJoin {
            name = "clonix-pxe";
            paths = with self.clonix-pxe.config.system.build; [
              netbootRamdisk
              kernel
              netbootIpxeScript
            ];
          };
          clonix-uki = self.clonix-pxe.config.system.build.uki;

          clonix-img = self.clonix-img;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];

          packages = with pkgs; [
            sbsigntool
            openssl
            mokutil ];

          shellHook = ''
            echo "Entered clonix-bin development shell."
            ${genRequirements}/bin/gen-requirements
            echo "Available packages: ${nixpkgs.lib.concatStringsSep ", " pythonDeps}"
            echo "Available tools: sbsign, mokutil, openssl"
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
      clonix-iso = nixpkgs.lib.nixosSystem {
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

      clonix-pxe = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          ({ pkgs, modulesPath, ... }: {

            imports = [ "${modulesPath}/installer/netboot/netboot-minimal.nix" ];
          })
          ./clonix-iso.nix
        ];
      };

      clonix-img = nixos-generators.nixosGenerate {
        system = "x86_64-linux";

        format = "raw-efi";

        modules = [
          ./clonix-iso.nix
        ];
      };
    };
  
}
    
