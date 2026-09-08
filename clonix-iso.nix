{ lib, pkgs, ... }:

{
  imports = [];

  users.mutableUsers = false;
  users.users = {
    "tech" = {
      isNormalUser = true;
      password = "";
      uid = 1000;
      extraGroups = [ "systemd-journal" "wheel" ];
    };
  };

  # SSH
  services.openssh = {
    enable = true;
    settings.PermitRootLogin = lib.mkForce "prohibit-password";
  };

  # Other services
  services.kmscon.enable = true; # Allow full color and UTF-8 support
  services.kmscon.fonts = [
    { name = "Hack Nerd Font"; package = pkgs.nerd-fonts.hack; }
  ];
  services.kmscon.extraConfig = ''
    font-engine=unifont
    palette=legacy
    font-name=AdwaitaMono Nerd Font
  '';

  services.ntp = {
    enable = true;
    servers = [ "" ]; # Can be configured somehow else, maybe with the flake? Should be able to be configured by the end user
  };

  environment.systemPackages = with pkgs; [
    # System requirements
    git
    btop
    tree
    vim
    
    # Required for clone system
    curl wget
    cryptsetup
    parted
    util-linux

    # Compression and stream tools
    gnutar pv zstd
  ];

  fileSystems."/nix/.rw-store" = {
    fsType = "tmpfs";
    options = [ "mode=0755" "nosuid" "nodev" "relatime" "size=8G" ];
    neededForBoot = true;
  };

  time.timeZone = lib.mkDefault "America/New_York";
  i18n.defaultLocale = "en_US.UTF-8";

  system.stateVersion = "25.05";

}
