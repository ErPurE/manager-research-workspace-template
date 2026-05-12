# Release Notes v2.4.0

## Highlights

- Add a Windows executable build for the browser-based Dashboard.
- Separate program files from user workspace data in packaged builds.
- Add in-app program update endpoints and Dashboard controls.
- Add a public-safe sync tool for moving framework changes from a private workspace to this public template.

## Safety

- Program updates do not overwrite `tasks/`, `guidance/`, `notes/`, `research/`, or local API profile files.
- Source/private workspace mode keeps public release auto-install disabled.
- The public sync tool defaults to dry-run and blocks known private content and secret patterns.
