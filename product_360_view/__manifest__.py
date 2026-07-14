{
    'name': 'Product 360 App',  # Changed name
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Standalone App to manage Product 360 Views',
    'description': """
        Standalone Application for 360 Product Visualization.
        - Own Menu Item.
        - Separate Form View.
        - Does not clutter Inventory/Sales.
    """,
    'author': 'YourName',
    'depends': ['product', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_360_view/static/src/css/product_360.scss',
            'product_360_view/static/src/xml/*.xml',
            'product_360_view/static/src/js/product_360_viewer.js',
            'product_360_view/static/src/js/product_360_field.js',
            'product_360_view/static/src/js/product_kanban_patch.js',
        ],
    },
    'installable': True,
    'application': True, # <--- THIS MAKES IT AN APP ON THE DASHBOARD
    'license': 'LGPL-3',
}