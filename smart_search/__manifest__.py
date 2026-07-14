{
    "name": "Smart Search",
    "version": "19.0.1.0.0",
    "summary": "Fetch product details from EZ-base using EAN",
    "category": "Inventory",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": [
        "product",
        "mail"
    ],
    "external_dependencies": {
        "python": ["selenium"],  # Optional: for JavaScript-rendered search
    },
    "data": [
        "security/ir.model.access.csv",

        "views/product_template_views.xml",
        "views/smart_search_result_views.xml",
        "views/smart_search_attribute_views.xml",
        'views/smart_search_config_views.xml',
        "views/smart_search_menu.xml",

        # "data/smart_search_data.xml",
    ],
    "installable": True,
    "application": True,
}
