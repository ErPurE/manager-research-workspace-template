# Installation

## Windows EXE Install

1. Open the latest GitHub Release.
2. Download `ManagerDashboard-windows-x64.zip`.
3. Unzip it to a program folder, for example `C:\Tools\ManagerDashboard`.
4. Run `ManagerDashboard.exe`.
5. The Dashboard opens in your browser and stores user data in a separate workspace folder.

Program updates replace only the Dashboard program files. They do not overwrite your workspace data, tasks, notes, guidance records, or API profiles.

## Source / Portable Install

1. Unzip the package.
2. Move the folder anywhere you want to keep your research workspace.
3. Run `dashboard/start.bat`.
4. Optional: create a desktop shortcut to `dashboard/start.bat`.

## First Personalization

- Replace `.agent/profile.md` with your own research profile.
- Add your first todo item in the Dashboard or `tasks/todo.json`.
- Add your own guidance notes under `guidance/`.
- Add ideas under `notes/ideas/`.
- Add project research under `research/`.

## API Agent

The Dashboard can store multiple API profiles locally. API keys are written to `.agent/runtime/local_api_profiles.json`, which is ignored by git.

Use “测试连接” before processing real inbox items. Always review the generated preview before applying it.

## Updates

- Packaged public builds can check, download, and apply program updates from the Dashboard.
- Source / private workspace mode disables automatic public release installation.
- Workspace template or `.agent` rule migrations should be reviewed before applying; never replace a working research workspace blindly.
