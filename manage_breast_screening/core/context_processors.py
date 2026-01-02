def nav_active(request):
    if request.path.startswith("/clinics/"):
        active = "clinics"
    else:
        active = "home"
    return {"navActive": active}
