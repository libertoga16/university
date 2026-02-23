/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, xml } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { _t } from "@web/core/l10n/translation";

/**
 * @description Widget for sending a silent email with the student's report.
 * @param {Object} props - Standard widget properties.
 * @returns {void}
 */
export class StudentEmailWidget extends Component {
    static template = xml`
        <button class="btn btn-link p-0 ms-2" t-on-click="onClickSend" t-att-disabled="isSending" title="Send Report">
            <i class="fa fa-info-circle text-info fa-lg"/>
        </button>
    `;
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.ui = useService("ui"); // Requerido para congelar la pantalla
        this.isSending = false; // Estado de prevención
    }

    async onClickSend() {
        if (this.isSending) return; // Cortafuegos contra doble clic rápido

        this.isSending = true;
        this.ui.block(); // Bloquea la UI para mostrar que el sistema está trabajando

        try {
            if (this.props.record.isDirty) {
                const saved = await this.props.record.save();
                // Si la validación de Odoo detuvo el guardado, abortamos silenciosamente
                if (!saved) {
                    this.notification.add(_t("Please correct the form errors before sending the report."), { type: "danger" });
                    return;
                }
            }

            const recordId = this.props.record.resId;
            const email = this.props.record.data.email;

            if (!recordId || !email) {
                this.notification.add(_t("Ensure the student has a valid email address."), { type: "danger" });
                return;
            }

            // Uso de resModel dinámico. Ahora el widget funciona en cualquier modelo de Odoo.
            const result = await this.orm.call(
                this.props.record.resModel,
                "action_send_email_silent_js",
                [[recordId]]
            );

            if (result) {
                this.notification.add(
                    _t("An email with the grades has been sent to %s.").replace("%s", result),
                    { type: "success" }
                );
            }
        } catch (error) {
            console.error("Error enviando el correo:", error);
        } finally {
            // Se ejecuta SIEMPRE, incluso si el RPC falla, liberando al usuario
            this.isSending = false;
            this.ui.unblock();
        }
    }
}

// Registramos el componente como un 'widget' para poder usarlo en el XML
registry.category("view_widgets").add("student_send_email", {
    component: StudentEmailWidget,
});
