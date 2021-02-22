# -*- coding: utf-8 -*-
{
    'name': "Landed costs tags",

    'summary': """Lorem ipsum dolor sit amet, consectetur adipiscing elit.""",

    'author': "Odoolatam",
    'website': "https://odoolatam.odoo.com/",

    'category': 'Warehouse',
    'version': '1.0.0',

    'depends': [
        # 'account_invoicing',
        'stock_landed_costs',
        # 'whin_process_thiemed',  # REVIEW: check this module later
    ],

    'data': [
        # 'data/res_config_settings.yml',
        # 'data/res_users_data.xml',
        # 'data/stock_landed_cost_data.xml',
        'views/stock_landed_cost_views.xml',
    ],

    'demo': [
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
