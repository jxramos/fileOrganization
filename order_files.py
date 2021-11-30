#region imports
# BASE PYTHON
import argparse
import os
import glob
import shutil
from datetime import datetime

# THIRD PARTY
import pandas
import exifread
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
    parser.add_argument("-s", "--sort_dirs", action='store_true', dest="is_sort_dirs",
                        help='Flag to enable the inclusion of directories to the sorting and organizing process.')

    return parser.parse_args()


def main(args):
    """
    Moves all files directly located beneath the given directory argument and
    """

    # Validate directory
    if not os.path.exists(args.dir):
        print("ERROR: given directory does not exist: {}".format(args.dir))
        return

    # Get all files under given directory
    files = glob.glob( os.path.join(args.dir, "*") )
    if not args.is_sort_dirs:
        # constrain to files alone
        files = [f for f in files if not os.path.isdir(f)]
    file_names = [os.path.basename(f) for f in files]

    # Lookup corresponding file attribute times for these files
    file_stats = [ os.stat(f) for f in files ]
    if args.type == "create":
        file_days = [ datetime.fromtimestamp(s.st_ctime).strftime("%Y-%m-%d") for s in file_stats ]
    else :
        file_days = [ datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d") for s in file_stats ]

    # Convert to DataFrame
    df = pandas.DataFrame( {'file_path':files, 'file_name':file_names, 'file_days': file_days } )

    #------------------------------------------------------------------------------
    # Parse out reliable creation date from mobile image filename timestamps
    #   NOTE moving files off MTP devices yields misleading creation date. Uses time of move
    #   not literal creation date unfortunately.

    # ANDROID MEDIA FILES
    # Test if media files (images/videos, eg IMG_20190902_170352.jpg)
    is_android_media = df['file_name'].str.match("(IMG|VID)_[0-9]{8}_[0-9]{6}_")

    # Reconstruct creation date from timestamp in filename
    if is_android_media.any():
        mobile_files = df['file_name'].loc[is_android_media]
        actual_create_days = mobile_files.apply(lambda d: f"{d[4:8]}-{d[8:10]}-{d[10:12]}")
        df.loc[is_android_media,'file_days'] = actual_create_days

    #------------------------------------------------------------------------------
    # Extract image exif data to lookup date taken
    # eg iphone's don't timestamp filenames unfortunately)
    is_jpeg = df['file_name'].str.match(r".*\.(jpg|jpeg|JPG|JPEG|PNG|png|MOV|heic|HEIC|THM)$")
    for idx_f, fp in df.loc[is_jpeg, 'file_path'].iteritems():
        with open(fp, 'rb') as img_file:
            tags = exifread.process_file(img_file, details=False, stop_tag='DateTimeOriginal')
            if 'EXIF DateTimeOriginal' not in tags:
                print("No DateTimeOriginal exif data in: " + fp)
                continue
            original_date = str(tags['EXIF DateTimeOriginal']) # eg '2018:03:01 15:49:55'
            df.loc[idx_f, 'file_days'] = original_date[0:10].replace(":","-")

    #------------------------------------------------------------------------------
    # Move all files according to their dates
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
