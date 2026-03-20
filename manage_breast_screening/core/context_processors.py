def nav_active(request):
    if request.path.startswith(("/clinics/", "/mammograms/", "/participants/")):
        active = "clinics"
    else:
        active = "home"
    return {"navActive": active}
