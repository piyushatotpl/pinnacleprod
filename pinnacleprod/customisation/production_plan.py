import frappe
from frappe import _
from frappe.utils import now_datetime, flt
from pypika.terms import ExistsCriterion
from erpnext.manufacturing.doctype.production_plan.production_plan import (
    ProductionPlan,
    get_item_details,
)


class CustomProductionPlan(ProductionPlan):

    @frappe.whitelist()
    def get_so_items(self):
        # Check for empty table or empty rows
        if not self.get("sales_orders") or not self.get_so_mr_list("sales_order", "sales_orders"):
            frappe.throw(_("Please fill the Sales Orders table"), title=_("Sales Orders Required"))

        so_list = self.get_so_mr_list("sales_order", "sales_orders")

        bom = frappe.qb.DocType("BOM")
        so_item = frappe.qb.DocType("Sales Order Item")

        items_subquery = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)

        items_query = (
            frappe.qb.from_(so_item)
            .select(
                so_item.parent,
                so_item.item_code,
                so_item.warehouse,
                so_item.qty,
                so_item.work_order_qty,
                so_item.delivered_qty,
                so_item.custom_weight,
                so_item.conversion_factor,
                so_item.description,
                so_item.name,
                so_item.bom_no,
            )
            .distinct()
            .where(
                (so_item.parent.isin(so_list)) &
                (so_item.docstatus == 1) &
                (so_item.qty > so_item.work_order_qty)
            )
        )

        if self.item_code and frappe.db.exists("Item", self.item_code):
            items_query = items_query.where(so_item.item_code == self.item_code)
            items_subquery = items_subquery.where(bom.item == so_item.item_code)

        items_query = items_query.where(ExistsCriterion(items_subquery))
        items = items_query.run(as_dict=True)

        for item in items:
            item.pending_qty = (
                flt(item.qty) - max(flt(item.work_order_qty or 0), flt(item.delivered_qty or 0))
            ) * flt(item.conversion_factor or 1)

        pi = frappe.qb.DocType("Packed Item")

        packed_items_query = (
            frappe.qb.from_(so_item)
            .from_(pi)
            .select(
                pi.parent,
                pi.item_code,
                pi.warehouse.as_("warehouse"),
                (((so_item.qty - so_item.work_order_qty) * pi.qty) / so_item.qty).as_("pending_qty"),
                pi.parent_item,
                pi.description,
                so_item.name,
            )
            .distinct()
            .where(
                (so_item.parent == pi.parent) &
                (so_item.docstatus == 1) &
                (pi.parent_item == so_item.item_code) &
                (so_item.parent.isin(so_list)) &
                (so_item.qty > so_item.work_order_qty) &
                ExistsCriterion(
                    frappe.qb.from_(bom)
                    .select(bom.name)
                    .where((bom.item == pi.item_code) & (bom.is_active == 1))
                )
            )
        )

        if self.item_code:
            packed_items_query = packed_items_query.where(so_item.item_code == self.item_code)

        packed_items = packed_items_query.run(as_dict=True)

        self.add_items(items + packed_items)
        self.calculate_total_planned_qty()

    @frappe.whitelist()
    def add_items(self, items):
        refs = {}

        for data in items:
            if not data.pending_qty:
                continue

            item_details = get_item_details(data.item_code, throw=False)

            # Handle combine logic
            if self.combine_items:
                bom_no = data.get("bom_no") or (item_details.bom_no if item_details else None)

                if not bom_no:
                    continue

                if bom_no in refs:
                    refs[bom_no]["so_details"].append({
                        "sales_order": data.parent,
                        "sales_order_item": data.name,
                        "qty": data.pending_qty,
                    })
                    refs[bom_no]["qty"] += data.pending_qty
                    continue
                else:
                    refs[bom_no] = {
                        "qty": data.pending_qty,
                        "po_item_ref": data.name,
                        "so_details": [{
                            "sales_order": data.parent,
                            "sales_order_item": data.name,
                            "qty": data.pending_qty,
                        }],
                    }

            # Normal append
            bom_no = data.get("bom_no") or (item_details.get("bom_no") if item_details else "")
            if not bom_no:
                frappe.logger().warning(f"No BOM found for item {data.item_code}, skipping.")
                continue

            pi = self.append("po_items", {
                "warehouse": data.warehouse,
                "item_code": data.item_code,
                "description": data.description or (item_details.description if item_details else ""),
                "stock_uom": "Kg",  # You may want to make this dynamic
                "bom_no": bom_no,
                "planned_qty": data.custom_weight,
                "pending_qty": data.custom_weight,
                "planned_start_date": now_datetime(),
                "product_bundle_item": data.get("parent_item"),
            })
            pi._set_defaults()

            if self.get_items_from == "Sales Order":
                pi.sales_order = data.parent
                pi.sales_order_item = data.name
            elif self.get_items_from == "Material Request":
                pi.material_request = data.parent
                pi.material_request_item = data.name

        if refs:
            for po_item in self.po_items:
                if po_item.bom_no in refs:
                    po_item.planned_qty = refs[po_item.bom_no]["qty"]
                    po_item.pending_qty = refs[po_item.bom_no]["qty"]
                    po_item.sales_order = ""

            self.add_pp_ref(refs)

        # Optional: comment this if you're already handling item addition above
        super().add_items(items)
