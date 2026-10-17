# Publishing to PyPI

The `publish.yml` workflow checks, tests, and builds the package on pull requests
and pushes to `main`. Publishing a GitHub Release also runs these checks and then
uploads the wheel and source distribution to PyPI using Trusted Publishing
(OIDC), without a stored PyPI API token. Draft releases do not publish; published
prereleases do.

## One-time setup

1. Create a PyPI account using `hello@robonine.com`, verify the email, and enable
   two-factor authentication. Apply for the Robonine organization with website
   `https://robonine.com` if organization ownership is desired. Corporate
   organizations require a paid subscription; organization registration is
   separate from user registration and is not required for Trusted Publishing.
2. In the repository's **Settings > Environments**, create `pypi`. Configure
   required reviewers and restrict deployment tags to `v*`.
3. Before the first upload, add a
   [pending publisher](https://pypi.org/manage/account/publishing/) with:

   | Field | Value |
   | --- | --- |
   | PyPI project name | `lerobot_robot_so_arm102` |
   | GitHub owner | `roboninecom` |
   | Repository | `so-arm102-package` |
   | Workflow filename | `publish.yml` |
   | Environment | `pypi` |

   If the project already exists, configure the same publisher in that project's
   **Manage > Publishing** page instead. The first successful pending-publisher
   upload creates the project under the registering user's ownership; transfer
   it to the approved organization afterwards if needed.

## TestPyPI rehearsal

1. Create and verify a separate account at https://test.pypi.org/ and enable
   two-factor authentication.
2. Create a GitHub environment named `testpypi` in this repository.
3. Add a pending publisher at https://test.pypi.org/manage/account/publishing/
   using the values above, with environment `testpypi` instead of `pypi`.
   If the project already exists, use its **Manage > Publishing** page.
4. Merge the workflow into `main`, then open **Actions > Build and publish
   package > Run workflow**, select `main`, and run it. Approve the deployment
   if required. The manual run builds and validates the package, then uploads
   only to TestPyPI.
5. Verify installation from outside the source checkout in a fresh environment:

   ```bash
   python3.12 -m venv /tmp/so102-testpypi-check
   source /tmp/so102-testpypi-check/bin/activate
   python -m pip install 'lerobot[feetech,core_scripts]==0.6.1'
   python -m pip install --index-url https://test.pypi.org/simple/ --no-deps \
     'lerobot_robot_so_arm102==0.1.0a1'
   python -m pip check
   lerobot-calibrate --help
   ```

Confirm that `so_arm102_follower` appears in the help output. Use a new package
version for changed uploads; existing files cannot be overwritten. TestPyPI
and production PyPI have separate publisher settings and release histories.

## Release

1. Update `project.version` in `pyproject.toml` and merge the change into `main`.
   Each PyPI release needs a new version; uploaded files cannot be overwritten.
2. Publish a GitHub Release from the intended commit on `main`, with a tag exactly
   matching `v<project.version>` (currently `v0.1.0a1`). For alpha versions, mark
   the GitHub Release as a prerelease. A mismatched tag fails before upload.
3. Approve the `pypi` deployment when prompted, then verify the workflow and the
   [PyPI project](https://pypi.org/project/lerobot-robot-so-arm102/).

After the first successful release, users can install in their existing LeRobot
environment with either command (the exact version also selects the alpha):

```bash
python -m pip install 'lerobot_robot_so_arm102[feetech]==0.1.0a1'
uv pip install 'lerobot_robot_so_arm102[feetech]==0.1.0a1'
```

If publishing fails because the publisher is missing, finish the one-time setup
and rerun the failed publish job. If an upload partially succeeds, inspect PyPI
before retrying; the workflow deliberately does not silently skip existing files.

References: [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
and [organization accounts](https://docs.pypi.org/organization-accounts/).
