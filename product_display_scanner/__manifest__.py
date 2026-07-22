# -*- coding: utf-8 -*-
{
    'name': 'Product Display Scanner',
    'version': '17.0.2.0.0',
    'summary': 'A dedicated screen with an input box for scanning product barcodes.',
    'description': """
        Provides a custom screen with a large input box. Scan a product barcode,
        and the product's details (image, name, price) will be displayed instantly.
    """,
    'author': 'Navabrind IT Solutions',
    'website': 'https://navabrindsol.com',
    'category': 'Inventory',
    'depends': [ 
        'web',
        'product',
        'stock'
    ],
    'data': [
        'views/menu.xml',
        'views/product_views.xml',
    ], 
    'assets': {
        'web.assets_backend': [
            'product_display_scanner/static/src/css/carousel.css',
            'product_display_scanner/static/src/js/barcode_scanner_view.js',
            'product_display_scanner/static/src/xml/barcode_scanner_view.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
