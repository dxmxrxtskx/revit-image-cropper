# -*- coding: utf-8 -*-
#pylint: disable=E0401,W0621,W0631,C0413,C0111,C0103
"""
PyRevit script for cropping images in Revit.

Crops images by Filled Region polygon (with transparency) or by rectangle via Detail Line.
Select an ImageInstance and either a FilledRegion or DetailLine, then run the script.
"""
__doc__ = 'Crop images by Filled Region polygon (with transparency) or by rectangle via Detail Line.'
__author__ = 'Yanshin Elisey'

import os
import math

import clr
clr.AddReference('System')
clr.AddReference('System.IO')
clr.AddReference('System.Drawing')

from System import Array, Single, Environment
from System.Drawing import GraphicsUnit, Graphics, Rectangle, Bitmap, Color, PointF
from System.Drawing.Imaging import ImageFormat
from System.Drawing.Drawing2D import GraphicsPath, FillMode

import rpw
from rpw import doc, uidoc, DB

# Constants
DEFAULT_DPI = 96.0
MIN_POLYGON_POINTS = 3
MIN_AREA_THRESHOLD = 1e-6
MIN_DIMENSION = 1

def _resolve_image_path(img_type, img_path):
    """
    Resolve image path. If file doesn't exist, extract embedded image from ImageType.
    
    Args:
        img_type: DB.ImageType instance
        img_path: Original image file path (may be None or invalid)
        
    Returns:
        str: Valid path to image file
        
    Raises:
        IOError: If image cannot be resolved
    """
    if img_path and os.path.exists(img_path):
        return img_path

    pics = Environment.GetFolderPath(Environment.SpecialFolder.MyPictures)
    stem = os.path.splitext(os.path.basename(img_path or "revit_image"))[0]
    out_path = os.path.join(pics, stem + "_from_revit.png")

    try:
        embedded_img = img_type.GetImage()  # System.Drawing.Image
    except Exception:
        embedded_img = None

    if embedded_img is None:
        raise IOError(
            "Не удалось получить встроенное изображение и отсутствует файл: {}".format(img_path)
        )

    embedded_img.Save(out_path, ImageFormat.Png)
    return out_path

def get_selected_elements():
    """
    Get currently selected elements in Revit.
    
    Returns:
        list: List of DB.Element instances, empty if nothing selected
    """
    sel = uidoc.Selection
    ids = sel.GetElementIds()
    if not ids:
        return []
    return [doc.GetElement(eid) for eid in ids]


def get_bbox_center_pt(bbox):
    """
    Calculate center point of bounding box.
    
    Args:
        bbox: DB.BoundingBoxXYZ instance
        
    Returns:
        DB.XYZ: Center point at Z=0
    """
    avg_x = (bbox.Min.X + bbox.Max.X) / 2.0
    avg_y = (bbox.Min.Y + bbox.Max.Y) / 2.0
    return DB.XYZ(avg_x, avg_y, 0)


def _safe_dpi(val, fallback=DEFAULT_DPI):
    """
    Safely convert value to DPI, using fallback if invalid.
    
    Args:
        val: Value to convert (may be None or invalid)
        fallback: Default DPI value if conversion fails
        
    Returns:
        float: Valid DPI value
    """
    try:
        dpi = float(val)
        if dpi > 0:
            return dpi
    except (TypeError, ValueError):
        pass
    return float(fallback)


def _output_path(img_path, suffix):
    """
    Generate output path for cropped image.
    
    Args:
        img_path: Original image path
        suffix: Suffix to add to filename (e.g., "cropped_rect", "cropped_poly")
        
    Returns:
        str: Output file path
    """
    folder = os.path.dirname(img_path)
    stem = os.path.splitext(os.path.basename(img_path))[0]
    return os.path.join(folder, "{}_{}.png".format(stem, suffix))


