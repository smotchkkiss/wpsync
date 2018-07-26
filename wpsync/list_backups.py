def list_backups(arguments, config, wpsyncdir):
    if arguments['--site'] is not None:
        is_single = True
        sites_to_list = [arguments['--site']]
    else:
        is_single = False
        if arguments['--legacy']:
            sites_to_list = [config[site]['name'] for site in config.keys()]
        else:
            sites_to_list = config.keys()
    backup_dir = wpsyncdir / 'backups'
    for site_name in sites_to_list:
        site_backup_dir = backup_dir / site_name
        try:
            for backup_path in site_backup_dir.iterdir():
                bn = backup_path.name
                backup_title = f'{bn[:13]}:{bn[14:16]}:{bn[17:]}'
                if not is_single:
                    backup_title = f'{site_name}@{backup_title}'
                details = [d.name for d in backup_path.iterdir()]
                backup_title += ' ' + ' '.join(details)
                do_list = len(details) > 0
                if arguments['--database'] or arguments['--all']:
                    do_list = do_list and 'database' in details
                if arguments['--uploads'] or arguments['--all']:
                    do_list = do_list and 'uploads' in details
                if arguments['--plugins'] or arguments['--all']:
                    do_list = do_list and 'plugins' in details
                if arguments['--themes'] or arguments['--all']:
                    do_list = do_list and 'themes' in details
                if arguments['--full']:
                    do_list = do_list and 'full' in details
                if do_list:
                    print(backup_title)
        except FileNotFoundError as e:
            if is_single:
                print(f'There are no backups for {site_name}.')
