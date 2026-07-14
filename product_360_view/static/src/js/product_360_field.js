/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
// FIX: Added 'xml' to the import list below
import { Component, xml } from "@odoo/owl";
import { Product360Viewer } from "./product_360_viewer";

export class Product360Field extends Component {
    // We use the 'xml' helper to define the template inline
    static template = xml`
        <div class="o_field_product_360" style="width:100%; max-width:400px; margin: 0 auto; border: 1px solid #ccc;">
            <t t-if="imageIds.length > 0">
                <Product360Viewer imageIds="imageIds"/>
            </t>
            <t t-else="">
                <div class="text-muted p-3 text-center">No 360 Images Uploaded</div>
            </t>
        </div>
    `;
    
    static components = { Product360Viewer };
    static props = { ...standardFieldProps };

    get imageIds() {
        // value passed from python is JSON/Array
        // We safely check if record.data exists
        return this.props.record.data[this.props.name] || [];
    }
}

export const product360Field = {
    component: Product360Field,
    supportedTypes: ["json"],
};

registry.category("fields").add("product_360_viewer_widget", product360Field);