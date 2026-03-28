import frappe
from erpnext.projects.doctype.task.task import Task

class ConstructTask(Task):
    def validate(self):
        super().validate()
