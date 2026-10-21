# Test and publish a release

The repository already uses Trusted Publishing. No PyPI API tokens or additional
GitHub secrets/variables are required by the publishing workflow.

## Environments and variables

| Setting | Purpose |
| --- | --- |
| GitHub environment `testpypi` | Staging uploads, triggered by **Run workflow** |
| GitHub environment `pypi` | Production uploads, triggered by a published GitHub Release |
| `RELEASE_TAG` | Set automatically from the GitHub release tag; must equal `v<project.version>` |
| `SO102_VERSION` | Local shell variable used by the installation commands below; not a workflow input |

The package version comes from `project.version` in
[`pyproject.toml`](../pyproject.toml), independently of the LeRobot version.
Set the local variable to the version you intend to test, for example:

```bash
export SO102_VERSION=0.1.0a3
```

This variable does not change the package version or select what GitHub publishes.
If you open another terminal, set it again before running the commands below.

The Trusted Publisher on each registry must match owner `roboninecom`, repository
`SO-ARM-102-Lerobot`, workflow filename `publish.yml`, and environment `testpypi`
or `pypi`, respectively. After a repository rename, replace the old publisher in
both registries' project **Publishing** settings.

If publishing fails with `invalid-publisher`, correct those settings and rerun
failed jobs in GitHub Actions. A version bump is unnecessary if no files were
uploaded; inspect the registry before retrying a partial upload.

## 1. Prepare and publish to staging (TestPyPI)

1. Update `project.version` to the new version, such as `0.1.0a3`. Update the README
   installation examples and release notes, then merge the intended changes into
   `main`. Uploaded files cannot be overwritten; changed uploads need a new version.
2. Open **Actions > Build and publish package > Run workflow**, select `main`,
   and run it. Note the commit SHA so production can release the same code.
3. Approve the `testpypi` deployment if prompted. Wait for the build, validation,
   and TestPyPI upload jobs to succeed. The production job is skipped.
4. Check the version on [TestPyPI](https://test.pypi.org/project/lerobot-robot-so-arm102/).

## 2. Test the staging installation

Create a fresh environment outside the source checkout. Install dependencies from
production PyPI, then install only the plugin from TestPyPI:

```bash
SO102_CHECK_DIR="$(mktemp -d)"
cd "$SO102_CHECK_DIR"
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --index-url https://pypi.org/simple/ \
  'lerobot[feetech,core_scripts]==0.6.1'
python -m pip install --index-url https://test.pypi.org/simple/ \
  --no-deps --no-cache-dir "lerobot_robot_so_arm102==$SO102_VERSION"

python -m pip check
python -m pip show lerobot_robot_so_arm102
lerobot-calibrate --help
lerobot-teleoperate --help
```

Confirm the installed version matches `SO102_VERSION` and each help command lists
`so_arm102_follower` and `bi_so_arm102_follower`. These checks do not connect to
hardware. Complete the hardware checks relevant to the release and record the
tested LeRobot/backend versions.

If changes are needed, use a new version and repeat staging. Once testing is done,
leave this environment with `deactivate`.

## 3. Prepare and publish production

1. Use the same package version and commit that passed staging. TestPyPI and PyPI
   have separate release histories, so the version can be the same on both.
2. Create a GitHub Release with a tag exactly matching `v<project.version>`
   (for example, `v0.1.0a3`), targeting the tested commit. Include the changes and
   validation results in the release notes. Mark alpha versions as prereleases.
3. Review the draft, then click **Publish release**. A published prerelease also
   uploads to production PyPI; a draft release or a Git tag alone does not.
4. Approve the `pypi` deployment if prompted, then verify the workflow and the
   [PyPI release](https://pypi.org/project/lerobot-robot-so-arm102/).

The workflow rebuilds the distributions from the release commit; it does not copy
the uploaded TestPyPI files. The README bundled in this build becomes the PyPI
project description. README changes require a new release to appear on PyPI.

## 4. Verify the production installation

Use another fresh environment, with `SO102_VERSION` still set to the released version:

```bash
SO102_CHECK_DIR="$(mktemp -d)"
cd "$SO102_CHECK_DIR"
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --index-url https://pypi.org/simple/ --no-cache-dir \
  'lerobot[feetech,core_scripts]==0.6.1' \
  "lerobot_robot_so_arm102[feetech]==$SO102_VERSION"

python -m pip check
python -m pip show lerobot_robot_so_arm102
lerobot-calibrate --help
lerobot-teleoperate --help
```

Confirm the version and plugin discovery again. If an upload partially succeeds,
inspect the registry before retrying; existing files cannot be overwritten.
