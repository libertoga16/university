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
    // Definimos el pequeño icono azul de información directo en la plantilla
    static template = xml`
        <button class="btn btn-link p-0 ms-2" t-on-click="onClickSend" title="Enviar reporte rápido">
            <i class="fa fa-info-circle text-info fa-lg"/>
        </button>
    `;
    static props = { ...standardWidgetProps };

    setup() {
        // Enganchamos los servicios base de Odoo (Base de datos y Notificaciones)
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    /**
     * @description Dispara la llamada RPC para enviar el email silencioso y notifica el resultado.
     * @returns {void}
     */
    async onClickSend() {
        const recordId = this.props.record.resId;
        const email = this.props.record.data.email;

        // Si es un registro nuevo sin guardar o no tiene correo, no disparamos
        if (!recordId || !email) {
            this.notification.add("Por favor, guarda el registro y asegúrate de que tiene un correo.", { type: "danger" });
            return;
        }

        try {
            // Llamada RPC al método de Python
            const result = await this.orm.call(
                "university.student",
                "action_send_email_silent_js",
                [[recordId]]
            );

            // Si Python nos devuelve un texto (el email), disparamos el verde
            if (result) {
                this.notification.add(
                    `Se ha enviado un correo con las notas a ${result}.`,
                    { type: "success" }
                );
            }
        } catch (error) {
            // Si Python explota, el ORM de Odoo mostrará la alerta roja nativa automáticamente
            console.error("Error enviando el correo:", error);
        }
    }
}

// Registramos el componente como un 'widget' para poder usarlo en el XML
registry.category("view_widgets").add("student_send_email", {
    component: StudentEmailWidget,
});
