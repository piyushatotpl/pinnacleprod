frappe.ui.form.on("Product Manufacturing Costing", {
	refresh: function (frm) {
		frm.disable_save();
		// frm.add_custom_button("Calculate Cost", () => {
		// 	frappe.call({
		// 		method: "pinnacleprod.pinnacle_production.doctype.product_manufacturing_costing.product_manufacturing_costing.calculate_manufacturing_cost",
		// 		args: {
		// 			bom: frm.doc.bom,
		// 			workstation: frm.doc.workstation,
		// 			quantity: frm.doc.quantity || 1,
		// 			scrap: frm.doc.scrap || 0,
		// 		},
		// 		callback: (r) => {
		// 			if (r.message) {
		// 				frm.set_value("total_material_cost", r.message.material_cost);
		// 				frm.set_value("labour_cost", r.message.labour_cost);
		// 				frm.set_value("overhead_cost", r.message.overhead_cost);
		// 				frm.set_value("total_cost", r.message.total_cost);
		// 				frm.set_value("cost_per_unit", r.message.cost_per_unit);
		// 			}
		// 		},
		// 	});
		// });
	},
	sales_order: function (frm) {
		let item_options = [];

		if (frm.doc.sales_order) {
			frappe.db.get_doc("Sales Order", frm.doc.sales_order).then((doc) => {
				doc.items.forEach((item) => {
					item_options.push(item.item_code);
				});

				frm.set_df_property("select_item", "options", item_options);
				frm.refresh_field("select_item");
			});
		}
	},
	select_item: function (frm) {
		if (frm.doc.select_item) {
			frm.set_query("bom", function () {
				return {
					filters: {
						item: frm.doc.select_item,
					},
				};
			});
		}
	},
	bom: function (frm) {
		let material_cost = 0;
		let operation_cost = 0;
		let scrap_cost = 0;

		if (frm.doc.bom) {
			frappe.db.get_doc("BOM", frm.doc.bom).then((doc) => {
				// Calculate material cost
				doc.items.forEach((item) => {
					material_cost += item.amount || 0;
				});

				// Calculate operation cost
				doc.operations.forEach((operation) => {
					operation_cost += operation.operating_cost || 0;
				});

				// Calculate scrap cost
				doc.scrap_items.forEach((scrap) => {
					scrap_cost += scrap.amount || 0;
				});

				// Total cost
				let total_cost = material_cost + operation_cost;

				// Set total in field
				frm.set_value("product_manufacturing_costing", total_cost);
				frm.refresh_field("product_manufacturing_costing");

				frm.set_value("scrap_cost", scrap_cost);
				frm.refresh_field("scrap_cost");

				// Log all costs
				console.log("Material Cost: ", material_cost);
				console.log("Operation Cost: ", operation_cost);
				console.log("Scrap Cost: ", scrap_cost);
				console.log("Total Manufacturing Cost: ", total_cost);
			});
		}
	},
});
