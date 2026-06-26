# qrob Auto-Update System

This system enables automatic daily updates of the qrob repository across multiple devices.

## Quick Start

### On Each Device (One-time Setup)

1. **Make setup script executable:**
   ```bash
   chmod +x ~/bin/qrob/setup-auto-update.sh
   ```

2. **Run the setup script:**
   ```bash
   ~/bin/qrob/setup-auto-update.sh
   ```

   This will:
   - Install a daily cron job to run at 2:00 AM
   - Create a log file at `~/.qrob-updates.log`
   - Display your cron configuration

That's it! Your device will now automatically update qrob daily.

## Files

- **update-qrob.sh** - Main update script (pulls latest changes from remote)
- **setup-auto-update.sh** - Setup script to install cron job
- **Auto-update README.md** - This file

## How It Works

1. **Daily Trigger**: Cron runs the update script at 2:00 AM every day
2. **Safe Pull**: Uses git fetch + fast-forward merge to safely update
3. **Conflict Handling**: If local changes exist, they are stashed before updating
4. **Logging**: All activity is logged to `~/.qrob-updates.log`

## Monitoring

### View Update Logs
```bash
tail -f ~/.qrob-updates.log
```

### Check Update History
```bash
cat ~/.qrob-updates.log
```

### Check Installed Cron Job
```bash
crontab -l | grep update-qrob
```

## Customization

### Change Update Time

Edit your cron job:
```bash
crontab -e
```

Find the qrob line and modify the time. Cron format: `minute hour day month weekday`

**Examples:**
- `0 2 * * *` - Daily at 2:00 AM (default)
- `0 */6 * * *` - Every 6 hours
- `0 9,17 * * *` - Daily at 9 AM and 5 PM

### Manual Update

Run the update script manually anytime:
```bash
~/bin/qrob/update-qrob.sh
```

## Troubleshooting

### Update Failed to Merge
- Check the log: `tail ~/.qrob-updates.log`
- Manual merge may be needed if there are conflicts
- Your local changes are safely stashed

### Cron Job Not Running
- Verify cron is enabled: `systemctl is-active cron` (Linux) or `sudo launchctl list | grep cron` (macOS)
- Check system logs for errors
- Verify script permissions: `ls -la ~/bin/qrob/update-qrob.sh`

### Permission Denied
- Make scripts executable: `chmod +x ~/bin/qrob/*.sh`

## Uninstall

To stop automatic updates:
```bash
crontab -e
```

Find and delete the qrob line, then save and exit.

Or remove just the cron entry:
```bash
crontab -l | grep -v update-qrob.sh | crontab -
```

## Notes

- Log file location can be changed in the cron job (default: `~/.qrob-updates.log`)
- The script uses `--ff-only` to ensure clean, linear history
- Local uncommitted changes are automatically stashed before updating
- Works on Linux, macOS, and WSL (Windows Subsystem for Linux)
- Does NOT work on native Windows (use WSL or schedule with Task Scheduler separately)
