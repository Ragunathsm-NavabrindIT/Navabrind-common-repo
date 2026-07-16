{
    'name': 'AI Enrichment',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Manage AI Providers and Models for Enrichment',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_enrichment_config.xml',
        'views/ai_enrichment_wizard.xml',
        'views/dashboard_enrichment_config.xml',
        'views/ai_enrichment_queue_log_views.xml',
        'views/menus.xml',
        'data/ir_cron_data.xml',
        'data/sequence.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "AI_Enrichment/static/src/js/wizard_loader.js",
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
