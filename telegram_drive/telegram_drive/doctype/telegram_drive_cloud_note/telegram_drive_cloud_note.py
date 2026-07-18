import frappe
from frappe.model.document import Document


class TelegramDriveCloudNote(Document):
    def validate(self):
        if self.title and len(self.title) > 80:
            frappe.throw("Title cannot exceed 80 characters")
        if self.body and len(self.body) > 4000:
            frappe.throw("Body cannot exceed 4000 characters")
        if self.color and self.color not in {"yellow", "blue", "green", "pink", "violet"}:
            frappe.throw("Invalid note color")
