# Image Cropper for Revit

PyRevit script for cropping images in Autodesk Revit using FilledRegion polygons or DetailLine rectangles.

## Description

This script allows you to crop images in Revit in two ways:
- **By polygon**: using FilledRegion (with transparency support)
- **By rectangle**: using DetailLine

## Requirements

- Autodesk Revit
- [PyRevit](https://github.com/eirannejad/pyRevit) extension
- [rpw](https://github.com/gtalarico/revitpythonwrapper) library (included with PyRevit)

## Installation

1. Copy the `1. Crop image.pushbutton` folder to your PyRevit extensions directory
2. Restart PyRevit

## Usage

### Polygon Cropping (FilledRegion)

1. Insert an image into a Revit view
2. Create a FilledRegion over the image, defining the crop area
3. Select both elements (ImageInstance and FilledRegion)
4. Run the script

### Rectangle Cropping (DetailLine)

1. Insert an image into a Revit view
2. Create a DetailLine (rectangle) over the image
3. Select both elements (ImageInstance and DetailLine)
4. Run the script

## Features

- ✅ Polygon cropping with transparency support
- ✅ Rectangle cropping by DetailLine bounding box
- ✅ Automatic extraction of embedded images
- ✅ Saving cropped images in PNG format
- ✅ Automatic replacement of original image with cropped version
- ✅ Resource management and proper error handling

## Technical Details

### Algorithm

1. **Element search**: Script finds ImageInstance and FilledRegion/DetailLine in selection
2. **Parameter extraction**: Gets image dimensions, resolution, scale
3. **Coordinate conversion**: Converts coordinates from Revit feet to pixels
4. **Image cropping**:
   - For FilledRegion: creates polygon mask with transparency
   - For DetailLine: crops by rectangular area
5. **New image creation**: Creates new ImageType and ImageInstance
6. **Cleanup**: Removes original elements

### Constants

DEFAULT_DPI = 96.0              # Default resolution
MIN_POLYGON_POINTS = 3          # Minimum number of points for polygon
MIN_AREA_THRESHOLD = 1e-6       # Minimum area for valid polygon
MIN_DIMENSION = 1               # Minimum image dimension## File Structure
