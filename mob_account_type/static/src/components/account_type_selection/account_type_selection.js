/* @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { AccountTypeSelection as OriginalAccountTypeSelection } from "account.AccountTypeSelection";

export class CustomAccountTypeSelection extends OriginalAccountTypeSelection {
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
CustomAccountTypeSelection.template = "account.CustomAccountTypeSelection";

export const customAccountTypeSelection = {
    ...OriginalAccountTypeSelection,
    component: CustomAccountTypeSelection,
};

registry.category("fields").add("account_type_selection", customAccountTypeSelection);