def _clean_loop(loop_pts):
    """
    Clean polygon loop points: remove invalid, NaN, Inf, and duplicate points.
    
    Args:
        loop_pts: List of (x, y) tuples
        
    Returns:
        list: Cleaned list of (x, y) tuples
    """
    clean = []
    prev = None
    for x, y in loop_pts:
        # Skip None values
        if x is None or y is None:
            continue
        # Skip NaN and Inf values
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            continue
        if isinstance(y, float) and (math.isnan(y) or math.isinf(y)):
            continue
        cur = (float(x), float(y))
        # Skip duplicate consecutive points
        if prev is None or cur != prev:
            clean.append(cur)
            prev = cur
    # Remove closing point if it matches first point
    if len(clean) >= 2 and clean[0] == clean[-1]:
        clean = clean[:-1]
    return clean


def _area_signed(pts):
    """
    Calculate signed area of polygon using shoelace formula.
    
    Args:
        pts: List of (x, y) tuples representing polygon vertices
        
    Returns:
        float: Signed area (positive for counter-clockwise, negative for clockwise)
    """
    if len(pts) < MIN_POLYGON_POINTS:
        return 0.0
    area = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area += x1 * y2 - x2 * y1
    return 0.5 * area


def crop_image_rect(img_path, rectangle_crop):
    """
    Crop image to rectangular region.
    
    Args:
        img_path: Path to source image file
        rectangle_crop: System.Drawing.Rectangle defining crop region
        
    Returns:
        str: Path to saved cropped image
        
    Raises:
        IOError: If source image file not found
    """
    if not os.path.exists(img_path):
        raise IOError('Image Source path not found: {}'.format(img_path))
    
    src = None
    bmp = None
    g = None
    try:
        src = Bitmap(img_path)
        src.SetResolution(DEFAULT_DPI, DEFAULT_DPI)
        bmp = Bitmap(max(MIN_DIMENSION, rectangle_crop.Width), 
                     max(MIN_DIMENSION, rectangle_crop.Height))
        g = Graphics.FromImage(bmp)
        g.DrawImage(src, 0, 0, rectangle_crop, GraphicsUnit.Pixel)
        out_path = _output_path(img_path, "cropped_rect")
        bmp.Save(out_path, ImageFormat.Png)
        return out_path
    finally:
        # Cleanup resources
        if g is not None:
            g.Dispose()
        if bmp is not None:
            bmp.Dispose()
        if src is not None:
            src.Dispose()


def crop_image_polygon(img_path, polygon_points_px):
    """
    Crop image to polygon region with transparency.
    
    Args:
        img_path: Path to source image file
        polygon_points_px: List of polygon loops, each loop is list of (x, y) tuples in pixels
        
    Returns:
        tuple: (output_path, bounding_rectangle)
        
    Raises:
        IOError: If source image file not found
        ValueError: If polygon loops are empty or invalid
    """
    if not os.path.exists(img_path):
        raise IOError('Image Source path not found: {}'.format(img_path))
    if not polygon_points_px:
        raise ValueError('Polygon loops are empty.')

    # Calculate bounding box of all polygons
    xs = [pt[0] for loop in polygon_points_px for pt in loop]
    ys = [pt[1] for loop in polygon_points_px for pt in loop]
    minx, maxx = int(math.floor(min(xs))), int(math.ceil(max(xs)))
    miny, maxy = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    width = max(MIN_DIMENSION, maxx - minx)
    height = max(MIN_DIMENSION, maxy - miny)

    # Build graphics path from valid polygons
    path = GraphicsPath(FillMode.Alternate)
    valid_any = False
    for loop in polygon_points_px:
        loop = _clean_loop(loop)
        if len(loop) < MIN_POLYGON_POINTS:
            continue
        # Convert to PointF array relative to bounding box
        pts = [PointF(Single(x - minx), Single(y - miny)) for (x, y) in loop]
        # Skip degenerate polygons (zero area)
        if abs(_area_signed([(p.X, p.Y) for p in pts])) < MIN_AREA_THRESHOLD:
            continue
        path.AddPolygon(Array[PointF](pts))
        valid_any = True

    if not valid_any:
        raise ValueError('No valid polygon loops to clip.')

    src = None
    dst = None
    g = None
    try:
        src = Bitmap(img_path)
        src.SetResolution(DEFAULT_DPI, DEFAULT_DPI)
        dst = Bitmap(width, height)
        dst.MakeTransparent()
        g = Graphics.FromImage(dst)
        g.Clear(Color.Transparent)
        g.SetClip(path)
        g.TranslateTransform(Single(-minx), Single(-miny))
        g.DrawImage(src, 0, 0)
        out_path = _output_path(img_path, "cropped_poly")
        dst.Save(out_path, ImageFormat.Png)
        return out_path, Rectangle(minx, miny, width, height)
    finally:
        # Cleanup resources
        if g is not None:
            g.Dispose()
        if dst is not None:
            dst.Dispose()
        if src is not None:
            src.Dispose()


