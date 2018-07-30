def list_backups(site_names, wpsyncdir,
                 database, uploads, plugins, themes, full):
    is_single = len(site_names) == 1
    backup_dir = wpsyncdir / 'backups'
    for (site_name, fs_safe_name) in site_names:
        site_backup_dir = backup_dir / fs_safe_name
        try:
            for backup_path in site_backup_dir.iterdir():
                bn = backup_path.name
                backup_title = f'{bn[:13]}:{bn[14:16]}:{bn[17:]}'
                if not is_single:
                    backup_title = f'{site_name}@{backup_title}'
                details = [d.name for d in backup_path.iterdir()]
                backup_title += ' ' + ' '.join(details)
                do_list = len(details) > 0
                if database:
                    do_list = do_list and 'database' in details
                if uploads:
                    do_list = do_list and 'uploads' in details
                if plugins:
                    do_list = do_list and 'plugins' in details
                if themes:
                    do_list = do_list and 'themes' in details
                if full:
                    do_list = do_list and 'full' in details
                if do_list:
                    print(backup_title)
        except FileNotFoundError as e:
            if is_single:
                print(f'There are no backups for {site_name}.')
