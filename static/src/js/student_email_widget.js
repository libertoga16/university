/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, xml } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

/**
 * @description Widget for sending a silent email with the student's report.
 * @param {Object} props - Standard widget properties.
 * @returns {void}
 */
export class StudentEmailWidget extends Component {
    static template = xml`
        <button class="btn btn-link p-0 ms-2" t-on-click="onClickSend" t-att-disabled="isSending" title="Enviar reporte rápido">
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
                await this.props.record.save();
            }

            const recordId = this.props.record.resId;
            const email = this.props.record.data.email;

            if (!recordId || !email) {
                this.notification.add("Asegúrate de que el estudiante tiene un correo válido.", { type: "danger" });
                return;
            }

            const result = await this.orm.call(
                "university.student",
                "action_send_email_silent_js",
                [[recordId]]
            );

            if (result) {
                this.notification.add(
                    `Se ha enviado un correo con las notas a ${result}.`,
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
