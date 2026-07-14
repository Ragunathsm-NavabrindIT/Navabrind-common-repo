/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { Product360Viewer } from "./product_360_viewer";
import { useService } from "@web/core/utils/hooks";

// 1. Define the Dialog Component (The Popup)
class Product360Dialog extends Component {
    static components = { Product360Viewer };
    static template = xml`
        <div class="o_product_360_dialog_content" style="text-align:center;">
             <Product360Viewer imageIds="props.imageIds"/>
             <p class="text-muted mt-2">Drag image to rotate</p>
        </div>
    `;
    static props = ["imageIds", "close"];
}

// 2. Define the Field Widget (The Button on the Card)
export class Product360KanbanButton extends Component {
    static template = xml`
        <t t-if="hasImages">
            <div class="o_product_360_btn_kanban" 
                 t-on-click.stop.prevent="open360View">
                <i class="fa fa-refresh"/> 360
            </div>
        </t>
    `;

    static props = { ...standardFieldProps };

    setup() {
        this.dialog = useService("dialog");
    }

    get imageIds() {
        // Retrieve JSON data from the field value
        return this.props.record.data[this.props.name] || [];
    }

    get hasImages() {
        return this.imageIds && this.imageIds.length > 0;
    }

    open360View() {
        // Open the dialog with the images
        this.dialog.add(Product360Dialog, {
            title: "360° Product View: " + this.props.record.data.name,
            imageIds: this.imageIds,
        });
    }
}

// 3. Register the widget so we can use it in XML
export const product360KanbanButton = {
    component: Product360KanbanButton,
    supportedTypes: ["json"],
};

registry.category("fields").add("product_360_kanban_button", product360KanbanButton);