from django.urls import resolve

def breadcrumb_context(request):
    """Generate breadcrumbs dynamically based on the URL path"""
    path = request.path.strip("/").split("/")
    breadcrumbs = []
    url = ""

    # Skip empty paths (e.g., when on the homepage)
    if not path or path == [""]:
        return {"breadcrumbs": []}

    for part in path:
        url += f"/{part}"
        breadcrumbs.append({
            "name": part.replace("-", " ").capitalize(),  # Convert URL part to readable name
            "url": url
        })

    return {"breadcrumbs": breadcrumbs}
