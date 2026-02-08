# TMUX Files Backup System

This directory contains timestamped backups of all tmux-related files.

## Backup Naming Convention

Files are backed up with the following naming pattern:
```
{original_filename}_{YYYYMMDD_HHMMSS}_{description}.py
```

Example:
- `tmux_bot_cleaner_20250904_112741_memory_leak_fix.py`

## How to Create Backups

### Automatic Backup (Recommended)
```bash
./backup_tmux_files.sh "description_of_changes"
```

### Manual Backup
```bash
cp tmux_bot_cleaner.py tmux_backups/tmux_bot_cleaner_$(date +%Y%m%d_%H%M%S).py
```

## Backup Descriptions

- `memory_leak_fix` - Fixed memory leak detection to only log alarms, not restart bots
- `database_alert_system` - Added database alert system for unexpected errors
- `manual_backup` - Manual backup without specific description

## Restoring from Backup

To restore a previous version:
```bash
cp tmux_backups/tmux_bot_cleaner_20250904_112741_memory_leak_fix.py tmux_bot_cleaner.py
```

## Best Practices

1. **Always backup before making changes** - Use the backup script
2. **Use descriptive names** - Include what changes you're making
3. **Keep recent backups** - Don't delete backups immediately
4. **Test changes** - Verify changes work before deleting old backups

## File History

- `20250904_112644` - Initial backup
- `20250904_112741` - Memory leak fix + database alert system
