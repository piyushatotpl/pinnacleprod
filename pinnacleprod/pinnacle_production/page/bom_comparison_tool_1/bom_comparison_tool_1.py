import frappe
from frappe import _
from frappe.utils import flt, get_datetime, add_to_date


@frappe.whitelist()
def get_selected_bom_comparison(item_code, qty, planned_start_time, boms):

    boms = frappe.parse_json(boms)

    result = []

    for bom_name in boms:

        bom_doc = frappe.get_doc("BOM", bom_name)

        entry = {
            "bom_name": bom_doc.name,
            "material_cost": 0,
            "operating_cost": 0,
            "operation": bom_doc.operations[0].operation if bom_doc.operations else "",
            "total_cost": 0,
            "scrap_cost": 0,
            "scrap_percentage": 0,
            "workstation_name": "",
            "availability": "N/A",
        }

        qty = flt(qty)
        material_cost = sum([(flt(i.qty) * (i.rate or 0)) for i in bom_doc.items])
        entry["material_cost"] = material_cost * qty

        operating_cost = 0
        total_time = 0
        for op in bom_doc.operations:
            rate = frappe.db.get_value("Workstation", op.workstation, "hour_rate") or 0
            time = flt(op.time_in_mins) / 60
            operating_cost += time * rate
            total_time += flt(op.time_in_mins)
            entry["workstation_name"] = op.workstation
        entry["operating_cost"] = operating_cost * qty
        entry["total_cost"] = entry["material_cost"] + entry["operating_cost"]

        entry["scrap_cost"] = sum([flt(s.amount) for s in bom_doc.scrap_items])
        if entry["total_cost"]:
            entry["scrap_percentage"] = round(
                (entry["scrap_cost"] / entry["total_cost"]) * 100, 2
            )

        # Check workstation conflict
        if entry["bom_name"]:
            
            conflict = frappe.get_list(
                "Job Card",
                filters=[
                    ["bom_no", "=", entry["bom_name"]],
                    ["operation", "=", entry["operation"]],
                    ["actual_start_date", "<=", planned_start_time],
                    ["actual_end_date", ">=", planned_start_time],
                    ["status", "=", "Work In Progress"],
                ],
                fields=["name"],
                limit=1,
            )
            
            # frappe.throw(str(conflict))
            entry["availability"] = "❌ Busy" if conflict else "✅ Available"

        result.append(entry)

    return result
