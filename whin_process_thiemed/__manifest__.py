# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


{
    'name': 'WH/IN Process Thiemed',
    'version': '14.0.0.1',
    'category': 'Accounting',
    'summary': 'Make the WH/IN Process for Thiemed',
    'description': """
    Make the WH/IN Process for Thiemed
""",
    'author': 'Odoo Latam',
    'website': 'http://www.odoolatam.com',
    'depends': ['purchase','product','stock','stock_landed_costs','analytic','account','parse_gs1_128'],
    'data': [
        'views/picking_view.xml', 
        'views/account_invoice_view.xml'
        ],
    'demo': [],
    'js': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    #"images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
