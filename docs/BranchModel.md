## Immcellfie Branch Model

* Branch off the main-branch.
* Name the branch as follows:
	* If the fix is a new feature, it should be named as 'feature/name-of-feature'.
	* If the fix is a bug, it should be named as 'bug/name-of-bug'.
* Once ready, create a branch for the release (for example, 2.1). Follow semantic versioning so that if we need to do hot fixes/patches the next branch will be 2.1.1 and so forth.

For reference, click [git-branching-model](https://nvie.com/posts/a-successful-git-branching-model/).

### Use Cases

* Typical Use Case:

> Create 'feature/<my-feature-for-version2.2>' branch off master-branch, '2.1' branch is created and frozen then once feature work is done merge 'feature/<my-feature-for-version2.2>' into master-branch, '2.2' branch is created and frozen.

* Patching:

> Create 2.1 and then merge the new feature into master that changes a lot of stuff and needs to be thoroughly tested. But then you find a critical bug in 2.1 that needs to be fixed right away, branch off 2.1 in this case instead of master-branch and then create '2.1.1' branch.
