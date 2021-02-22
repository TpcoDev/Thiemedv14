{
    "name": """Chile - E-Invoicing Delivery Guides""",
    'version': '1.0.2',
    'category': 'Localization/Chile',
    'sequence': 12,
    'author':  'Blanco Martín & Asociados',
    'description': """""",
    'website': 'http://blancomartin.cl',
    'depends': [
        'sale_stock',
        'l10n_cl_edi',
        ],
    'data': [
        'data/l10n_latam.document.type.csv',
        'template/dte_template.xml',
        'template/dd_template.xml',
        'template/ted_template.xml',
        'views/dte_caf_view.xml',
        'views/res_partner_view.xml',
        'views/stock_picking_views.xml',
        'views/report_delivery_guide.xml',
        'views/menuitems.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
