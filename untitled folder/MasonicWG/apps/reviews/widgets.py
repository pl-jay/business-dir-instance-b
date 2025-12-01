from django.forms.widgets import ClearableFileInput

class MultiFileInput(ClearableFileInput):
    # Tell Django this widget supports selecting multiple files
    allow_multiple_selected = True
