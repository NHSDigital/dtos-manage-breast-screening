from django.tasks import task


@task(backend="database")
def create_modality_worklist_item():
    pass
