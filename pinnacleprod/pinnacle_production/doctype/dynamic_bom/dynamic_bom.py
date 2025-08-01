# Copyright (c) 2025, OTPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DynamicBOM(Document):
    def before_save(self):
        doc = frappe.get_doc(
            {
                "doctype": "BOM",
                "item": self.finished_good,
                "quantity": 1,
                "is_active": 1,
                "is_default": 0,
                "with_operations": 1,
                "routing": self.routing,
            }
        )

        # Append each item one by one
        if self.material_1:
            doc.append("items", {"item_code": self.material_1, "qty": 1})
        if self.material_2:
            doc.append("items", {"item_code": self.material_2, "qty": 1})
        if self.material_3:
            doc.append("items", {"item_code": self.material_3, "qty": 1})

        doc.insert(ignore_permissions=True)
        frappe.msgprint(
            msg=f'<a href="/app/bom/{doc.name}" target="_blank">BOM {doc.name} created</a>',
            indicator="green",
        )
