from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('qa_qc_approve', 'QA/QC Approved'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")

    def _valid_field_parameter(self, field, name):
        # EXTENDS models
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    @api.depends('product_uom_qty', 'price_cost')
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_cost

    def _default_cost(self):
        return self.product_id.standard_price

    price_cost = fields.Float(
        string="Cost", related='product_id.standard_price')
    price_subtotal = fields.Float(
        string="Price Subtotal", compute="_compute_subtotal", readonly=True)

    store_request_size = fields.Char('Size', copy=False)
    brand_id = fields.Many2one('brand.type', 'Make/Brand', copy=False)
    certificate_required = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Certificate Required', readonly=False, index=True, copy=False, tracking=True,)
    reserved_uom_qty = fields.Float('reserved_uom_qty', default=1)

    def _get_relevant_state_among_moves(self):
        # We sort our moves by importance of state:
        #     ------------- 0
        #     | Assigned  |
        #     -------------
        #     |  Waiting  |
        #     -------------
        #     |  Partial  |
        #     -------------
        #     |  Confirm  |
        #     ------------- len-1
        sort_map = {
            'assigned': 4,
            'waiting': 3,
            'partially_available': 2,
            'confirmed': 1,
        }
        moves_todo = self\
            .filtered(lambda move: move.state not in ['cancel', 'done'])\
            .sorted(key=lambda move: (sort_map.get(move.state, 0)))
        # The picking should be the same for all moves.
        if moves_todo[0].picking_id.move_type == 'one':
            most_important_move = moves_todo[0]
            if most_important_move.state == 'confirmed':
                return 'confirmed' if most_important_move.product_uom_qty else 'assigned'
            elif most_important_move.state == 'partially_available':
                return 'confirmed'
            else:
                return moves_todo[0].state or 'draft'
        elif moves_todo[0].state != 'assigned' and any(move.state in ['assigned', 'partially_available'] for move in moves_todo):
            return 'partially_available'
        else:
            least_important_move = moves_todo[-1]
            if least_important_move.state == 'confirmed' and least_important_move.product_uom_qty == 0:
                return 'assigned'
            else:
                return moves_todo[-1].state or 'draft'
            
class StockMoveLine(models.Model):
    _name = 'stock.move.line'
    _inherit = ['mail.thread', 'stock.move.line', 'mail.activity.mixin']

