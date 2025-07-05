frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		// frm.add_custom_button("Calculate Raw Material", () => {
		// 	// Get list of items in Sales Order
		// 	let items = (frm.doc.items || []).map((d) => ({
		// 		label: d.item_name,
		// 		value: d.item_code,
		// 	}));
		// 	if (!items.length) {
		// 		frappe.msgprint(__("No items found in Sales Order"));
		// 		return;
		// 	}
		// 	let selected_item_qty = 0;
		// 	const dialog = new frappe.ui.Dialog({
		// 		title: "Calculate Raw Material",
		// 		fields: [
		// 			{
		// 				label: "Select Item",
		// 				fieldname: "selected_item",
		// 				fieldtype: "Select",
		// 				options: items,
		// 				reqd: 1,
		// 				onchange: function () {
		// 					let selected = dialog.get_value("selected_item");
		// 					let item_row = frm.doc.items.find((row) => row.item_code === selected);
		// 					if (item_row) {
		// 						selected_item_qty = item_row.qty;
		// 						dialog.set_value("qty", selected_item_qty);
		// 					} else {
		// 						dialog.set_value("qty", 0);
		// 					}
		// 				},
		// 			},
		// 			{
		// 				label: "Qty",
		// 				fieldname: "qty",
		// 				fieldtype: "Float",
		// 				read_only: 1,
		// 			},
		// 			{
		// 				label: "BOM",
		// 				fieldname: "bom",
		// 				fieldtype: "Link",
		// 				options: "BOM",
		// 				reqd: 1,
		// 				get_query: () => {
		// 					return {
		// 						filters: {
		// 							item: dialog.get_value("selected_item"),
		// 						},
		// 					};
		// 				},
		// 				onchange: function () {
		// 					let bom = dialog.get_value("bom");
		// 					let qty = dialog.get_value("qty");
		// 					if (bom && qty) {
		// 						frappe.call({
		// 							method: "frappe.client.get",
		// 							args: {
		// 								doctype: "BOM",
		// 								name: bom,
		// 							},
		// 							callback: function (r) {
		// 								if (r.message) {
		// 									let bomDoc = r.message;
		// 									bomQty = bomDoc.quantity || 1; // Default to 1 if not set
		// 									let html = `<h5>Raw Materials Required for ${qty} Qty</h5>
		// 										<table class="table table-bordered">
		// 											<thead><tr>
		// 												<th>Item Code</th>
		// 												<th>Item Name</th>
		// 												<th>Qty</th>
		// 												<th>UOM</th>
		// 											</tr></thead>
		// 											<tbody>`;
		// 									(bomDoc.items || []).forEach((item) => {
		// 										html += `<tr>
		// 											<td>${item.item_code}</td>
		// 											<td>${item.item_name}</td>
		// 											<td>${flt((item.qty / bomQty) * qty, 3)}</td>
		// 											<td>${item.uom}</td>
		// 										</tr>`;
		// 									});
		// 									html += "</tbody></table>";
		// 									dialog.set_value("raw_material_html", html);
		// 								}
		// 							},
		// 						});
		// 					}
		// 				},
		// 			},
		// 			{
		// 				fieldtype: "HTML",
		// 				fieldname: "raw_material_html",
		// 				options: "",
		// 				label: "Raw Materials",
		// 			},
		// 		],
		// 		primary_action_label: "Close",
		// 		primary_action() {
		// 			dialog.hide();
		// 		},
		// 	});
		// 	dialog.show();
		// });
	},
});

frappe.ui.form.on("Sales Order Item", {
	qty: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		let length = flt(row.custom_length);
		let width = flt(row.custom_width);
		let thickness = flt(row.custom_thickness);

		if (length && width && thickness) {
			let weight = ((length * width * thickness) / 100000) * 0.95; // mm³ to m³
			weight = flt(weight, 3); // round to 3 decimal places

			frappe.model.set_value(cdt, cdn, "custom_weight", weight * row.qty); // Set weight based on quantity
		} else {
			console.log("Dimensions not fully set; weight not calculated.");
			frappe.model.set_value(cdt, cdn, "custom_weight", 0);
		}
	},
});
