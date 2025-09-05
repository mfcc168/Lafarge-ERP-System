from django.urls import resolve

def breadcrumb_context(request):
    """
    Generate breadcrumb navigation dynamically from URL path.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        dict: Context containing breadcrumb data
    """
    path = request.path.strip("/").split("/")
    breadcrumbs = []
    url = ""

    # Return empty breadcrumbs for homepage
    if not path or path == [""]:
        return {"breadcrumbs": []}

    for part in path:
        url += f"/{part}"
        breadcrumbs.append({
            "name": part.replace("-", " ").capitalize(),
            "url": url
        })

    return {"breadcrumbs": breadcrumbs}
