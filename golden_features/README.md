# golden_features

This directory stores expert-approved reference `.feature` files.

## Naming convention

- Use file names aligned with manual tests:
  - `manual_tests/tests/acquiring_tariffs.txt`
  - `golden_features/acquiring_tariffs.feature`
- The app matches files by stem (`<name>.txt` -> `<name>.feature`).

## Usage

- Keep only validated "golden" scenarios here.
- These files are displayed next to candidate outputs during expert scoring.

