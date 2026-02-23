/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, xml } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { _t } from "@web/core/l10n/translation"; // Obligatorio para Odoo
import { sprintf } from "@web/core/utils/strings";

export class StudentEmailWidget extends Component {
    static template = xml`
        <button class="btn btn-link p-0 ms-2" t-on-click="onClickSend" t-att-title="titleText">
            <i class="fa fa-info-circle text-info fa-lg"/>
        </button>
    `;
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    get titleText() {
        return _t("Send quick report");
    }

    async onClickSend() {
        if (this.props.record.isDirty) {
            await this.props.record.save();
        }

        const recordId = this.props.record.resId;
        const email = this.props.record.data.email;

        if (!recordId || !email) {
            this.notification.add(_t("Ensure the student has a valid email address."), { type: "danger" });
            return;
        }

        try {
            // Dinámico. Nunca más hardcodees un modelo en un widget reutilizable.
            const result = await this.orm.call(
                this.props.record.resModel,
                "action_send_email_silent_js",
                [[recordId]]
            );

            if (result) {
                this.notification.add(
                    sprintf(_t("An email with the grades has been sent to %s."), result),
                    { type: "success" }
                );
            }
        } catch (error) {
            console.error(_t("Error sending email:"), error);
        }
    }
}

registry.category("view_widgets").add("student_send_email", {
    component: StudentEmailWidget,
});
