{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "drop-rss";
  src = ./.;
  version = "0.1";
  propagatedBuildInputs = with pkgs.python3Packages; [ beautifulsoup4 requests feedgen ];
}
