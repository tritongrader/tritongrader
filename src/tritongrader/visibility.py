from enum import Enum, auto

class Visibility(Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"

class GradescopeVisibility(Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"
    AFTER_DUE_DATE = "after_due_date"
    AFTER_PUBLISHED = "after_published"