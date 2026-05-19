# Deprecation Policy

This library is in the `0.X` stage of development, where breaking changes are permitted between minor versions.
Our deprecation policy is on a "best effort" basis: we we issue deprecation warnings and state a promised lifetime of the deprication period (nominally, one month) whenever it is reasonably feasible to do so.
In such cases, please refer to [the Qiskit SDK's deprecation file](https://github.com/Qiskit/qiskit/blob/main/DEPRECATION.md) for information about the mechanisms of this process; samplomatic imports Qiskit's deprecation tooling.
However, since this project is still relatively young, we require the flexibility to fix poor design decisions as they are discovered, which may occasionally come with the need to make a change with no deprecation period.

In any case, the [changelog](CHANGELOG.md) keeps a detailed record of all changes and deprecations.
