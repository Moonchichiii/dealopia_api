from wagtail import hooks
import cloudinary


@hooks.register('before_edit_page')
def set_default_transformation_options(request, page):
    """
    Set default transformation options for any images being added to pages.
    
    Args:
        request: The HTTP request object
        page: The page being edited
    """
    # Access any image chooser fields and add default transformation options
    pass


@hooks.register('after_create_image')
def optimize_new_image(image):
    """
    Apply optimizations to newly uploaded images.
    
    Sets default transformation options for images that don't have them already.
    
    Args:
        image: The newly created image object
    """
    if hasattr(image, 'transformation_options') and not image.transformation_options:
        # Set default transformations for all new images
        image.transformation_options = {
            'quality': 'auto',
            'fetch_format': 'auto',
            'responsive': True,
            'width': 'auto',
            'dpr': 'auto',
            'crop': 'limit',
        }
        image.save()