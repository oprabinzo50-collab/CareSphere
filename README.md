# CareSphere UI upgrade package

This package contains a visual-only UI layer inspired by modern electronics-platform interfaces:
- dark navy navigation with electric blue/cyan accents
- brighter primary actions and more consistent interaction states
- cleaner cards, forms, data tables, patient panels and status chips
- responsive refinements and visible keyboard focus states
- updated page title and browser theme colour

It intentionally does not change API calls, routes, authentication, clinical logic, permissions, or patient data.

## Apply to the repository

1. Unzip this package.
2. Run from the extracted folder:
   `python apply-upgrade.py /path/to/CareSphere`
3. In the repository, run:
   `cd frontend && npm run build && npm run lint`
4. Review the diff, then commit on a new branch.

Note: the GitHub integration rejected branch creation with HTTP 403 during this session, so this package is prepared for local application; it has not been committed to the remote repository. The supplied reference site was not fetchable in the available web inspector, so this is a carefully styled electronics-inspired direction rather than a verified pixel-for-pixel copy.