def _main():
    """
    Main function: crop image based on selected elements.
    
    Requires:
        - ImageInstance element (source image)
        - FilledRegion or DetailLine element (crop reference)
        
    Process:
        1. Find ImageInstance and crop reference in selection
        2. Extract image properties and calculate scale
        3. Crop image (polygon for FilledRegion, rectangle for DetailLine)
        4. Create new ImageType and ImageInstance
        5. Clean up original elements
    """
    img_element, element_bbox = None, None
    crop_ref_element = None

    elements = get_selected_elements()
    if not elements:
        return

    for element in elements:
        if isinstance(element, (DB.FilledRegion, DB.DetailLine)):
            element_bbox = element.get_BoundingBox(doc.ActiveView)
            crop_ref_element = element
            continue

        for valid_type_id in element.GetValidTypes():
            valid_type = doc.GetElement(valid_type_id)
            if isinstance(valid_type, DB.ImageType):
                img_element = element
                img_type = valid_type

                bip_filename = DB.BuiltInParameter.RASTER_SYMBOL_FILENAME
                bip_height_px = DB.BuiltInParameter.RASTER_SYMBOL_PIXELHEIGHT
                bip_width_px = DB.BuiltInParameter.RASTER_SYMBOL_PIXELWIDTH
                bip_resolution = DB.BuiltInParameter.RASTER_SYMBOL_RESOLUTION

                img_path = img_type.get_Parameter(bip_filename).AsString()
                img_width_px = img_type.get_Parameter(bip_width_px).AsInteger()
                img_height_px = img_type.get_Parameter(bip_height_px).AsInteger()
                img_resolution = img_type.get_Parameter(bip_resolution).AsInteger()
                # гарантируем, что изображение существует на диске
                img_path = _resolve_image_path(img_type, img_path)

                # если в типе не записаны размеры, пробуем взять из файла
                if (not img_width_px) or (not img_height_px):
                    tmp_bmp = None
                    try:
                        tmp_bmp = Bitmap(img_path)
                        img_width_px = tmp_bmp.Width
                        img_height_px = tmp_bmp.Height
                    except Exception:
                        pass
                    finally:
                        if tmp_bmp is not None:
                            tmp_bmp.Dispose()

                bip_scale = DB.BuiltInParameter.RASTER_VERTICAL_SCALE
                bip_width_ft = DB.BuiltInParameter.RASTER_SHEETWIDTH
                bip_height_ft = DB.BuiltInParameter.RASTER_SHEETHEIGHT

                img_scale = img_element.get_Parameter(bip_scale).AsDouble()
                img_width = img_element.get_Parameter(bip_width_ft).AsDouble()
                img_height = img_element.get_Parameter(bip_height_ft).AsDouble()
                img_bbox = img_element.get_BoundingBox(doc.ActiveView)
                break

    if not (img_element and element_bbox and crop_ref_element):
        return

    cropbox_height_ft = element_bbox.Max.Y - element_bbox.Min.Y
    cropbox_width_ft = element_bbox.Max.X - element_bbox.Min.X
    if cropbox_height_ft <= 0 or cropbox_width_ft <= 0:
        return

    x_ft_to_px_scale = float(img_width_px) / float(img_width) if img_width else 0.0
    y_ft_to_px_scale = float(img_height_px) / float(img_height) if img_height else 0.0
    if x_ft_to_px_scale <= 0 or y_ft_to_px_scale <= 0:
        return

    def pt_ft_to_px(pt_xyz):
        dx_ft = pt_xyz.X - img_bbox.Min.X
        dy_ft = pt_xyz.Y - img_bbox.Min.Y
        x_px = dx_ft * x_ft_to_px_scale
        y_px = (img_height - dy_ft) * y_ft_to_px_scale
        return (x_px, y_px)

    if isinstance(crop_ref_element, DB.FilledRegion):
        # Try to get boundaries from FilledRegion
        boundaries = None
        try:
            boundaries = crop_ref_element.GetBoundaries()
        except Exception:
            # Fallback to Sketch profile if GetBoundaries() fails
            boundaries = []
            try:
                sp = crop_ref_element.Sketch
                if sp:
                    for prof in sp.Profile:
                        boundaries.append(list(prof))
            except Exception:
                pass

        if boundaries:
            loops = []
            for crv_loop in boundaries:
                pts = []
                for crv in crv_loop:
                    for p in crv.Tessellate():
                        pts.append(pt_ft_to_px(p))
                pts = _clean_loop(pts)
                if len(pts) >= MIN_POLYGON_POINTS:
                    loops.append(pts)
            new_img_path, poly_rect = crop_image_polygon(img_path, loops)
            target_width_ft = poly_rect.Width / x_ft_to_px_scale
        else:
            return
    else:
        lw_left_crop_pt = element_bbox.Min - img_bbox.Min
        up_left_crop_pt = lw_left_crop_pt + DB.XYZ(0, cropbox_height_ft, 0)
        crop_pt_x_ft = up_left_crop_pt.X
        crop_pt_y_ft = img_height - up_left_crop_pt.Y

        crop_pt_x_px = int(round(crop_pt_x_ft * x_ft_to_px_scale))
        crop_pt_y_px = int(round(crop_pt_y_ft * y_ft_to_px_scale))
        cropbox_width_px = int(round(cropbox_width_ft * x_ft_to_px_scale))
        cropbox_height_px = int(round(cropbox_height_ft * y_ft_to_px_scale))

        rect_px = Rectangle(crop_pt_x_px, crop_pt_y_px, cropbox_width_px, cropbox_height_px)
        new_img_path = crop_image_rect(img_path, rect_px)
        target_width_ft = cropbox_width_ft

    dpi = _safe_dpi(img_resolution)
    opts = DB.ImageTypeOptions(new_img_path, False, DB.ImageTypeSource.Import)
    opts.Resolution = dpi

    with rpw.db.Transaction('Create ImageType (cropped)'):
        img_type_new = DB.ImageType.Create(doc, opts)

    place = DB.ImagePlacementOptions(get_bbox_center_pt(element_bbox), DB.BoxPlacement.Center)

    with rpw.db.Transaction('Place Cropped Image and Cleanup'):
        new_img_instance = DB.ImageInstance.Create(doc, doc.ActiveView, img_type_new.Id, place)
        par_w = new_img_instance.get_Parameter(DB.BuiltInParameter.RASTER_SHEETWIDTH)
        if par_w:
            par_w.Set(target_width_ft)
        # Cleanup: remove original elements
        try:
            doc.Delete(img_element.Id)
        except Exception:
            pass
        try:
            doc.Delete(crop_ref_element.Id)
        except Exception:
            pass


# Вызов
if not __shiftclick__:  #pylint: disable=E0602
    pass

_main()
