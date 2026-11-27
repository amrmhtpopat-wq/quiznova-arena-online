# TAG SMART MATH — independent public pilot

Temporary five-device test environment using simulated student accounts only.

Build: `python --version`
Start: `python server.py --host 0.0.0.0 --demo --allow-lan-demo`
Environment: `SECURE_COOKIE=1`, `PILOT_PASSWORD=unique random strong password`, `DATA_DIR=/tmp/tag-math-pilot`.

**Render free filesystem is ephemeral.** Export CSV after each test; do not enter real student names, PINs, results, or personal data.

This branch is not used by the official TAG site. The school demo supports grade seven equations only, and does not include actual student accounts or persistent records.
