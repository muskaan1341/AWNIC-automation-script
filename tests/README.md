# The test files

The files are numbered so they run in a fixed order: login first (if sign-in is broken,
everything after it would fail with a confusing error), access-control checks last (they switch
between many accounts).

The list of files, what each covers, and how many tests each has is in the main
[README](../README.md#what-each-test-file-covers).

## Never run in parallel

Tests run one class after another, never side by side:

1. each test class opens its own Chrome and signs in, and sign-in is limited to 10 per minute;
2. a few tests create data, and parallel runs would change the numbers other tests read.

Do not add `pytest-xdist`.

## Running one part

```bash
pytest --env=deployed tests/test_07_kanban.py   # one file
pytest --env=deployed -m smoke                  # the short check
pytest --env=deployed -k "breadcrumb"           # one behaviour across files
```
