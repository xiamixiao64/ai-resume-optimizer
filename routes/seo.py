"""SEO routes - Sitemap, Robots.txt"""
import os
from flask import Blueprint, Response

seo_bp = Blueprint('seo', __name__)


@seo_bp.route('/sitemap.xml')
def sitemap():
    base_url = os.environ.get('BASE_URL', 'https://resumeforge.ai')
    pages = [
        ('', '1.0', 'daily'),
        ('/jobs', '0.8', 'weekly'),
        ('/linkedin', '0.8', 'weekly'),
        ('/templates', '0.8', 'weekly'),
        ('/login', '0.3', 'monthly'),
        ('/register', '0.3', 'monthly'),
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path, priority, changefreq in pages:
        xml += f'  <url>\n    <loc>{base_url}{path}</loc>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')


@seo_bp.route('/robots.txt')
def robots():
    base_url = os.environ.get('BASE_URL', 'https://resumeforge.ai')
    content = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin
Disallow: /history

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content, mimetype='text/plain')
