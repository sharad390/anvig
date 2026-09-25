# ANVI Garments Android v8.9.18

Android 13+ cloud-build project based on the uploaded ANVI Garments v8.9.18 Windows source.

## Included
- Login
- Dashboard
- Work Entry
- Employee dropdown
- Work item dropdown
- Quantity/rate/amount calculation
- Saved Records search
- Edit Saved Record with locked date
- Delete Record
- Employees
- Work Items
- Reports
- CSV backup/export
- Settings
- SQLite local storage

## Default login
`admin123`

## GitHub Actions
1. Upload the contents of this folder to the root of `https://github.com/sharad390/anvi`.
2. Confirm `.github/workflows/build-apk.yml` exists.
3. Open **Actions**.
4. Select **Build ANVI Garments APK**.
5. Click **Run workflow**.
6. When successful, open the run summary.
7. Download artifact **ANVI-Garments-v8.9.18-APK**.
8. Extract the APK and install it on Android 13+.

## Important
The original Windows application uses Tkinter and Excel. Android does not run Tkinter directly, so this Android build uses Kivy for the UI and SQLite for local data. The original source is retained separately; this folder is the Android port/build project.
