# Deprecation Policy

This library is in a beta stage of development.
Certain core design decisions have not yet been finalized as the development team learns about what works best.
Therefore, the deprecation policy described here is designed to enable rapid iteration of ideas.
This comes at the cost of inter-version stability.

The guiding principles are:

- the development team requires the ability to make breaking changes between minor versions
- there is no deprecation period for breaking changes
- all published versions will be of high quality with strong test coverage
- a detailed changelog will be published on every release, where all breaking changes are clearly enumerated and described

Note that this policy is consistent with [standard semantic versioning](https://semver.org/#spec-item-4).

Once the beta stage is completed, this and other documents will be updated, and a new deprecation policy will be published.
In particular, the new deprecation policy will come with a certain amount of backwards compatibility.


## Beta Stability warnings

This library raises a beta stability `UserWarning` on import to highlight the current beta status.
This is intended to catch the eye of those who may not notice the status in the `README.md`, `CONTRIBUTING.md`, or `DEPRECATION.md` files.
The warning will only be raised once per installed version of samplomatic, even in separate Python sessions.
This is implemented by storing some non-essential runtime state in your state directory.
Run

```python
from samplomatic._beta_warning import _get_config_path
print(_get_config_path())
```

to find your state directory. This directory is safe to delete; it will be recreated as needed.
