# -*- coding: utf-8 -*-
from odoo import http

# class NgTaxOilStream(http.Controller):
#     @http.route('/ng_tax_oil_stream/ng_tax_oil_stream/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ng_tax_oil_stream/ng_tax_oil_stream/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ng_tax_oil_stream.listing', {
#             'root': '/ng_tax_oil_stream/ng_tax_oil_stream',
#             'objects': http.request.env['ng_tax_oil_stream.ng_tax_oil_stream'].search([]),
#         })

#     @http.route('/ng_tax_oil_stream/ng_tax_oil_stream/objects/<model("ng_tax_oil_stream.ng_tax_oil_stream"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ng_tax_oil_stream.object', {
#             'object': obj
#         })