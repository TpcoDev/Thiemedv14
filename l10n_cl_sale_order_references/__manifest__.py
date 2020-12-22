# -*- coding: utf-8 -*-
{
    "name": """Referencias en Notas de Ventas\
    """,
    'version': '0.0.2',
    'category': 'Localization/Chile',
    'sequence': 12,
    'author':  'Konos',
    'website': 'https://konos.cl',
    'license': 'AGPL-3',
    'summary': 'Referencias de Documentos en Notas de Ventas hacia DTE.',
    'description': """
Referencias de Documentos en Notas de Ventas hacia DTE
""",
    'depends': [
            'l10n_cl_fe',
            'sale',
            'l10n_cl_stock_picking'
        ],

    'data': [
            'views/layout.xml',
            'views/sale_order.xml',
            'security/ir.model.access.csv'

    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
