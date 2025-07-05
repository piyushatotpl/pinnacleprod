# Copyright (c) 2025, OTPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProductManufacturingCosting(Document):
    pass


import frappe


@frappe.whitelist()
def calculate_manufacturing_cost(bom, workstation, quantity=1, scrap=0):

    try:
        # ✅ Convert to float to avoid TypeError
        quantity = float(quantity)
        scrap = float(scrap)
    except (ValueError, TypeError):
        frappe.throw("Quantity and Scrap must be valid numbers.")

    bom_doc = frappe.get_doc("BOM", bom)
    
    material_cost = 0
    for item in bom_doc.items:
        scrap_factor = 1 + (scrap / 100)
        total_qty = item.qty * scrap_factor
        material_cost += total_qty * item.rate
    rate_per_hour = frappe.db.get_value("Workstation", workstation, "hour_rate")
    labour_cost = 0
    for op in bom_doc.operations:
        labour_cost += (op.time_in_mins / 60) * rate_per_hour

    overhead_cost = 0  # Optional: Add your own logic
    frappe.throw(str(material_cost))
    total_cost = material_cost + labour_cost + overhead_cost
    cost_per_unit = total_cost / quantity

    return {
        "material_cost": round(material_cost, 2),
        "labour_cost": round(labour_cost, 2),
        "overhead_cost": round(overhead_cost, 2),
        "total_cost": round(total_cost, 2),
        "cost_per_unit": round(cost_per_unit, 2),
    }
