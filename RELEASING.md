# Releasing

Default branch: `master`.

## Check and package

After editing `assets/starter/system/tokens.json`, regenerate its CSS; the
self-tests fail on a stale `tokens.css`, a failing contrast pair or any lint
error in the starter:

```sh
python -B scripts/pfui.py tokens build assets/starter/system/tokens.json --out assets/starter/system --format css
```

```sh
python -B scripts/validate_skill.py --skill-dir .
python -B tests/run_all.py --report ../validation.json
python -B scripts/package_skill.py --source . --tag v3.0.0 --output ../prototype-first-ui.zip
```

## Publish

Set `metadata.version` in `SKILL.md` and add the matching entry to `CHANGELOG.md`.
Commit the changes, then push the branch and version tag:

```sh
git push origin master
git tag -a v3.0.0 -m "Release v3.0.0"
git push origin v3.0.0
```

[GitHub Actions](.github/workflows/ci.yml) tests the extracted package and publishes
its ZIP, SHA-256 checksum, and test reports when all checks pass.
