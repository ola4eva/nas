/* @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { SelectionField, selectionField } from "@web/views/fields/selection/selection_field";

export class CustomAccountTypeSelection extends SelectionField {
    get hierarchyOptions() {
        const opts = this.options;
        console.log("<<<<<<<<<<< My selection widget >>>>>>>>>>>");
        return [
            { name: _t('Balance Sheet') },
            { name: _t('Assets'), children: opts.filter(x => x[0] && x[0].startsWith('asset')) },
            { name: _t('Liabilities'), children: opts.filter(x => x[0] && x[0].startsWith('liability')) },
            { name: _t('Equity'), children: opts.filter(x => x[0] && x[0].startsWith('equity')) },
            { name: _t('Profit & Loss') },
            { name: _t('Income'), children: opts.filter(x => x[0] && x[0].startsWith('income')) },
            { name: _t('Expense'), children: opts.filter(x => x[0] && x[0].startsWith('expense')) },
            { name: _t('Other'), children: opts.filter(x => x[0] && x[0].startsWith('off_balance')) }, // Changed line
        ];
    }
}
CustomAccountTypeSelection.template = "mob_account_type.CustomAccountTypeSelection";

export const customAccountTypeSelection = {
    ...selectionField,
    component: CustomAccountTypeSelection,
};

registry.category("fields").add("custom_account_type_selection", customAccountTypeSelection);