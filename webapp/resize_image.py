from PIL import Image
import argparse
import sys
from io import BytesIO

""" Python script to resize images to a custom resolution

It performs the following tasks:

1. Parse arguments for 
    - Source image 
    - Resolution
    - Destination folder (including image name to save)

2. Re-size image using PIL 
    - resize image to custom resolution without losing quality and maintaining aspect ratio


Usage:
    $ python resize_image.py -img <name_of_source_image> -res <X_dim> <Y_dim> -dest <Save_path>

Example:
    $ python resize_image.py -img ../Demo_images/joe_biden_2.jpg -res 900 900 -dest ../Demo_images/result.png


Help:
    To get help on the script usage, type the following in cmd/shell:
    $ python resize_image.py -h
"""

# Parse command line arguments provided
#ap = argparse.ArgumentParser(description=" Re-size images with custom resolution using Python")

# 1. Source image (Including filename) 
#ap.add_argument("-img","--image",required=True, help="< Specify Path for source image (Image to resize) >")

# 2. Resize resolution
#ap.add_argument("-res","--resolution",required=True, nargs=2,type=int,help="< Specify Re-size resolution (space-seperated), Eg: 900 900 > default= 900 x 900 ", default=(900,900))

# 3. Destination path (Including filename) 
#ap.add_argument("-dest","--destination", help="< Specify Destination path (including filename) >", default="resized_image.png")


def resize(im, resolution): #save_fp
    
    """ Re-size and save image using PIL library

    Args:
        img_fp: str
        resolution: list,tuple
        save_fp: str
    """

    try:
        #im = Image.open(img_fp)
        len_x, wid_y = im.size  #Original size

        x_dim, y_dim = resolution
       
        print("\n Image found, resizing image.. \n")

        ratio = min(x_dim / len_x, y_dim / wid_y)
        proper_size = int(ratio * len_x), int(ratio * wid_y)
        im_resized = im.resize(proper_size, Image.LANCZOS)
        img_byte_arr = BytesIO()
        im_resized.save(img_byte_arr,format='PNG')
        im_resized = img_byte_arr.getvalue()
        #im_resized.save(save_fp,"PNG")
        
        #print(f"\n Image re-sized successfully..Check path {save_fp} for results \n")

        return im_resized

    except Exception as e:
        print(f"\n Error:  {e} \n ")
        return e 



        
