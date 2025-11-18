# Image Cropper for Revit

PyRevit script for cropping images in Autodesk Revit using FilledRegion polygons or DetailLine rectangles.

## Описание / Description

Этот скрипт позволяет обрезать изображения в Revit двумя способами:
- **По полигону**: используя FilledRegion (с поддержкой прозрачности)
- **По прямоугольнику**: используя DetailLine

This script allows you to crop images in Revit in two ways:
- **By polygon**: using FilledRegion (with transparency support)
- **By rectangle**: using DetailLine

## Требования / Requirements

- Autodesk Revit
- [PyRevit](https://github.com/eirannejad/pyRevit) extension
- [rpw](https://github.com/gtalarico/revitpythonwrapper) library (included with PyRevit)

## Установка / Installation

1. Скопируйте папку `1. Crop image.pushbutton` в вашу директорию PyRevit extensions
2. Перезапустите PyRevit

1. Copy the `1. Crop image.pushbutton` folder to your PyRevit extensions directory
2. Restart PyRevit

## Использование / Usage

### Обрезка по полигону (FilledRegion) / Polygon Cropping

1. Вставьте изображение в вид Revit
2. Создайте FilledRegion поверх изображения, определяя область обрезки
3. Выделите оба элемента (ImageInstance и FilledRegion)
4. Запустите скрипт

1. Insert an image into a Revit view
2. Create a FilledRegion over the image, defining the crop area
3. Select both elements (ImageInstance and FilledRegion)
4. Run the script

### Обрезка по прямоугольнику (DetailLine) / Rectangle Cropping

1. Вставьте изображение в вид Revit
2. Создайте DetailLine (прямоугольник) поверх изображения
3. Выделите оба элемента (ImageInstance и DetailLine)
4. Запустите скрипт

1. Insert an image into a Revit view
2. Create a DetailLine (rectangle) over the image
3. Select both elements (ImageInstance and DetailLine)
4. Run the script

## Особенности / Features

- ✅ Поддержка полигональной обрезки с прозрачностью
- ✅ Прямоугольная обрезка по bounding box DetailLine
- ✅ Автоматическое извлечение встроенных изображений
- ✅ Сохранение обрезанных изображений в PNG формате
- ✅ Автоматическая замена исходного изображения на обрезанное
- ✅ Управление ресурсами и корректная обработка ошибок

- ✅ Polygon cropping with transparency support
- ✅ Rectangle cropping by DetailLine bounding box
- ✅ Automatic extraction of embedded images
- ✅ Saving cropped images in PNG format
- ✅ Automatic replacement of original image with cropped version
- ✅ Resource management and proper error handling

## Технические детали / Technical Details

### Алгоритм работы / Algorithm

1. **Поиск элементов**: Скрипт ищет ImageInstance и FilledRegion/DetailLine в выделении
2. **Извлечение параметров**: Получает размеры изображения, разрешение, масштаб
3. **Преобразование координат**: Конвертирует координаты из футов Revit в пиксели
4. **Обрезка изображения**:
   - Для FilledRegion: создает полигональную маску с прозрачностью
   - Для DetailLine: обрезает по прямоугольной области
5. **Создание нового изображения**: Создает новый ImageType и ImageInstance
6. **Очистка**: Удаляет исходные элементы

1. **Element search**: Script finds ImageInstance and FilledRegion/DetailLine in selection
2. **Parameter extraction**: Gets image dimensions, resolution, scale
3. **Coordinate conversion**: Converts coordinates from Revit feet to pixels
4. **Image cropping**:
   - For FilledRegion: creates polygon mask with transparency
   - For DetailLine: crops by rectangular area
5. **New image creation**: Creates new ImageType and ImageInstance
6. **Cleanup**: Removes original elements

### Константы / Constants

```python
DEFAULT_DPI = 96.0              # Разрешение по умолчанию
MIN_POLYGON_POINTS = 3          # Минимальное количество точек для полигона
MIN_AREA_THRESHOLD = 1e-6       # Минимальная площадь для валидного полигона
MIN_DIMENSION = 1               # Минимальный размер изображения
```

## Структура файлов / File Structure

```
1. Crop image.pushbutton/
├── script.py          # Основной скрипт
├── bundle.yaml        # Конфигурация PyRevit
├── icon.png           # Иконка (светлая тема)
└── icon.dark.png      # Иконка (темная тема)
```

## Оптимизации / Optimizations

Скрипт был оптимизирован для:
- Правильного управления ресурсами (Dispose для Bitmap/Graphics)
- Улучшенной обработки исключений
- Использования констант вместо магических чисел
- Добавления документации (docstrings)
- Удаления неиспользуемых импортов

The script has been optimized for:
- Proper resource management (Dispose for Bitmap/Graphics)
- Improved exception handling
- Using constants instead of magic numbers
- Added documentation (docstrings)
- Removed unused imports

## Автор / Author

**Yanshin Elisey**

## Лицензия / License

Этот проект распространяется свободно. Используйте на свой страх и риск.

This project is provided as-is. Use at your own risk.

## Известные ограничения / Known Limitations

- Работает только в активном виде (не в 3D)
- Требует точного выделения элементов
- Обрезанные изображения сохраняются в ту же папку, что и исходные

- Works only in active view (not in 3D)
- Requires precise element selection
- Cropped images are saved to the same folder as originals

## Поддержка / Support

При возникновении проблем проверьте:
- Правильность выделения элементов
- Наличие изображения на диске или встроенного в проект
- Корректность установки PyRevit и rpw

If you encounter issues, check:
- Correct element selection
- Image file exists on disk or is embedded in project
- Correct installation of PyRevit and rpw

