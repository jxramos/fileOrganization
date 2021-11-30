#region imports
# BASE PYTHON
import argparse
import os
import glob
import shutil
from datetime import datetime

# THIRD PARTY
import pandas
#endregion


def parse_args():
    help_message = """
        order_files   Organizes all files under the given directory into subfolders
                      matching the file's creation or modification date where the files
                      will be moved to.
        """
    parser = argparse.ArgumentParser(description=help_message)
    parser.add_argument('-d', '--dir', default="", help="A path with files to be organized")
    parser.add_argument('-t', '--type', default='create', help='Date type to group by', nargs='?', choices=('create', 'modified'), )

    return parser.parse_args()


def main(args):
    """
    Moves all files directly located beneath the given directory argument and
    """

    # Get all files under given directory
    files = glob.glob( os.path.join(args.dir, "*") )

    # Lookup corresponding file attribute times for these files
    file_stats = [ os.stat(f) for f in files ]
    if args.type == "create":
        file_days = [ datetime.fromtimestamp(s.st_ctime).strftime("%Y-%m-%d") for s in file_stats ]
    else :
        file_days = [ datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d") for s in file_stats ]

    # Convert to DataFrame
    df = pandas.DataFrame( {'file_path':files, 'file_days': file_days } )

    for group_name, df_group in df.groupby('file_days'):
        # Make the subfolder for this file's day
        group_dir = os.path.join(args.dir, group_name + ' ()')
        os.makedirs(group_dir, exist_ok=True)

        # Move all files under this subfolder
        for file_path in df_group['file_path']:
            shutil.move(file_path, group_dir)


if __name__ == "__main__":
    args = parse_args()
    main(args)
