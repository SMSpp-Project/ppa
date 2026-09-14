# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The packaging carries no version of its own: every section here is named
after the release of the umbrella whose packages it built.

## [Unreleased]

### Added

### Changed

### Fixed

## [0.6.2] - 2026-09-13

### Added

- the job of the tag builds, signs and uploads by itself: it takes the key
  from the file variable `PPA_GPG_KEY`, tells the signature which one to use
  with `SMSPP_SIGN_KEY`, since the key of the CI does not carry the name of
  the maintainer that `dpkg-buildpackage` would look for, and configures gpg
  with the loopback, having no terminal in a container

### Changed

- the install of each module goes through `DESTDIR` and not through
  `--prefix`, which the link that carries the name a tool had before the
  prefix needs, that one being made of the directory of the configure

### Fixed

- the image of the job installs `debhelper`, which `debian/rules clean`
  calls before anything else

- no pipeline is made for a push that carries no version, and the
  fingerprint of the key is read without the colon that broke the YAML

## [0.6.1] - 2026-09-13

### Added

- a second upload of the same version to the PPA bumps a number of its own,
  `SMSPP_PPA_BUILD`, and leaves the original tarballs out of it, the archive
  having them already

## [0.6.0] - 2026-09-13

### Added

- the packaging of the project: one build of the umbrella split into 61
  binary packages, a library and a `-dev` for each module, a command for each
  tool, `smspp-project` for all of them, and the two projects that
  MCFClassSolver and BundleSolver wrap in packages of their own

- `gen_debian.py`, whose tables hold the modules, the tools and their
  dependencies, and which writes `debian/control` and the tables that
  `debian/rules` reads

- `mk-ppa-source`, which takes the release tarball and FastFlow at the commit
  the other packages of the project pin, builds the source package for a
  series and uploads it to `ppa:smspp/ppa`
