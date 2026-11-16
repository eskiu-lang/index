<p align="center">
  <img src="https://raw.githubusercontent.com/eskiu-lang/eskiu/main/assets/logo.png" alt="Eskiu" width="120">
</p>

<h3 align="center">The Eskiu package index</h3>

<p align="center">
  Every published Eskiu package, from anyone.
  <br>
  <a href="https://eskiu-lang.org/packages.html">Package catalog</a> ·
  <a href="https://github.com/eskiu-lang/eskiu">The language</a> ·
  <a href="https://github.com/eskiu-packages">eskiu-packages</a>
</p>

---

A package's code stays in its own repository. The index holds one small file per package
that says where it is and what it does, so people and tools can find it: the
[package catalog](https://eskiu-lang.org/packages.html) and the Eskiu MCP read it. The
packages the project maintains are in [eskiu-packages](https://github.com/eskiu-packages);
they are listed here the same way as anyone else's.

Adding a package to a project does not need the index:

```bash
eskiuc add NAME --git https://github.com/OWNER/REPO --rev v0.1.0
```

## Publishing a package

1. Make the package: a public git repository with an `eskiu.toml` whose `[package]` has the
   name (`eskiuc new NAME` writes one). Document its API in the README or `docs/`.
2. Tag a release: `git tag v0.1.0 && git push --tags`. Versions are the repository's
   `vX.Y.Z` tags; a new release needs no change here.
3. Open a pull request here that adds `packages/NAME.toml`:

   ```toml
   name = "mything"
   git = "https://github.com/you/mything"
   description = "What it does, in one line"
   license = "MIT"
   keywords = ["parsing", "json"]
   maintainers = ["you"]
   ```

The check on the pull request (`tools/check.py --remote`) reads the repository: it must be
public, have a `vX.Y.Z` tag, and name the package `NAME` in `eskiu.toml` at that tag.

## The rules

- **Names are first come, first served** and match `eskiu.toml`: lower-case letters, digits
  and `_`, starting with a letter. The file is `packages/NAME.toml`.
- **One entry per repository**, and the entry points at the repository its maintainers own.
- `name`, `git`, `description` (up to 160 characters) and `license` (an SPDX id) are
  required; `keywords` (up to 8), `maintainers` (GitHub users or organizations) and
  `homepage` are optional.
- A maintainer changes or removes an entry with a pull request. An entry whose repository
  disappears, or that impersonates another project, is removed.

## For tools

`python3 tools/check.py --json` prints the whole index as JSON, with each package's latest
tag when run with `--remote`.

## License

The index data is MIT; each package has its own license, given in its entry.
