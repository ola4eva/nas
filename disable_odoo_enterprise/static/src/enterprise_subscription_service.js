/** @odoo-module */

import { SubscriptionManager } from "@web_enterprise/webclient/home_menu/enterprise_subscription_service";
import { patch } from "@web/core/utils/patch";

patch(SubscriptionManager.prototype, {
  get daysLeft() {
    return 1000;
  },
});
