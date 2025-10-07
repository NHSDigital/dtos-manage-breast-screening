def extract_next_path_from_params(request):
    """Extract and validate a 'next' URL from request GET or POST parameters.

    Only returns the URL if it's a safe relative URL (starts with '/').
    Returns None if no valid next URL is found.
    """
    next_candidate = request.POST.get("next") or request.GET.get("next")

    if not next_candidate:
        return None

    if next_candidate.startswith("/"):
        return next_candidate

    return None
