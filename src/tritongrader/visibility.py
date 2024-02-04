from enum import Enum

class GradescopeVisibility(Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"
    AFTER_DUE_DATE = "after_due_date"
    AFTER_PUBLISHED = "after_published"